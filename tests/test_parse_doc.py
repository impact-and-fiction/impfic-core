import unittest

from spacy.tokens import DocBin

import impfic_core.parse.doc as parse_docs
from impfic_core.parse.chunk import read_chunk_file


class TestReading(unittest.TestCase):

    def setUp(self) -> None:
        self.spacy_file = 'tests/spacy_test_data.json.gz'
        self.trankit_file = 'tests/trankit_test_data-1.json.gz'

    def test_can_read_trankit_parse_file(self):
        self.doc = read_chunk_file(self.trankit_file)

    def test_can_read_spacy_parse_json_file(self):
        self.doc = read_chunk_file(self.spacy_file)

    def test_can_read_spacy_parse_docbin_file(self):
        self.doc = read_chunk_file(self.spacy_file)


class TestDocSentTokenAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.spacy_file = 'tests/spacy_test_data.json.gz'
        self.trankit_file = 'tests/trankit_test_data-1.json.gz'
        doc_json = read_chunk_file(self.trankit_file)
        self.doc = parse_docs.trankit_json_to_doc(doc_json)

    def test_token_len_is_defined(self):
        token = self.doc.tokens[0]
        self.assertEqual(len(token.text), len(token))

    def test_sent_len_is_defined(self):
        sent = self.doc.sentences[0]
        self.assertEqual(len(sent.tokens), len(sent))

    def test_doc_len_is_defined(self):
        self.assertEqual(len(self.doc), sum([len(sent) for sent in self.doc.sentences]))

    def test_sent_iters_tokens(self):
        sent = self.doc.sentences[0]
        self.assertEqual(True, all([isinstance(token, parse_docs.Token) for token in sent]))


class TestTrankitParsing(unittest.TestCase):

    def setUp(self) -> None:
        self.trankit_file = 'tests/trankit_test_data-1.json.gz'
        self.doc_json = read_chunk_file(self.trankit_file)
        self.doc = parse_docs.trankit_json_to_doc(self.doc_json)

    def test_merge_docs_concatenates_sentences(self):
        merged_doc = parse_docs.merge_docs([self.doc, self.doc])
        self.assertEqual(2 * len(self.doc.sentences), len(merged_doc.sentences))

    def test_merge_docs_concatenates_tokens(self):
        merged_doc = parse_docs.merge_docs([self.doc, self.doc])
        self.assertEqual(2 * len(self.doc.tokens), len(merged_doc.tokens))


class TestTrankitTokens(unittest.TestCase):

    def setUp(self) -> None:
        self.trankit_file = 'tests/trankit_test_data-1.json.gz'
        self.doc_json = read_chunk_file(self.trankit_file)

    def test_parse_token(self):
        sent = self.doc_json['sentences'][0]
        token_json = sent['tokens'][0]
        token = parse_docs.trankit_json_to_token(0, 0, token_json)
        self.assertEqual(token_json['dspan'][0], token.start)


class TestTrankitEntities(unittest.TestCase):

    def setUp(self) -> None:
        self.trankit_file = 'tests/trankit_test_data-1.json.gz'
        self.doc_json = read_chunk_file(self.trankit_file)

    def test_trankit_can_create_entity(self):
        sent = self.doc_json['sentences'][1]
        token_offset = len(self.doc_json['sentences'][0])
        tokens = [parse_docs.trankit_json_to_token(ti, token_offset, token_json)
                  for ti, token_json in enumerate(sent['tokens'])]
        sent_start = tokens[0].start
        entity_tokens = [token for token in tokens if token.ner != 'O']
        entity = parse_docs.trankit_json_to_entity(entity_tokens, sent, sent_start)
        self.assertEqual('Ishmael', entity.text)
        self.assertEqual('PER', entity.label)

    def test_trankit_parses_entities(self):
        sent = self.doc_json['sentences'][1]
        token_offset = len(self.doc_json['sentences'][0])
        tokens = [parse_docs.trankit_json_to_token(ti+token_offset, ti, token_json)
                  for ti, token_json in enumerate(sent['tokens'])]
        sent_start = tokens[0].start
        sentence = parse_docs.trankit_json_to_sentence(0, sent)
        print('entities:', sentence.entities)
        self.assertEqual(sent_start, sentence.start)
        self.assertEqual(1, len(sentence.entities))


class TestSpacyTokens(unittest.TestCase):

    def setUp(self) -> None:
        self.spacy_file = 'tests/spacy_test_data.json.gz'
        self.doc_json = read_chunk_file(self.spacy_file)

    def test_parse_token(self):
        token_json = self.doc_json['tokens'][0]
        token_json['ner'] = 'O'
        token = parse_docs.spacy_json_to_token(0, 0, token_json, self.doc_json)
        for ki, key in enumerate(token.feats):
            with self.subTest(ki):
                self.assertIn(f"{key}={token.feats[key]}", token_json['morph'])


class TestSpacySentences(unittest.TestCase):

    def setUp(self) -> None:
        self.spacy_file = 'tests/spacy_test_data.json.gz'
        self.doc_json = read_chunk_file(self.spacy_file)

    def test_sorting_spacy_sentence_tokens_returns_correct_number_of_token_lists(self):
        sents_tokens = parse_docs.sort_spacy_tokens_by_sents(self.doc_json, 'tokens')
        self.assertEqual(len(sents_tokens), len(self.doc_json['sents']))

    def test_sorting_spacy_sentence_tokens_returns_correct_number_of_tokens(self):
        sents_tokens = parse_docs.sort_spacy_tokens_by_sents(self.doc_json, 'tokens')
        num_tokens = sum([len(tokens) for tokens in sents_tokens])
        self.assertEqual(len(self.doc_json['tokens']), num_tokens)

    def test_sorting_spacy_sentence_entities_returns_correct_number_of_entity_lists(self):
        sents_ents = parse_docs.sort_spacy_tokens_by_sents(self.doc_json, 'ents')
        self.assertEqual(len(sents_ents), len(self.doc_json['sents']))

    def test_sorting_spacy_sentence_entities_with_no_entities_returns_correct_number_of_entity_lists(self):
        self.doc_json['ents'] = []
        sents_ents = parse_docs.sort_spacy_tokens_by_sents(self.doc_json, 'ents')
        self.assertEqual(len(sents_ents), len(self.doc_json['sents']))

    def test_sorting_spacy_sentence_entities_returns_correct_number_of_entities(self):
        sents_ents = parse_docs.sort_spacy_tokens_by_sents(self.doc_json, 'ents')
        num_ents = sum([len(ents) for ents in sents_ents])
        self.assertEqual(len(self.doc_json['ents']), num_ents)


class TestSpacyDoc(unittest.TestCase):

    def setUp(self) -> None:
        self.spacy_file = 'tests/spacy_test_data.json.gz'
        self.doc_json = read_chunk_file(self.spacy_file)

    def test_spacy_doc_has_token_list(self):
        doc = parse_docs.spacy_json_to_doc(self.doc_json)
        self.assertEqual(len(doc.tokens), len(self.doc_json['tokens']))

    def test_spacy_doc_sets_correct_doc_id(self):
        doc = parse_docs.spacy_json_to_doc(self.doc_json)
        doc_idx = 347
        self.assertEqual(doc_idx, doc.tokens[doc_idx].doc_idx)

    def test_spacy_doc_sets_correct_id(self):
        doc = parse_docs.spacy_json_to_doc(self.doc_json)
        sent_idx = 14
        sent = doc.sentences[sent_idx]
        token_idx = 4
        self.assertEqual(token_idx, sent.tokens[token_idx].id)

    def test_spacy_doc_sets_correct_head(self):
        doc = parse_docs.spacy_json_to_doc(self.doc_json)
        ref_token_id = 347
        ref_token = doc.tokens[ref_token_id]
        head_token_id = self.doc_json['tokens'][ref_token_id]['head']
        head_token = doc.tokens[head_token_id]
        self.assertEqual(head_token.id, ref_token.head)

    def test_spacy_doc_head_is_within_sent(self):
        doc = parse_docs.spacy_json_to_doc(self.doc_json)
        for sent in doc.sentences:
            for token in sent.tokens:
                with self.subTest(token.doc_idx):
                    self.assertEqual(True, token.head < len(sent))

    def test_spacy_doc_without_entities_parses_correctly(self):
        self.doc_json['ents'] = []
        doc = parse_docs.spacy_json_to_doc(self.doc_json)
        self.assertEqual(len(doc.tokens), len(self.doc_json['tokens']))
