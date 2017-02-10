#!/usr/bin/env python

"""
Thumpy web process to resize images.
"""


import argparse
import os
import traceback

import yaml
from six.moves.urllib.parse import parse_qsl
from six import BytesIO

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from PIL import ImageOps, Image as PILImage
from boto import connect_s3


class MissingImage(Exception):
    pass


class S3Storage(object):
    def __init__(self, s3_key, s3_secret, s3_bucket, quality=75, **kwargs):
        self.conn = connect_s3(s3_key, s3_secret)
        self.bucket = self.conn.get_bucket(s3_bucket)
        self.quality = quality

    def get_image(self, path):
        # Make a boto connection, pull down the file, and return the file
        # object.  If not found, return None

        key = self.bucket.get_key(path)
        if path is None:
            raise MissingImage("No S3 key for %s" % path)

        # For returning PIL "Image" from a url see
        # http://blog.hardlycode.com/pil-image-from-url-2011-01/.  That will
        # need to be adapted a little bit to work from S3, but should be fine.

        if not key or not key.exists():
            raise MissingImage("No S3 file for %s" % path)

        im = Image(path, quality=self.quality)
        # actually stick the data in there
        im.storage = self
        try:
            im.im = PILImage.open(BytesIO(key.read()))
        except IOError:
            raise MissingImage("Could not read data for " + path)
        return im


class LocalStorage(object):
    def __init__(self, root=None, quality=75, **kwargs):
        self.root = os.path.realpath(root or os.path.dirname(__file__))
        self.quality = quality

    def get_image(self, path):
        f = os.path.realpath(os.path.join(self.root, path))

        # raise an exception if someone tries to break out of jail with paths
        # like "../../../blah"
        assert f.startswith(self.root)

        # TODO: ensure that the file is actually an image.
        im = Image(path, quality=self.quality)
        try:
            im.im = PILImage.open(f)
        except IOError:
            raise MissingImage("No file for %s" % path)
        im.storage = self
        return im


class Image(object):
    def __init__(self, path, quality=75):
        self.path = path
        self.quality=quality

        # Browsers like a image/jpeg content-type but not image/jpg.
        # Pillow wants a format that's like 'jpeg', 'gif', 'png', or 'bmp'
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

    def zoom_crop(self, w=None, h=None, left=None, top=None):
        if (w is None and h is None) or left is None or top is None:
            raise Exception('Zoom crop requires at least width or height and both left and top')

        w = int(float(w)) if w is not None else int(float(h))
        h = int(float(h)) if h is not None else int(float(w))

        left = int(float(left))
        top = int(float(top))

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

        # Now do any zoom cropping.
        if any(option in options for option in ['zcw', 'zch', 'zct', 'zcl']):
            self.zoom_crop(w=options.get('zcw'),
                           h=options.get('zch'),
                           top=options.get('zct'),
                           left=options.get('zcl'))

        # Post-scaling operations
        if 'pw' in options and 'ph' in options:
            # scale both width and height
            self.scale(int(options['pw']), int(options['ph']))
        elif 'pw' in options:
            # scale width to w, and height proportionally
            self.scale_to_width(int(options['pw']))
        elif 'ph' in options:
            # scale height to h, and width proportionally
            self.scale_to_height(int(options['ph']))

        # Other filters
        if 'gray' in options:
            self.im = ImageOps.grayscale(self.im)

    @property
    def contents(self):
        # Write the file contents out to a specific format, but just in memory.
        # Return the file obj
        f = BytesIO()
        self.im.save(f, self.fmt, quality=self.quality)
        f.seek(0)
        return f

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
    for name, value in parse_qsl(qs, keep_blank_values, strict_parsing):
        if name not in od:
            od[name] = value
    return od


def Http404(start_response):
    start_response("404 NOT FOUND", [('Content-Type','text/plain')])
    return [b"File not found"]

def Http500(start_response):
    start_response("500 SERVER ERROR", [('Content-Type','text/plain')])
    return [b"Server Error"]

def get_storage(config):
    if config['storage'] == 'LocalStorage':
        return LocalStorage(**config)
    elif config['storage'] == 'S3Storage':
        return S3Storage(**config)
    else:
        raise Exception('Invalid storage backend.')

def is_request_cors_eligible(environ, config):
    if 'HTTP_ORIGIN' not in environ:
        return False

    http_origin = environ['HTTP_ORIGIN']

    if http_origin in config['cors_hosts']:
        return True
    else:
        return False

def get_cors_headers(environ):
    http_origin = environ['HTTP_ORIGIN']

    return [
        ('Access-Control-Allow-Origin', http_origin),
    ]


class App():
    def __init__(self, config):
        self.config = config

    def __call__(self, environ, start_response):
        # catch all server errors.  only dump stacktrace if self.config['debug'] is
        # true.
        try:
            sto = get_storage(self.config)

            # throw away the leading slash on the path.
            path = environ['PATH_INFO']
            if path.startswith('/'):
                path = path[1:]

            filepath = path
            params = oparse_qs(environ['QUERY_STRING'])

            if self.config['ignore_favicon'] and filepath == 'favicon.ico':
                return Http404(start_response)

            try:
                im = sto.get_image(filepath)
            except MissingImage:
                return Http404(start_response)

            im.process(options=params)
            contents = im.contents
            headers = [
                ('Content-Type', im.mimetype),
                ('Expires', 'Thu, 01 Dec 2050 16:00:00 GMT'),
                ('Cache-Control', 'max-age=31536000'),
            ]
            if is_request_cors_eligible(environ, self.config) is True:
                headers.extend(get_cors_headers(environ))

            start_response("200 OK", headers)
            return contents
        except:
            traceback.print_exc()
            return Http500(start_response)


def nice_bool(val):
    if isinstance(val, str):
        val = val.lower()
    if val in {True, 'yes', 'true', '1'}:
        return True
    if val in {False, 'no', 'false', '0'}:
        return False
    raise ValueError("Cannot parse %s into a bool" % val)


def get_config():
    # Default configuration here.  Override by specifying a settings.yaml file with
    # your own values.
    config = {
        'host': os.getenv('HOST', 'localhost'),
        'port': int(os.getenv('PORT', 8000)),
        'ignore_favicon': nice_bool(os.getenv('IGNORE_FAVICON', True)),
        'cloudfront_ugliness': nice_bool(os.getenv('CLOUDFRONT_UGLINESS', False)),
        'storage': 'LocalStorage',
        'quality': 75,
        'cors_hosts': [],
        'debug': nice_bool(os.getenv('DEBUG', False)),

        # for s3 storage
        's3_key': os.getenv('AWS_ACCESS_KEY_ID'),
        's3_secret': os.getenv('AWS_SECRET_ACCESS_KEY'),
        's3_bucket': os.getenv('S3_BUCKET'),

        # for local storage
        'root': os.getenv('THUMPY_ROOT')
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', dest='config_file',
                    default='',
                    help='Path to the YAML config file.')

    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, 'r') as f:
            config.update(yaml.safe_load(f))
    return config

def run():
    from gevent.wsgi import WSGIServer
    config = get_config()

    address = config['host'], config['port']
    server = WSGIServer(address, App(config))
    try:
        print("Server running on port %s:%d. Ctrl+C to quit" % address)
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
        print("Bye bye")

if __name__ == '__main__':
    run()
