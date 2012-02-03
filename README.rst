Meet Thumpy
===========

Thumpy is a Python web service that crops and scales images.  It doesn't store
anything.  It's meant to be used as an origin server sitting behind a CDN such
as Amazon CloudFront.

CONFIGURATION
=============

Settings are stored in the settings.yaml file.  They should include the name
and access keys to your S3 bucket.

HANDLING LOAD
=============

Cropping and scaling images is a bit more computationally intensive than
serving a text-based web page, so you may wonder what keeps Thumpy from
buckling under the strain of increased traffic.

First and foremost, Thumpy should not directly accept requests from the big bad
internet.  You want a big, long-lived cache in front of Thumpy, so that it only
serves the tiny proportion of requests that have never been requested before
(or that are expired from the cache).  

Even behind a CDN though, it would be possible for some joker to DoS your
server by making lots of requests for the same image, but with different scales
and croppings.  Thumpy combats this with the IP_THROTTLE_CAP and
IP_THROTTLE_INTERVAL options.  Both are required if you want to enable
throttling.  When set, Thumpy will stop serving requests from the same IP
address if that address has exceeded more than IP_THROTTLE_CAP requests in
IP_THROTTLE_INTERVAL seconds.

INTERFACE
=========

Thumpy serves images using the same paths as their storage location on S3.
Conversion parameters are specified in the query string, using an interface
mostly-identical to `TimThumb
<http://www.binarymoon.co.uk/projects/timthumb/>`_.  examples:

Scale the width to 200px, and the height proportionally::

  http://mythumpyserver.somewhere/castle.jpg?w=200

Scale the height to 150px, and the width propotionally::

  http://mythumpyserver.somewhere/castle.jpg?w=200

Specify both height and width::

  http://mythumpyserver.somewhere/castle.jpg?w=200&h=150


