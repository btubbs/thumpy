#!/usr/bin/env python

"""
Thumpy web process to resize images.
"""

import argparse
import os
import urlparse
import yaml
from cStringIO import StringIO

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from PIL import ImageOps, Image as PILImage
from boto import connect_s3


# Default configuration here.  Override by specifying a settings.yaml file with
# your own values.
config = {
    'host': 'localhost',
    'port': 8000,
    'ignore_favicon': True,
    'cloudfront_ugliness': False,
    'storage': 'LocalStorage',
}


class MissingImage(Exception):
    pass


class S3Storage(object):
    def __init__(self, s3_key, s3_secret, s3_bucket, **kwargs):
        self.conn = connect_s3(s3_key, s3_secret)
        self.bucket = self.conn.get_bucket(s3_bucket)

    def get_image(self, path):
        # Make a boto connection, pull down the file, and return the file
        # object.  If not found, return None

        key = self.bucket.get_key(path)
        if path is None:
            raise MissingImage, "No key for %s" % path

        # For returning PIL "Image" from a url see
        # http://blog.hardlycode.com/pil-image-from-url-2011-01/.  That will
        # need to be adapted a little bit to work from S3, but should be fine.

        if not key or not key.exists():
            raise MissingImage("No file for %s" % path)

        im = Image(path)
        # actually stick the data in there
        im.storage = self
        im.im = PILImage.open(StringIO(key.read()))
        return im


class LocalStorage(object):
    def __init__(self, root=None, **kwargs):
        self.root = os.path.realpath(root or os.path.dirname(__file__))

    def get_image(self, path):
        f = os.path.realpath(os.path.join(self.root, path))

        # raise an exception if someone tries to break out of jail with paths
        # like "../../../blah"
        assert f.startswith(self.root)

        # TODO: ensure that the file is actually an image.
        im = Image(path)
        try:
            im.im = PILImage.open(f)
        except IOError:
            raise MissingImage, "No file for %s" % path
        im.storage = self
        return im


class Image(object):
    def __init__(self, path):
        self.path = path

        # TODO: isn't there a python mimetypes library that can do this file
        # format guessing a little more intelligently?
        self.fmt = path.split('.')[-1].lower()
        if self.fmt.lower() == 'jpg':
            self.fmt = 'jpeg'

    def scale(self, w, h):
        if w > self.im.size[0]:
            w = self.im.size[0]

        if h > self.im.size[1]:
            h = self.im.size[1]

        self.im = self.im.resize((w, h), PILImage.ANTIALIAS)

    def scale_to_width(self, w):
        r =  float(w) / self.im.size[0]
        h = int(self.im.size[1] * r)
        self.scale(w, h)

    def scale_to_height(self, h):
        r =  float(h) / self.im.size[1]
        w = int(self.im.size[0] * r)
        self.scale(w, h)

    def crop(self, w=None, h=None):
        w = w or self.im.size[0]
        h = h or self.im.size[1]

        if w > self.im.size[0]:
            w = self.im.size[0]

        if h > self.im.size[1]:
            h = self.im.size[1]

        left = (self.im.size[0] / 2) - (w / 2)
        top = (self.im.size[1] / 2) - (h / 2)
        right = left + w
        bottom = top + h

        self.im = self.im.crop((left, top, right, bottom))

    def process(self, options):

        # First do all the scaling operations
        if 'w' in options and 'h' in options:
            # scale both width and height
            self.scale(int(options['w']), int(options['h']))
        elif 'w' in options:
            # scale width to w, and height proportionally
            self.scale_to_width(int(options['w']))
        elif 'h' in options:
            # scale height to h, and width proportionally
            self.scale_to_height(int(options['h']))

        # Now do any cropping.  This order is important.
        if 'cw' in options and 'ch' in options:
            self.crop(w=int(options['cw']), h=int(options['ch']))
        elif 'cw' in options:
            self.crop(w=int(options['cw']))
        elif 'ch' in options:
            self.crop(h=int(options['ch']))



        # Other filters
        if 'gray' in options:
            self.im = ImageOps.grayscale(self.im)

    @property
    def contents(self):
        # Write the file contents out to a specific format, but just in memory.
        # Return them as a string.
        f = StringIO()
        self.im.save(f, self.fmt)
        f.seek(0)
        # TODO: probably better to just return the file object rather than copy
        # it out into a string, which doubles the memory usage.
        return f.read()

    @property
    def mimetype(self, fmt=None):
        fmt = fmt or self.fmt
        return "image/" + fmt


def oparse_qs(qs, keep_blank_values=0, strict_parsing=0):
    """Kind of like urlparse.parse_qs, except returns an ordered dict, and
    doesn't allow for multiple values per key (it just takes the first), so you
    don't have to do any list unpacking.  """
    # Also avoids replicating that function's bad habit of overriding the
    # built-in 'dict' type.
    od = OrderedDict()
    for name, value in urlparse.parse_qsl(qs, keep_blank_values, strict_parsing):
        if name not in od:
            od[name] = value
    return od


def Http404(start_response):
    start_response("404 NOT FOUND", [('Content-Type','text/plain')])
    return ["File not found"]

def get_storage(config):
    if config['storage'] == 'LocalStorage':
        return LocalStorage(**config)
    elif config['storage'] == 'S3Storage':
        return S3Storage(**config)
    else:
        raise Exception('Invalid storage backend.')


def app(environ,start_response):
    sto = get_storage(config)

    # throw away the leading slash on the path.
    path = environ['PATH_INFO']
    if path.startswith('/'):
        path = path[1:]

    if config['cloudfront_ugliness']:
        # DIRTY CLOUDFRONT HACK HERE
        # Stupid CloudFront doesn't pass query string arguments, so we have to
        # put image change params into the path.
        pathparts = path.split('/')
        filepath = '/'.join(pathparts[1:])
        params = oparse_qs(pathparts[0])
    else:
        filepath = path
        params = oparse_qs(environ['QUERY_STRING'])

    if config['ignore_favicon'] and filepath == 'favicon.ico':
        return Http404(start_response)

    try:
        im = sto.get_image(filepath)
    except MissingImage:
        return Http404(start_response)

    start_response("200 OK", [('Content-Type',im.mimetype)])
    im.process(options=params)
    return [im.contents]

def run():
    from gevent.wsgi import WSGIServer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', dest='config_file',
                    default='',
                    help='Path to the YAML config file.')

    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, 'r') as f:
            config.update(yaml.safe_load(f))

    # XXX: Can we monkeypatch with gevent to make our calls out to S3
    # non-blocking?  Do we get that for free by using the gevent wsgi server?
    address = config['host'], config['port']
    server = WSGIServer(address, app)
    try:
        print "Server running on port %s:%d. Ctrl+C to quit" % address
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
        print "Bye bye"

if __name__ == '__main__':
    run()
