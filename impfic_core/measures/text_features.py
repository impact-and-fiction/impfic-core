""" This script is generated from a Jupyter notebook and contains analysis functions
related to word usage in fiction novels.  """

import glob
import gzip
import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from impfic_core.api import Doc
from impfic_core.parse.doc import trankit_json_to_doc
from impfic_core.api import PatternNL, get_lang_patterns
from impfic_core.parse import book_model


# load
def get_book_chunk_files(book_id: str, data_dir: str, parser: str = 'trankit') -> list[str]:
    """
    Helper function to find .json.gz files for a given subdirectory (identified by book id) 
    within the data directory.

    Args:
        book_id (str): The identifier of the book.
        data_dir (str): The directory path to search for book chunk files.
        parser (str): The parser used for generating the parse trees ('trankit' or 'spacy')

    Returns:
        List[str]: A list of paths to the book chunk files.
    """
    return glob.glob(os.path.join(data_dir, f'{book_id}/*.{parser}.json.gz'))


def load_book_chunks(data_dir: str, max_items: int = None) -> Dict[str, List[str]]:
    """
    Loads and filters book chunks based on the presence of
    JSON.GZ files within each book's directory.

    Args:
        data_dir (str): The directory to search for book data.
        max_items (int): The maximum number of books to load.

    Returns:
        List[str]: A list of ISBNs for books with available data.
    """
    book_dirs = glob.glob(os.path.join(data_dir, '*'))
    if max_items is not None:
        book_dirs = book_dirs[:max_items]
    book_ids = [os.path.split(book_dir)[-1] for book_dir in book_dirs]
    book_subdirs = [book_id for book_id in book_ids if len(get_book_chunk_files(book_id, data_dir)) > 0]
    isbn_chunk_files = defaultdict(list)
    for book_subdir in book_subdirs:
        book_chunk_files = get_book_chunk_files(book_subdir, data_dir)
        for book_chunk_file in book_chunk_files:
            if match := re.search(r"_(978\d{9}[0-9Xx])\b", book_chunk_file):
                isbn = match.group(1)
                isbn_chunk_files[isbn].append(book_chunk_file)
            else:
                raise ValueError(f"cannot identify ISBN in chunk filename: {book_chunk_file}")
    return isbn_chunk_files


# analyse
def read_book_chunk_file(book_chunk_file: str) -> dict:
    """
    Reads a book chunk file and returns its content as a dict

    Args:
        book_chunk_file (str): The path to the book chunk file.

    Returns:
        Dict: The content of the book chunk file as a dictionary.
    """
    with gzip.open(book_chunk_file, 'rt') as fh:
        book_chunk = json.load(fh)
    return book_chunk


def read_book_chunk_files(book_chunk_files: List[str]) -> dict:
    """
    Generator function that yields the content of each book chunk file as a dictionary.

    Args:
        book_chunk_files (List[str]): A list of paths to the book chunk files.

    Yields:
        dict: The content of a book chunk file as a dictionary.
    """
    for book_chunk_file in book_chunk_files:
        yield read_book_chunk_file(book_chunk_file)


def get_all_book_stats(isbn_chunk_files: Dict[str, List[str]], lang: str):
    """Overarching function that extracts books' stats"""
    all_stats = []
    pattern = get_lang_patterns(lang)
    # add progress bar
    for isbn in tqdm(isbn_chunk_files, desc="Processing Books"):
        book_stats = get_book_stats(isbn, isbn_chunk_files[isbn], pattern)
        all_stats.append(book_stats)
    return all_stats


def get_book_stats(isbn: str, book_chunk_files: List[str], pattern: PatternNL) -> list[Union[str, int, float]]:
    """
    Gets book statistics

    Returns:
        list[str, int, float]: A list of mixed types containing the ISBN followed by
        various statistics for the book, including counts and measures of sentence
        length as integers and floats.
    """
    book_chunks = [book_chunk for book_chunk in read_book_chunk_files(book_chunk_files)]
    book_docs = [trankit_json_to_doc(book_chunk, skip_bad_tokens=True) for book_chunk in book_chunks]
    verb_vars = get_verb_count(book_docs, pattern)

    total, present, past, pv = verb_vars[:4]
    clause_count, presp, pastp, press, pasts = verb_vars[4:9]
    no_tense_simple, no_tense_perfect, no_tense_no_aspect, both_tense, both_aspect = verb_vars[9:]

    num_tokens, num_sents, sent_len_mean, sent_len_median, sent_len_stdev, unique_tokens = get_length_stats(book_docs)
    pron_count, propn_count, det_count = get_funcword_count(book_docs)
    noun_count, adj_count, adv_count, intj_count = get_uposword_count(book_docs)
    sconj_count, cconj_count, punct_count = get_gramword_count(book_docs)
    # added present_perfect_count below as 'pp'
    stats = [isbn,
             total, present, past, pv, clause_count, presp, pastp, press, pasts, no_tense_simple, no_tense_perfect,
             no_tense_no_aspect, both_tense, both_aspect,
             num_tokens, num_sents, sent_len_mean, sent_len_median, sent_len_stdev,
             unique_tokens, pron_count, propn_count, det_count, noun_count, adj_count, adv_count, intj_count,
             sconj_count, cconj_count, punct_count]
    return stats


def get_length_stats(book_docs: List[Doc]):
    """Count length of sentences in book docs"""
    sentence_lengths = []
    num_tokens = 0
    num_sents = 0
    unique_tokens = set()
    for doc in book_docs:
        num_sents += len(doc.sentences)
        for sentence in doc.sentences:
            sentence_length = len(sentence)
            sentence_lengths.append(sentence_length)
            num_tokens += sentence_length
            unique_tokens.update(token.text for token in sentence.tokens)
    unique_tokens_count = len(unique_tokens)
    sentence_lengths = np.array(sentence_lengths)
    sent_len_mean = sentence_lengths.mean()
    sent_len_median = np.median(sentence_lengths)
    sent_len_stdev = sentence_lengths.std()
    return num_tokens, num_sents, sent_len_mean, sent_len_median, sent_len_stdev, unique_tokens_count


def classify_clause_tense(clause, pattern: PatternNL):
    tense = 'no_tense'
    if pattern.is_present_tense_clause(clause):
        tense = 'present'
        if pattern.is_past_tense_clause(clause):
            tense = 'both_tense'
    elif pattern.is_past_tense_clause(clause):
        tense = 'past'
    return tense


def classify_clause_aspect(clause, pattern: PatternNL):
    aspect = 'no_aspect'
    if pattern.is_perfect_tense_clause(clause):
        aspect = "perfect"
        if pattern.is_simple_tense_clause(clause):
            aspect = 'both_aspect'
    elif pattern.is_simple_tense_clause(clause):
        aspect = "simple"
    return aspect


def classify_book_clauses(book: book_model.BookContent, pattern: PatternNL):
    """Classify the tense and aspect of each clause in a book, keeping track of
    chunk number, sentence number and clause number."""
    book_tense_aspects = []
    for bi, book_item in enumerate(book.book_items):
        for ei, ele in enumerate(book_item.content_elements):
            if not hasattr(ele, 'parsed_text') or ele.parsed_text is None:
                continue
            trankit_doc = trankit_json_to_doc(ele.parsed_text)
            for si, sent in enumerate(trankit_doc.sentences):
                try:
                    for ci, clause in enumerate(pattern.get_verb_clauses(sent)):
                        tense = classify_clause_tense(clause, pattern)
                        aspect = classify_clause_aspect(clause, pattern)
                        row = [book.book_id, bi, ei, si, ci, tense, aspect]
                        book_tense_aspects.append(row)
                except RecursionError:
                    # print(f"RecursionError for book {book_id}, doc {di}, sent {si}: {sent}")
                    raise
    return book_tense_aspects


def get_verb_count(book_docs: List[Doc], pattern: PatternNL) -> tuple:
    """counts frequency of types of verbs from book docs"""
    all_present_tense_count = 0
    all_past_tense_count = 0
    total_verb_count = 0
    total_pv_count = 0
    present_perfect_count = 0
    no_tense_perfect_count = 0
    past_perfect_count = 0
    present_simple_count = 0
    past_simple_count = 0
    no_tense_simple_count = 0
    no_tense_no_aspect_count = 0
    both_tense_count = 0
    both_aspect_count = 0

    sentences = [sent for doc in book_docs for sent in doc.sentences]
    # print('number of sentences:', len(sentences))
    doc_clauses = []
    for sent in sentences:
        try:
            clauses = pattern.get_verb_clauses(sent)
            doc_clauses.extend(clauses)
        except RecursionError:
            continue
    # clauses = [clause for sent in sentences for clause in pattern.get_verb_clauses(sent)]
    # print('number of clauses:', len(clauses))
    clause_count = len(doc_clauses)

    for clause in doc_clauses:
        if pattern.is_perfect_tense_clause(clause):
            if pattern.is_present_perfect_clause(clause):
                present_perfect_count += 1
            elif pattern.is_past_perfect_clause(clause):
                past_perfect_count += 1
            else:
                no_tense_perfect_count += 1
        elif pattern.is_simple_tense_clause(clause):
            if pattern.is_present_simple_clause(clause):
                present_simple_count += 1
            elif pattern.is_past_simple_clause(clause):
                past_simple_count += 1
            else:
                no_tense_simple_count += 1
        else:
            no_tense_no_aspect_count += 1

        if pattern.is_present_tense_clause(clause) and pattern.is_past_tense_clause(clause):
            both_tense_count += 1
        if pattern.is_perfect_tense_clause(clause) and pattern.is_simple_tense_clause(clause):
            both_aspect_count += 1

        # present_perfect_count += pattern.is_present_perfect_clause(clause)
        # past_perfect_count += pattern.is_past_perfect_clause(clause)
        # present_simple_count += pattern.is_present_simple_clause(clause)
        # past_simple_count += pattern.is_past_simple_clause(clause)
        for token in clause.tokens:
            if token.upos == 'VERB':

                total_verb_count += 1
                if 'pv' in token.xpos:
                    total_pv_count += 1

                if 'tgw' in token.xpos:
                    all_present_tense_count += 1

                if 'verl' in token.xpos:
                    all_past_tense_count += 1

    return (total_verb_count, all_present_tense_count, all_past_tense_count,
            total_pv_count, clause_count, present_perfect_count, past_perfect_count,
            present_simple_count, past_simple_count, no_tense_simple_count, no_tense_perfect_count,
            no_tense_no_aspect_count, both_tense_count, both_aspect_count)


def get_funcword_count(book_docs: List[Doc]) -> Tuple[int, int, int]:
    """
    Get functional words count for book docs
    e.g., pronouns, proper names, determinatives etc
    """
    pron_count = 0
    propn_count = 0
    det_count = 0

    for doc in book_docs:
        for token in doc.tokens:
            if token.upos == 'PRON':
                pron_count += 1
            if token.upos == 'PROPN':
                propn_count += 1
            if token.upos == 'DET':
                det_count += 1

    return pron_count, propn_count, det_count


def get_uposword_count(book_docs: List[Doc]) -> Tuple[int, int, int, int]:
    """ counts nouns, adjectives, adverbs and intejerctions """
    noun_count = 0
    adj_count = 0
    adv_count = 0
    intj_count = 0

    for doc in book_docs:
        for token in doc.tokens:
            if token.upos == 'NOUN':
                noun_count += 1
            if token.upos == 'ADJ':
                adj_count += 1
            if token.upos == 'ADV':
                adv_count += 1
            if token.upos == 'INTJ':
                intj_count += 1

    return noun_count, adj_count, adv_count, intj_count


def get_gramword_count(book_docs: List[Doc]) -> Tuple[int, int, int]:
    """ counts conjunctions and punctuation """
    sconj_count = 0  # subordinating conjunction
    cconj_count = 0  # coordinating conjunction
    punct_count = 0  # punctuation

    for doc in book_docs:
        for token in doc.tokens:
            if token.upos == 'SCONJ':
                sconj_count += 1
            if token.upos == 'CCONJ':
                cconj_count += 1
            if token.upos == 'PUNCT':
                punct_count += 1

    return sconj_count, cconj_count, punct_count


def extract_text_features(data_dir: str, lang: str = 'nl', max_items: int = None) -> pd.DataFrame:
    """
    Extracts various text features from book docs for a list of books identified by their ISBNs.
    Features include verb counts, sentence length statistics, functional word counts, POS word counts,
    and grammar-related word counts.

    Args:
        data_dir (str): The directory where book data is stored.
        lang (str): The language of the books
        max_items (int): Optional. How many books you want to extract

    Returns:
        pd.DataFrame: dataframe that contains statistics for a book.
    """

    print("1 - load book docs")
    isbn_chunk_files = load_book_chunks(data_dir, max_items=max_items)
    print("2 - get all book stats")
    all_stats = get_all_book_stats(isbn_chunk_files, lang)
    print("3 - assign name columns")
    columns = [
        'isbn', 'total_verbs', 'all_present_verbs', 'all_past_verbs', 'pv_verbs',
        # added present perfect verbs here as 'pp_verbs'
        'num_clauses', 'pres_part_clauses', 'past_part_clauses', 'pres_simple_clauses', 'past_simple_clauses',
        'no_tense_simple_clauses', 'no_tense_perfect_clause', 'no_tense_no_aspect_clauses',
        'both_tense_clauses', 'both_aspect_clauses',
        'num_tokens', 'num_sents', 'sent_len_mean', 'sent_len_median',
        'sent_len_stdev', 'unique_tokens_count',
        'pron_count', 'propn_count', 'det_count', 'noun_count', 'adj_count', 'adv_count', 'intj_count',
        'sconj_count', 'cconj_count', 'punct_count'
    ]
    print("4 - save dataframe")
    return pd.DataFrame(all_stats, columns=columns)
