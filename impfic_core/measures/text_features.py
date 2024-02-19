""" This script is generated from a Jupyter notebook and contains analysis functions
related to word usage in fiction novels.  """

import glob
import gzip
import json
import numpy as np
import os
import pandas as pd
from typing import Union
from tqdm import tqdm

def extract_text_features(data_dir: str, max_items: int = None) -> pd.DataFrame:
    """
    Extracts various text features from book chunks for a list of books identified by their ISBNs.
    Features include verb counts, sentence length statistics, functional word counts, POS word counts,
    and grammar-related word counts.

    Args:
        data_dir (str): The directory where book data is stored.
        max_items (int): Optional. How many books you want to extract

    Returns:
        pd.DataFrame: dataframe that contains statistics for a book.
    """

    # load
    def get_book_chunk_files(isbn: str, d_dir: str) -> list[str]:
        """
        Helper function to find .json.gz files for a given ISBN within a specified directory.

        Args:
            isbn (str): The ISBN of the book.
            dir (str): The directory path to search for book chunk files.

        Returns:
            List[str]: A list of paths to the book chunk files.
        """
        return glob.glob(os.path.join(d_dir, f'{isbn}/*.json.gz'))

    def load_book_chunks(data_dir: str) -> list[str]:
        """
        Loads and filters book chunks based on the presence of
        JSON.GZ files within each book's directory.

        Args:
            data_dir (str): The directory to search for book data.

        Returns:
            List[str]: A list of ISBNs for books with available data.
        """
        book_dirs = glob.glob(os.path.join(data_dir, '*'))
        isbns = [os.path.split(book_dir)[-1] for book_dir in book_dirs]
        parsed_isbns = [isbn for isbn in isbns if len(get_book_chunk_files(isbn, data_dir)) > 0]
        return parsed_isbns

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

    def read_book_chunk_files(book_chunk_files: list[str]) -> dict:
        """
        Generator function that yields the content of each book chunk file as a dictionary.

        Args:
            book_chunk_files (List[str]): A list of paths to the book chunk files.

        Yields:
            dict: The content of a book chunk file as a dictionary.
        """
        for book_chunk_file in book_chunk_files:
            yield read_book_chunk_file(book_chunk_file)

    def is_present_perfect(parsed_output: dict) -> int:
        """
        Counts the number of sentences in the parsed output that are in the present perfect tense.

        It checks for the presence of auxiliary verbs 'hebben' or 'zijn' in the present tense,
        and for main verbs in participle or infinitive forms.

        Args:
        parsed_output (dict): A dict containing parsed sentences.

        Returns:
        int: The count of sentences in the present perfect tense.
        """
        present_perf_count = 0
        for sentence in parsed_output.get('sentences', []):
            # note that we use the method `.get` to handle missing keys, and we give alternatives as `[]` or `{}` if there are any missing keys
            verbs = [token for token in sentence.get('tokens', []) if token.get('upos', '') in ['VERB', 'AUX']]

            has_aux_present = any(
                (token.get('lemma', '') == 'hebben' or token.get('lemma', '') == 'zijn') and 'Pres' in token.get(
                    'feats', {}) for token in verbs)
            has_verb_participle = any(token.get('feats', {}) and 'Part' in token.get('feats', {}) for token in verbs)
            has_verb_inf = any(token.get('feats', {}) and 'Inf' in token.get('feats', {}) for token in verbs)

            if has_aux_present and (has_verb_participle or has_verb_inf):
                present_perf_count += 1

        return present_perf_count

    def is_past_perfect(parsed_output: dict) -> int:
        """
        Counts the number of sentences in the parsed output that are in the PAST perfect tense.

        It checks for the presence of auxiliary verbs 'hebben' or 'zijn' in the present tense,
        and for main verbs in participle or infinitive forms.

        Args:
            parsed_output (dict): A dict containing parsed sentences.

        Returns:
            int: The count of sentences in the PAST perfect tense.
        """
        past_perfect_count = 0
        for sentence in parsed_output.get('sentences', []):
            verbs = [token for token in sentence.get('tokens', []) if token.get('upos', '') in ['VERB', 'AUX']]

            has_aux_past = any(
                (token.get('lemma', '') == 'hebben' or token.get('lemma', '') == 'zijn') and 'Past' in token.get(
                    'feats', {}) for token in verbs)
            has_verb_participle = any(token.get('feats', {}) and 'Part' in token.get('feats', {}) for token in verbs)
            has_verb_inf = any(token.get('feats', {}) and 'Inf' in token.get('feats', {}) for token in verbs)

            if has_aux_past and (has_verb_participle or has_verb_inf):
                past_perfect_count += 1

        return past_perfect_count

    def get_book_stats(isbn: str, data_dir: str) -> list[Union[str, int, float]]:
        """
        Gets book statistics

        Returns:
            list[str, int, float]: A list of mixed types containing the ISBN followed by
            various statistics for the book, including counts and measures of sentence
            length as integers and floats.
        """
        book_chunk_files = get_book_chunk_files(isbn, data_dir)
        book_chunks = [book_chunk for book_chunk in read_book_chunk_files(book_chunk_files)]
        total, present, past, pv, pp, pastp = get_verb_count(book_chunks)
        num_tokens, sent_len_mean, sent_len_median, sent_len_stdev, unique_tokens = get_length_stats(book_chunks)
        pron_count, propn_count, det_count = get_funcword_count(book_chunks)
        noun_count, adj_count, adv_count, intj_count = get_uposword_count(book_chunks)
        sconj_count, cconj_count, punct_count = get_gramword_count(book_chunks)
        # added present_perfect_count below as 'pp'
        stats = [isbn, total, present, past, pv, pp, pastp, num_tokens, sent_len_mean, sent_len_median, sent_len_stdev,
                 unique_tokens, pron_count, propn_count, det_count, noun_count, adj_count, adv_count, intj_count,
                 sconj_count, cconj_count, punct_count]
        return stats

    def get_all_book_stats(parsed_isbns: list[str], data_dir: str):
        """Overarching function that extracts books' stats"""
        all_stats = []
        # add progress bar
        for isbn in tqdm(parsed_isbns, desc="Processing Books"):
            book_stats = get_book_stats(isbn, data_dir)
            all_stats.append(book_stats)
        return all_stats

    def get_length_stats(book_chunks):
        """Count length of sentences in book chunks"""
        sentence_lengths = []
        num_tokens = 0
        unique_tokens = set()
        for chunk in book_chunks:
            for sentence in chunk['sentences']:
                sentence_length = len(sentence['tokens'])
                sentence_lengths.append(sentence_length)
                num_tokens += sentence_length
                unique_tokens.update(token['text'] for token in sentence['tokens'])
        unique_tokens_count = len(unique_tokens)
        sentence_lengths = np.array(sentence_lengths)
        sent_len_mean = sentence_lengths.mean()
        sent_len_median = np.median(sentence_lengths)
        sent_len_stdev = sentence_lengths.std()
        return num_tokens, sent_len_mean, sent_len_median, sent_len_stdev, unique_tokens_count

    def get_verb_count(book_chunks: list) -> tuple:
        """counts verb counts from book chunks"""
        all_present_tense_count = 0
        all_past_tense_count = 0
        total_verb_count = 0
        total_pv_count = 0
        present_perfect_count = 0
        past_perfect_count = 0

        for chunk in book_chunks:
            present_perfect_count += is_present_perfect(chunk)
            past_perfect_count += is_past_perfect(chunk)

            for sentence in chunk['sentences']:
                tokens = sentence.get('tokens')
                for token in tokens:
                    upos = token.get('upos', '')
                    xpos = token.get('xpos', '')

                    if upos == 'VERB':
                        total_verb_count += 1
                        if 'pv' in xpos:

                            total_pv_count += 1
                        if 'tgw' in xpos:

                            all_present_tense_count += 1
                        if 'verl' in xpos:

                            all_past_tense_count += 1
        return (total_verb_count, all_present_tense_count, all_past_tense_count,
                total_pv_count, present_perfect_count, past_perfect_count)

    def get_funcword_count(book_chunks):
        """
        Get functional words count for book chunks
        e.g., pronouns, proper names, determinatives etc
        """
        pron_count = 0
        propn_count = 0
        det_count = 0

        for chunk in book_chunks:
            for sentence in chunk['sentences']:
                tokens = sentence.get('tokens')
                for token in tokens:
                    upos = token.get('upos', '')

                    if upos == 'PRON':
                        pron_count += 1
                    if upos == 'PROPN':
                        propn_count += 1
                    if upos == 'DET':
                        det_count += 1

        return pron_count, propn_count, det_count

    def get_uposword_count(book_chunks):
        """ counts nouns, adjectives, adverbs and intejerctions """
        noun_count = 0
        adj_count = 0
        adv_count = 0
        intj_count = 0

        for chunk in book_chunks:
            for sentence in chunk['sentences']:
                tokens = sentence.get('tokens')
                for token in tokens:
                    upos = token.get('upos', '')

                    if upos == 'NOUN':
                        noun_count += 1
                    if upos == 'ADJ':
                        adj_count += 1
                    if upos == 'ADV':
                        adv_count += 1
                    if upos == 'INTJ':
                        intj_count += 1

        return noun_count, adj_count, adv_count, intj_count

    def get_gramword_count(book_chunks):
        """ counts conjunctions and punctuation """
        sconj_count = 0  # subordinating conjunction
        cconj_count = 0  # coordinating conjunction
        punct_count = 0  # punctuation

        for chunk in book_chunks:
            for sentence in chunk['sentences']:
                tokens = sentence.get('tokens')
                for token in tokens:
                    upos = token.get('upos', '')

                    if upos == 'SCONJ':
                        sconj_count += 1
                    if upos == 'CCONJ':
                        cconj_count += 1
                    if upos == 'PUNCT':
                        punct_count += 1

        return sconj_count, cconj_count, punct_count

    print("1 - load book chunks")
    parsed_isbns = load_book_chunks(data_dir)
    if max_items is not None:
        # subset
        parsed_isbns = parsed_isbns[:max_items]
    print("2 - get all book stats")
    all_stats = get_all_book_stats(parsed_isbns, data_dir)
    print("3 - assign name columns")
    columns = [
        'isbn', 'total_verbs', 'all_present_verbs', 'all_past_verbs', 'pv_verbs',
        # added present perfect verbs here as 'pp_verbs'
        'pp_verbs', 'pastp_verbs',
        'num_tokens', 'sent_len_mean', 'sent_len_median',
        'sent_len_stdev', 'unique_tokens_count',
        'pron_count', 'propn_count', 'det_count', 'noun_count', 'adj_count', 'adv_count', 'intj_count',
        'sconj_count', 'cconj_count', 'punct_count'
    ]
    print("4 - save dataframe")
    return pd.DataFrame(all_stats, columns=columns)