import gzip
import json
import os
from pathlib import Path
from typing import List

import impfic_core.measures.text_features as text_features
import pandas as pd
from impfic_core.api import Pattern, PatternNL, get_lang_patterns
from impfic_core.parse import book_model
from tqdm import tqdm


def load_book(book_file: str) -> book_model.BookContent:
    with gzip.open(book_file, 'rt') as fh:
        book_json = json.load(fh)
        return book_model.BookContent.from_json(book_json)


def get_all_book_tense_aspects(book_files: List[Path], out_dir: Path, lang: str):
    """Overarching function that extracts tense aspects per clause for a list of books."""
    columns = ['book_id', 'item_num', 'element_num', 'sent_num', 'clause_num', 'tense', 'aspects']
    pattern = get_lang_patterns(lang)
    # add progress bar
    if os.path.exists(out_dir) is False:
        os.mkdir(out_dir)
    for book_file in tqdm(book_files, desc="Processing Books"):
        book = load_book(book_file)
        out_file = os.path.join(out_dir, f'tense_aspect-isbn_{book.book_id}.tsv.gz')
        if os.path.exists(out_file):
            continue
        book_tense_aspects = text_features.classify_book_clauses(book, pattern)
        df = pd.DataFrame(book_tense_aspects, columns=columns)
        df.to_csv(out_file, sep='\t', compression='gzip', index=False)
        # all_tense_aspects.extend(book_tense_aspects)
    return None


def main():
    book_dir = Path('../data/books/epub_json/kb_epubs_sample')
    output_dir = Path('../data/book_statistics/tense_aspect')
    lang = 'nl'
    book_files = list(book_dir.glob('*.gz'))
    get_all_book_tense_aspects(book_files, output_dir, lang)
    pass


if __name__ == "__main__":
    main()
