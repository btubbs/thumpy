Meet Thumpy
===========

Thumpy is a Python web service that crops and scales images.  It doesn't store
anything.  It's meant to be used as an origin server sitting behind a CDN such
as Amazon CloudFront.

Configuration
=============

Settings are stored in the settings.yaml file. They should include:
- the name and access keys to your S3 bucket
- compression quality (e.g. 80)
- list of CORS allowed hosts

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

Scaling (Post processing)
~~~~~~~~~~~~~~~~~~~~~~~~~
Same as Scaling (above) but applied to the output image after all transformations

  http://mythumpyserver.somewhere/castle.jpg?pw=200&ph=150

Cropping
~~~~~~~~

Crop the width to 200 and the height to 100::

	http://mythumpyserver.somewhere/castle.jpg?cw=200&ch=100

Crop the width and height to 50::

	http://mythumpyserver.somewhere/castle.jpg?cw=50&ch=50

- Thumpy will always scale first before any cropping.
- Thumpy always crops from the center of the image.

Reveal Mask / Zoom Cropping
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Minimum 3 parameters required:
- Top offset (e.g. zct=100px)
- Left offset (e.g. zcl=100px)
- Width or Height of the output crop from the offsets. If only one is provided the other will automatically be assigned the other's value.

The mask should be applied to the original image which means there is no scaling but only masking.

See: Scaling (Post processing) to get the scaled mask/crop.

Get 100px x 50px scaled crop off a larger image with a reveal mask of 350px x 175px applied at 20px x 10px top-left offset.

    http://mythumpyserver.somewhere/castle.jpg?zcw=350&zch=175&zct=20&zcl=10&pw=100&ph=50


Greyscale
~~~~~~~~~

Example of a greyscale image with no resizing::
	http://mythumpyserver.somewhere/castle.jpg?gray=1
