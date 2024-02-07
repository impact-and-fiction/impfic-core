import unittest

import impfic_core.parse.chunk as parse_chunk


class TestRead(unittest.TestCase):

    def setUp(self) -> None:
        self.trankit_chunk_file_gzip = 'tests/trankit_test_data-1.json.gz'
        self.trankit_chunk_file = 'tests/trankit_test_data-1.json'
        self.spacy_chunk_file_gzip = 'tests/spacy_test_data.json.gz'

    def test_read_json(self):
        book_chunk = parse_chunk.read_chunk_file(self.trankit_chunk_file)
        self.assertEqual(dict, type(book_chunk))
        self.assertIn('text', book_chunk)

    def test_read_json_from_gzip(self):
        book_chunk = parse_chunk.read_chunk_file(self.trankit_chunk_file_gzip)
        self.assertEqual(dict, type(book_chunk))
        self.assertIn('text', book_chunk)

    def test_parse_filename(self):
        book_id, chunk_num = parse_chunk.parse_chunk_file_name(self.trankit_chunk_file)
        self.assertEqual(1, chunk_num)

    def test_parse_filename_gzip(self):
        book_id, chunk_num = parse_chunk.parse_chunk_file_name(self.trankit_chunk_file_gzip)
        self.assertEqual(1, chunk_num)

    def test_parse_doc_from_json_gzip(self):
        book_chunk = parse_chunk.parse_chunk_file(self.trankit_chunk_file_gzip)
        self.assertEqual(parse_chunk.Doc, type(book_chunk))

    def test_parse_doc_from_spacy_gzip(self):
        book_chunk = parse_chunk.parse_chunk_file(self.spacy_chunk_file_gzip)
        self.assertEqual(parse_chunk.Doc, type(book_chunk))
