from typing import Union
from collections import defaultdict
import json
import gzip


def read_rbn(rbn_file: str):
    if rbn_file.endswith('gz'):
        with gzip.open(rbn_file, 'rt') as fh:
            return json.load(fh)
    else:
        with open(rbn_file, 'rt') as fh:
            return json.load(fh)


class RBN:

    def __init__(self, rbn_file: str):
        self.rbn_file = rbn_file
        self.terms = read_rbn(rbn_file)
        self.term_info = {}
        self.pos_terms = defaultdict(list)
        self._index_terms()

    def _index_terms(self):
        for term in self.terms:
            if 'id-cat' not in term:
                continue
            self.term_info[term['id-form']] = term
            self.pos_terms[term['id-cat']].append(term)

    def has_term(self, term: str) -> bool:
        return term in self.term_info

    def get_term(self, term: str) -> Union[None, dict]:
        if self.has_term(term):
            return self.term_info[term]
        else:
            return None

    def get_sem_type(self, sem_type: str, pos_tag: str = None):
        if pos_tag:
            return [term for term in self.get_pos_terms[pos_tag] if term['sem-type'] == sem_type]
        else:
            return [term for term in self.terms if term['sem-type'] == sem_type]

    def get_pos_terms(self, pos_tag: str):
        if pos_tag not in self.pos_terms:
            raise KeyError(f'unknown pos tag {pos_tag}')
        return [term for term in self.pos_terms[pos_tag]]
