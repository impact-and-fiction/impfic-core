import gzip
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

import pandas as pd

REPORT_POS = ['DET', 'VERB', 'ADV', 'ADP', 'CCONJ', 'PROPN', 'ADJ', 'AUX', 'NOUN', 'SCONJ', 'PRON', 'PUNCT']

HEADERS = ['isbn', 'sent_num', 'sent_len'] + REPORT_POS


@dataclass
class Token:

    word: str
    lemma: str
    upos: str
    deprel: str


@dataclass
class Sentence:

    id: int
    tokens: List[Token]
    text: str


@dataclass
class Book:

    text: str
    sentences: List[Sentence]

    @property
    def tokens(self):
        return [token for sent in self.sentences for token in sent.tokens]


def json_to_token(token: Dict[str, any]) -> Token:
    return Token(
        word=token['text'],
        lemma=token['lemma'],
        upos=token['upos'],
        deprel=token['deprel'] if 'deprel' in token else 'no_deprel'
    )


def json_to_sentence(sentence: Dict[str, any]) -> Sentence:
    return Sentence(
        id=sentence['id'],
        text=sentence['text'],
        tokens=[json_to_token(token) for token in sentence['tokens']]
    )


def json_to_book(book_json: Dict[str, any]) -> Book:
    sentences = [json_to_sentence(sent) for sent in book_json['sentences']]
    return Book(
        text=book_json['text'],
        sentences=sentences
    )


def merge_book_chunks(book_chunks: List[Book]) -> Book:
    """Merge a list of Book chunks into a single Book instance."""
    return Book(
        text='\n'.join([chunk.text for chunk in book_chunks]),
        sentences=[sent for chunk in book_chunks for sent in chunk.sentences]
    )


def read_chunk_file(chunk_file: str) -> Book:
    """Read a parsed chunk of book text from file and return as a Book instance."""
    if chunk_file.endswith('.gz'):
        with gzip.open(chunk_file, 'rt') as fh:
            chunk_json = json.load(fh)
            chunk_book = json_to_book(chunk_json)
    else:
        with open(chunk_file, 'rt') as fh:
            chunk_json = json.load(fh)
            chunk_book = json_to_book(chunk_json)
    return chunk_book


def collect_per_sent_stats(isbn: str, book: Book) -> List[List[Union[str, int]]]:
    """Collect per sentence statistics on number of tokens and POS-tag frequency."""
    rows = []
    for si, sent in enumerate(book.sentences):
        pos_freq = Counter([token.upos for token in sent.tokens])
        row = [isbn, si, len(sent.tokens)]
        row.extend([pos_freq[pos] for pos in REPORT_POS])
        rows.append(row)
    return rows


def collect_book_stats(isbn: str, book: Book, stats_dir: str) -> None:
    rows = collect_per_sent_stats(isbn, book)
    stats_file = os.path.join(stats_dir, f'book_stats-{isbn}.tsv.gz')
    df = pd.DataFrame(data=rows, columns=HEADERS)
    df.to_csv(stats_file, compression='gzip', sep='\t')


def parse_chunk_file_name(chunk_file: str) -> Tuple[Union[str, None], Union[int, None]]:
    chunk_dir, chunk_fname = os.path.split(chunk_file)
    if m := re.match(r"^(.*)-(\d+)\.json(\.gz)?$", chunk_fname):
        book_id = m.group(1)
        chunk_num = int(m.group(2))
        return book_id, chunk_num
    else:
        return None, None


def count_chars_words_sents(book_chunk: Book) -> Tuple[int, int, int]:
    num_words, num_sents = 0, 0
    chars = len(book_chunk.text)
    for sent in book_chunk.sentences:
        num_sents += 1
        num_words += len(sent.tokens)
    return chars, num_words, num_sents


def get_pos_deprel_tag_count(book_chunk: Book) -> Tuple[Counter, Counter]:
    pos_count = Counter()
    deprel_count = Counter()
    for sent in book_chunk.sentences:
        pos_count.update([token.upos for token in sent.tokens])
        deprel_count.update([token.deprel for token in sent.tokens])
    return pos_count, deprel_count


def get_word_lemma_token_count(book_chunk: Book) -> Tuple[Counter, Counter]:
    word_count = Counter()
    lemma_count = Counter()
    for sent in book_chunk.sentences:
        word_count.update([token.word for token in sent.tokens])
        lemma_count.update([token.lemma for token in sent.tokens])
    return word_count, lemma_count


def get_count_stats(book_chunk: Book) -> Dict[str, int]:
    num_chars, num_words, num_sents = count_chars_words_sents(book_chunk)
    word_count, lemma_count = get_word_lemma_token_count(book_chunk)
    pos_count, deprel_count = get_pos_deprel_tag_count(book_chunk)
    count_stats = {
        'word_tokens': sum(word_count.values()),
        'word_types': len(word_count),
        'lemma_tokens': sum(lemma_count.values()),
        'lemma_types': len(lemma_count),
        'num_sents': num_sents,
        'num_chars': num_chars,
    }
    for pos in pos_count:
        count_stats[f"pos_{pos}"] = pos_count[pos]
    for deprel in deprel_count:
        count_stats[f"deprel_{deprel}"] = deprel_count[deprel]
    return count_stats


def get_dist_stats(book_chunk: Book) -> Dict[str, Counter]:
    dist_stats = {
        'word_length': Counter(),
        'lemma_length': Counter(),
        'sent_length': Counter()
    }
    for sent in book_chunk.sentences:
        dist_stats['sent_length'].update([len(sent.tokens)])
        dist_stats['word_length'].update([len(token.word) for token in sent.tokens])
        dist_stats['lemma_length'].update([len(token.lemma) for token in sent.tokens])
    return dist_stats
