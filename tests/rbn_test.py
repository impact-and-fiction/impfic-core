import unittest

from impfic_core.resources.rbn import RBN


class RBNTest(unittest.TestCase):

    def test_can_read_file(self):
        rbn_file = 'tests/rbn_test_data.json'
        error = None
        try:
            RBN(rbn_file)
        except BaseException as err:
            error = err
        self.assertEqual(error, None)

    def test_can_lookup_term(self):
        rbn_file = 'tests/rbn_test_data.json'
        rbn = RBN(rbn_file)
        self.assertEqual(rbn.has_term('test'), True)

    def test_can_get_terms_by_pos(self):
        rbn_file = 'tests/rbn_test_data.json'
        rbn = RBN(rbn_file)
        self.assertEqual(len(rbn.get_pos_terms('noun')), 1)

    def test_can_get_terms_by_sem_type(self):
        rbn_file = 'tests/rbn_test_data.json'
        rbn = RBN(rbn_file)
        self.assertEqual(len(rbn.get_sem_type('abstract')), 1)

    def test_can_get_term_info(self):
        rbn_file = 'tests/rbn_test_data.json'
        rbn = RBN(rbn_file)
        term = rbn.get_term('test')
        self.assertEqual(term['id-form'], 'test')

    def test_get_unknown_term_returns_none(self):
        rbn_file = 'tests/rbn_test_data.json'
        rbn = RBN(rbn_file)
        term = rbn.get_term('nest')
        self.assertEqual(term, None)


if __name__ == "__main__":
    unittest.main()
