import unittest

from resources.rbn import RBN


class RBNTest(unittest.TestCase):

    def test_can_read_file(self):
        rbn_file = 'rbn_test_data.json'
        error = None
        try:
            RBN(rbn_file)
        except BaseException as err:
            error = err
        self.assertEqual(error, None)


if __name__ == "__main__":
    unittest.main()
