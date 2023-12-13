import gzip
import json
import os
import re
from collections import Counter
from typing import Dict, List, Tuple, Union


def read_chunk_file(chunk_file: str) -> Dict[str, any]:
    if chunk_file.endswith('.gz'):
        with gzip.open(chunk_file, 'rt') as fh:
            chunk_json = json.load(fh)
    else:
        with open(chunk_file, 'rt') as fh:
            chunk_json = json.load(fh)
    return chunk_json


def parse_chunk_file_name(chunk_file: str) -> Tuple[Union[str, None], Union[int, None]]:
    chunk_dir, chunk_fname = os.path.split(chunk_file)
    if m := re.match(r"^(.*)-(\d+)\.json(\.gz)?$", chunk_fname):
        book_id = m.group(1)
        chunk_num = int(m.group(2))
        return book_id, chunk_num
    else:
        return None, None


def count_chars_words_sents(chunk_json: Dict[str, any]) -> Tuple[int, int, int]:
    num_words, num_sents = 0, 0
    chars = len(chunk_json['text'])
    for sent in chunk_json['sentences']:
        num_sents += 1
        num_words += len(sent['tokens'])
    return chars, num_words, num_sents


def get_pos_deprel_tag_count(chunk_json: Dict[str, any]) -> Tuple[Counter, Counter]:
    pos_count = Counter()
    deprel_count = Counter()
    for sent in chunk_json['sentences']:
        pos_count.update([token['upos'] for token in sent['tokens']])
        deprel_count.update([token['deprel'] if 'deprel' in token else 'nodeprel' for token in sent['tokens']])
    return pos_count, deprel_count


def get_word_lemma_token_count(chunk_json: Dict[str, any]) -> Tuple[Counter, Counter]:
    word_count = Counter()
    lemma_count = Counter()
    for sent in chunk_json['sentences']:
        word_count.update([token['text'] for token in sent['tokens']])
        lemma_count.update([token['lemma'] for token in sent['tokens']])
    return word_count, lemma_count


def get_count_stats(chunk_json: Dict[str, any]):
    num_chars, num_words, num_sents = count_chars_words_sents(chunk_json)
    word_count, lemma_count = get_word_lemma_token_count(chunk_json)
    pos_count, deprel_count = get_pos_deprel_tag_count(chunk_json)
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


def get_dist_stats(chunk_json: Dict[str, any]) -> Dict[str, Counter]:
    dist_stats = {
        'word_length': Counter(),
        'lemma_length': Counter(),
        'sent_length': Counter()
    }
    for sent in chunk_json['sentences']:
        dist_stats['sent_length'].update([len(sent['tokens'])])
        dist_stats['word_length'].update([len(token['text']) for token in sent['tokens']])
        dist_stats['lemma_length'].update([len(token['lemma']) for token in sent['tokens']])
    return dist_stats


def merge_chunks_json(chunks_json: List[Dict[str, any]]) -> Dict[str, any]:
    return {
        'text': '\n'.join([cj['text'] for cj in chunks_json]),
        'sentences': [sent for cj in chunks_json for sent in cj['sentences']],
    }
