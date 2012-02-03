import os
import unittest
import thumpy

# Add src dir to sys.path
here = os.path.dirname((os.path.realpath(__file__)))


class ThumpyTestCase(unittest.TestCase):
    def setUp(self):
        lenna = os.path.join(here, 'Lenna.png')
        self.im = thumpy.Image(lenna, thumpy.LocalStorage())

    def test_resize(self):
        assert len(self.im.contents) == 479778
        self.im.scale_to_width(30)
        assert len(self.im.contents) == 2229
