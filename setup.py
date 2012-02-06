#!/usr/bin/python
from setuptools import setup, find_packages

setup(
    name='thumpy',
    version='0.0.1',
    author='Brent Tubbs/Berry Phillips',
    author_email='brent.tubbs@gmail.com/berryphillips@gmail.com',
	packages=find_packages(),
    include_package_data=True,
	install_requires = [
        'PIL==1.1.7',
        'boto==2.1.0',
        'gevent==0.13.6',
        'pyyaml==3.10',
	],
    entry_points = {
        'console_scripts': [
            'thumpy = thumpy:run',
        ],
    },
    url='http://bits.btubbs.com/thumpy',
    description=('A Python web server that uses PIL to dynamically scale, '
                 'crop, transform and serve images from S3 or the local '
                 'filesystem'),
    long_description=open('README.rst').read(),
)
