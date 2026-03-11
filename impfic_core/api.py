import gzip
import json
from pathlib import Path
from typing import Callable, Union

import impfic_core.parse.parse_trankit_sentence as parse_trankit_sentence
import impfic_core.pattern.tag_sets_en as tag_sets_en
import impfic_core.pattern.tag_sets_nl as tag_sets_nl
from impfic_core.pattern.patterns import Pattern
from impfic_core.pattern.patterns_nl import PatternNL
from impfic_core.parse import book_model
from impfic_core.parse.doc import json_to_doc
from impfic_core.parse.doc import Clause, Doc, Sentence, Token
from impfic_core.parse.chunk import read_chunk_file


def load_book(book_file: Union[str, Path]) -> book_model.BookContent:
    open_func = gzip.open if str(book_file).endswith('.gz') else open
    with open_func(book_file, 'rt') as fh:
        book_json = json.load(fh)
        return book_model.BookContent.from_json(book_json)


def get_book_tokens(book_content: Union[book_model.BookContent, book_model.BookItem], tokenizer: Callable=None):
    """

    :param book_content: a BookContent or BookItem from the impfic_core.parse.book_model module
    :param tokenizer: a tokenizer function that takes a string and returns a list of tokens
    :return: a list of tokens
    """
    tokens = []
    if isinstance(book_content, book_model.BookContent) or isinstance(book_content, book_model.BookItem):
        content_elements = book_content.content_elements
    elif isinstance(book_content, book_model.TextElement):
        content_elements = [book_content]
    else:
        content_elements = []
    for ele in content_elements:
        if ele.parsed_text is not None:
            ele_tokens = [token for sent in ele.parsed_text['sentences'] for token in sent['tokens']]
        elif ele.text is not None:
            ele_tokens = tokenizer(ele.text)
        else:
            continue
        tokens.extend(ele_tokens)
    return tokens




def get_lang_patterns(lang: str, tag_set_name: str = None):
    """Create a language-specific pattern instance.

    Arguments:
        lang (str): a language code, e.g. 'en' (English) or 'nl' (Dutch)

    Returns:
        pattern (Pattern): a language-specific pattern object

    The tag_set_name argument is for future implementation, e.g.
    allowing for different tag sets per language.
    """
    if lang == 'en':
        return Pattern(lang)
    elif lang == 'nl':
        return PatternNL()


def get_lang_tag_set(lang: str):
    if lang == 'en':
        return tag_sets_en
    if lang == 'nl':
        return tag_sets_nl


__all__ = [
    'Pattern', 'PatternNL', 'Doc', 'Clause', 'Sentence', 'Token',
    'json_to_doc', 'parse_trankit_sentence', 'read_chunk_file'
]
