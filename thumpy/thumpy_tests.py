import os
import unittest
import thumpy

here = os.path.dirname((os.path.realpath(__file__)))

config = {
    'host': 'localhost',
    'port': 8000,
    'ignore_favicon': True,
    'cloudfront_ugliness': False,
    'storage': 'LocalStorage',
    'root': here,
}


class ThumpyTestCase(unittest.TestCase):
    def setUp(self):
        self.sto = thumpy.get_storage(config)
        self.im = self.sto.get_image('Lenna.png')

    def test_resize(self):
        assert len(self.im.contents) == 479778
        self.im.scale_to_width(30)
        assert len(self.im.contents) == 2229
