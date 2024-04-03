import os
from collections import Counter
from typing import Dict, List, Tuple, Union

import pandas as pd

from impfic_core.parse.doc import Doc

REPORT_POS = ['DET', 'VERB', 'ADV', 'ADP', 'CCONJ', 'PROPN', 'ADJ', 'AUX', 'NOUN', 'SCONJ', 'PRON', 'PUNCT']

HEADERS = ['isbn', 'sent_num', 'sent_len'] + REPORT_POS


def collect_per_sent_stats(isbn: str, doc: Doc) -> List[List[Union[str, int]]]:
    """Collect per sentence statistics on number of tokens and POS-tag frequency."""
    rows = []
    for si, sent in enumerate(doc.sentences):
        pos_freq = Counter([token.upos for token in sent.tokens])
        row = [isbn, si, len(sent.tokens)]
        row.extend([pos_freq[pos] for pos in REPORT_POS])
        rows.append(row)
    return rows


def collect_book_stats(isbn: str, book: Doc, stats_dir: str) -> None:
    rows = collect_per_sent_stats(isbn, book)
    stats_file = os.path.join(stats_dir, f'book_stats-{isbn}.tsv.gz')
    df = pd.DataFrame(data=rows, columns=HEADERS)
    df.to_csv(stats_file, compression='gzip', sep='\t')


def count_chars_words_sents(book_chunk: Doc) -> Tuple[int, int, int]:
    num_words, num_sents = 0, 0
    chars = len(book_chunk.text)
    for sent in book_chunk.sentences:
        num_sents += 1
        num_words += len(sent.tokens)
    return chars, num_words, num_sents


def get_pos_deprel_tag_count(book_chunk: Doc) -> Tuple[Counter, Counter]:
    pos_count = Counter()
    deprel_count = Counter()
    for sent in book_chunk.sentences:
        pos_count.update([token.upos for token in sent.tokens])
        deprel_count.update([token.deprel for token in sent.tokens])
    return pos_count, deprel_count


def get_word_lemma_token_count(book_chunk: Doc) -> Tuple[Counter, Counter]:
    word_count = Counter()
    lemma_count = Counter()
    for sent in book_chunk.sentences:
        word_count.update([token.text for token in sent.tokens])
        lemma_count.update([token.lemma for token in sent.tokens])
    return word_count, lemma_count


def get_count_stats(book_chunk: Doc) -> Dict[str, int]:
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


def get_dist_stats(book_chunk: Doc) -> Dict[str, Counter]:
    dist_stats = {
        'word_length': Counter(),
        'lemma_length': Counter(),
        'sent_length': Counter()
    }
    for sent in book_chunk.sentences:
        dist_stats['sent_length'].update([len(sent.tokens)])
        dist_stats['word_length'].update([len(token.text) for token in sent.tokens])
        dist_stats['lemma_length'].update([len(token.lemma) for token in sent.tokens])
    return dist_stats
