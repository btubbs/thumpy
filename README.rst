Meet Thumpy
===========

Thumpy is a Python web service that crops and scales images.  It doesn't store
anything.  It's meant to be used as an origin server sitting behind a CDN such
as Amazon CloudFront.

CONFIGURATION
=============

Settings are stored in the settings.yaml file.  They should include the name
and access keys to your S3 bucket.

INTERFACE
=========

Thumpy serves images using the same paths as their storage location on S3.
Conversion parameters are specified in the query string, using an interface
inspired by `TimThumb
<http://www.binarymoon.co.uk/projects/timthumb/>`_.  examples:

Scale the width to 200px, and the height proportionally::

  http://mythumpyserver.somewhere/castle.jpg?w=200

Scale the height to 150px, and the width propotionally::

  http://mythumpyserver.somewhere/castle.jpg?w=200

Specify both height and width::

  http://mythumpyserver.somewhere/castle.jpg?w=200&h=150


