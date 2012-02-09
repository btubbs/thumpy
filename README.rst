Meet Thumpy
===========

Thumpy is a Python web service that crops and scales images.  It doesn't store
anything.  It's meant to be used as an origin server sitting behind a CDN such
as Amazon CloudFront.

Configuration
=============

Settings are stored in the settings.yaml file.  They should include the name
and access keys to your S3 bucket.

Interface
=========

Thumpy serves images using the same paths as their storage location on S3.
Conversion parameters are specified in the query string, using an interface
inspired by `TimThumb
<http://www.binarymoon.co.uk/projects/timthumb/>`_.  

examples:

Scaling
~~~~~~~

Scale the width to 200px, and the height proportionally::

  http://mythumpyserver.somewhere/castle.jpg?w=200

Scale the height to 150px, and the width propotionally::

  http://mythumpyserver.somewhere/castle.jpg?w=200

Specify both height and width::

  http://mythumpyserver.somewhere/castle.jpg?w=200&h=150

Cropping
~~~~~~~~

Crop the width to 200 and the height to 100::

	http://mythumpyserver.somewhere/castle.jpg?cw=200&ch=100

Crop the width and height to 50::

	http://mythumpyserver.somewhere/castle.jpg?cw=50&ch=50

- Thumpy will always scale first before any cropping.
- Thumpy always crops from the center of the image.

Greyscale
~~~~~~~~~

Example of a greyscale image with no resizing::
	http://mythumpyserver.somewhere/castle.jpg?gray=1


Cloudfront Ugliness
~~~~~~~~~~~~~~~~~~~

If the "cloudfront_ugliness" option in thumpy's config is set to true, then the image modification parameters will be pulled from the first segment of the path instead of the URL query string.

This is to workaround Amazon Cloudfront dropping the URL query string when making requests to your origin server.  Example::

	http://mycloudfrontdist.somewhere/w=100/path/to/image/castle.jpg

For the original, unaltered image, place an "o" where the query string would go, like this::
	
	http://mycloudfrontdist.somewhere/o/path/to/image/castle.jpg




