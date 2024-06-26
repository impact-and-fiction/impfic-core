import math
import unittest

from impfic_core.measures.dispersion import compute_percentages
from impfic_core.measures.dispersion import compute_dispersion


class TestExpected(unittest.TestCase):

    def setUp(self) -> None:
        self.examples = [
            {
                'part_sizes': [200, 200, 200],
                'part_freqs': [3, 3, 3],
                'expected': [1/3, 1/3, 1/3],
                'observed': [1/3, 1/3, 1/3],
                'dispersion': 0.0
            },
            {
                'part_sizes': [200, 200, 200],
                'part_freqs': [9, 0, 0],
                'expected': [1/3, 1/3, 1/3],
                'observed': [1.0, 0.0, 0.0],
                'dispersion': 2/3
            },
            {
                'part_sizes': [100, 100, 9800],
                'part_freqs': [98, 1, 1],
                'expected': [0.01, 0.01, 0.98],
                'observed': [0.98, 0.01, 0.01],
                'dispersion': 0.97
            },
            {
                'part_sizes': [100, 100, 9800],
                'part_freqs': [0, 0, 100],
                'expected': [0.01, 0.01, 0.98],
                'observed': [0.0, 0.0, 1.0],
                'dispersion': 0.02
            },
            {
                'part_sizes': [45, 35, 20],
                'part_freqs': [1, 0, 0],
                'expected': [0.45, 0.35, 0.2],
                'observed': [1.0, 0.0, 0.0],
                'dispersion': 0.55
            },
            {
                'part_sizes': [45, 35, 20],
                'part_freqs': [0, 1, 0],
                'expected': [0.45, 0.35, 0.2],
                'observed': [0.0, 1.0, 0.0],
                'dispersion': 0.65
            },
        ]

    def test_expected_Gries_example_1(self):
        for ei, example in enumerate(self.examples):
            with self.subTest(ei):
                expected = compute_percentages(example['part_sizes'])
                self.assertEqual(example['expected'], expected)

    def test_observed_Gries_example_1(self):
        for ei, example in enumerate(self.examples):
            with self.subTest(ei):
                observed = compute_percentages(example['part_freqs'])
                self.assertEqual(example['observed'], observed)

    def test_dispersion_Gries_example_1(self):
        for ei, example in enumerate(self.examples):
            with self.subTest(ei):
                dispersion = compute_dispersion(example['part_sizes'], example['part_freqs'])
                self.assertEqual(True, math.isclose(example['dispersion'], dispersion))

    def test_dispersion_for_unequally_sized_list_returns_an_error(self):
        part_sizes = [200, 200, 200, 200]
        part_freqs = [3, 3, 3]
        self.assertRaises(ValueError, compute_dispersion, part_sizes, part_freqs)
