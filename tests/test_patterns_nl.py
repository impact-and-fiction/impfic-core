import unittest

import impfic_core.parse.doc as parse_docs
from impfic_core.parse.chunk import read_chunk_file
from impfic_core.pattern.patterns_nl import PatternNL


class TestPatternNLClause(unittest.TestCase):

    def setUp(self) -> None:
        self.trankit_file = 'tests/trankit_test_data-3.json.gz'
        doc_json = read_chunk_file(self.trankit_file)
        self.doc = parse_docs.trankit_json_to_doc(doc_json)
        self.pattern = PatternNL()

    def test_get_verb_clauses_returns_correct_number_of_clauses(self):
        self.test_sents = {
            "Ik heb het kunnen maken.": 1,
            "Ik ben aan het werken.": 1,
            "Ik werk hard om te kunnen leven.": 1,
            "Ik werk hard omdat die ander weinig doet.": 2,
            "Ik werk hard omdat die ander weinig gedaan heeft.": 2
        }
        for si, sent in enumerate(self.doc.sentences):
            with self.subTest(si):
                clauses = self.pattern.get_verb_clauses(sent)
                self.assertEqual(self.test_sents[sent.text], len(clauses))


class TestPatternNLPerfectTense(unittest.TestCase):

    def setUp(self) -> None:
        self.trankit_file = 'tests/trankit_test_data-2.json.gz'
        doc_json = read_chunk_file(self.trankit_file)
        self.doc = parse_docs.trankit_json_to_doc(doc_json)
        self.pattern = PatternNL()

    def test_is_present_perfect(self):
        self.test_sents = {
            "Mariken is mijn docent.": False,
            "Zij werkt elke dag.": False,
            "Zij heeft veel studenten.": False,
            "Zij moet veel werken.": False,
            "Zij heeft lang gestudeerd.": True,
            "Zij heeft veel mensen leren kennen.": True,
            "Zij is in veel landen geweest.": True,
            "Zij is een carrière gaan bouwen.": True,
            "Zij heeft lang moeten wachten.": True,
            "Ze studeerde hard.": False,
            "Maar ze had op haar studie gewacht.": False,
            # no (it is past perfect, so if we search now for present perfenct, then right)
            "Ze had op haar studie moeten wachten.": False,  # no (it is also past perfect)
            "Dat is niet leuk.": False,
            "Veel boeken zijn door Mariken gelezen.": True
        }
        test_num = 0
        for sent in self.doc.sentences:
            for clause in self.pattern.get_verb_clauses(sent):
                test_num += 1
                with self.subTest(test_num):
                    is_present_perfect = self.pattern.is_present_perfect_clause(clause)
                    self.assertEqual(self.test_sents[sent.text], is_present_perfect)
