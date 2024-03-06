from impfic_core.pattern.patterns import Pattern
from impfic_core.pattern.patterns_nl import PatternNL
import impfic_core.pattern.tag_sets_en as tag_sets_en
import impfic_core.pattern.tag_sets_nl as tag_sets_nl
from impfic_core.parse.doc import json_to_doc
from impfic_core.parse.doc import Clause, Doc, Sentence, Token
from impfic_core.parse.chunk import read_chunk_file
import impfic_core.parse.parse_trankit_sentence as parse_trankit_sentence


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
