#!/usr/bin/python
import sys

from setuptools import setup, find_packages

needs_wheel = {'release', 'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

setup(
    name='thumpy',
    version='0.4.2',
    author='Brent Tubbs/Berry Phillips',
    author_email='brent.tubbs@gmail.com/berryphillips@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires = [
        'pillow==3.2.0',
        'boto>=2.45.0',
        'gevent>=1.2.0',
        'pyyaml>=3.10',
        'six>=1.10.0',
    ],
    setup_requires=[
        'setuptools_scm',
    ] + wheel,
    entry_points = {
        'console_scripts': [
            'thumpy = thumpy:run',
        ],
    },
    url='https://github.com/btubbs/thumpy',
    description=('A Python web server that uses Pillow to dynamically scale, '
                 'crop, transform and serve images from S3 or the local '
                 'filesystem'),
    long_description=open('README.rst').read(),
)
