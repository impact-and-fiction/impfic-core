import unittest

import impfic_core.extract.extract_stats as et
from impfic_core.parse.chunk import read_chunk_file
from impfic_core.parse.doc import merge_docs


class TestCounting(unittest.TestCase):

    def setUp(self) -> None:
        self.chunk_file_gzip = 'tests/trankit_test_data-1.json.gz'
        self.book_chunk = read_chunk_file(self.chunk_file_gzip)

"""
    def test_count_words_sents(self):
        chars, words, sents = et.count_chars_words_sents(self.book_chunk)
        self.assertEqual(12209, chars)
        self.assertEqual(2601, words)
        self.assertEqual(106, sents)

    def test_get_pos_deprel_tag_count(self):
        pos_count, deprel_count = et.get_pos_deprel_tag_count(self.book_chunk)
        self.assertIn('NOUN', pos_count)
        self.assertIn('vocative', deprel_count)

    def test_get_word_lemma_token_count(self):
        word_count, lemma_count = et.get_word_lemma_token_count(self.book_chunk)
        self.assertIn('Ishmael', word_count)
        self.assertIn('Ishmael', lemma_count)

    def test_merge_chunks_json(self):
        book = merge_docs([self.book_chunk, self.book_chunk])
        chars, words, sents = et.count_chars_words_sents(book)
        self.assertEqual(24419, chars)
        self.assertEqual(5202, words)
        self.assertEqual(212, sents)

    def test_get_count_stats(self):
        count_stats = et.get_count_stats(self.book_chunk)
        self.assertIn('word_tokens', count_stats)
        self.assertIn('pos_NOUN', count_stats)

    def test_get_dist_stats(self):
        dist_stats = et.get_dist_stats(self.book_chunk)
        self.assertIn('word_length', dist_stats)
        self.assertIn('lemma_length', dist_stats)
        self.assertIn('sent_length', dist_stats)
"""
