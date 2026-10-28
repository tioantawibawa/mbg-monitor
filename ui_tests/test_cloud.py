import unittest
from io import BytesIO
from PIL import Image
from src.text_analysis import cloud_png

class CloudTests(unittest.TestCase):
    def test_cloud_is_deterministic_valid_png(self):
        frequencies = {'dirawat': 12, 'muntah': 8, 'pulih': 3}
        first = cloud_png(frequencies)
        self.assertEqual(first, cloud_png(frequencies))
        self.assertEqual(Image.open(BytesIO(first)).size, (1200, 550))
        self.assertIsNone(cloud_png({}))
