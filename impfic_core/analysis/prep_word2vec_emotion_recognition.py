import glob
import gzip
import os
import re
from collections import defaultdict

from tqdm import tqdm

from impfic_core.parse.chunk import read_chunk_file
from impfic_core.parse.doc import trankit_json_to_doc
from impfic_core.parse.doc import Token
from impfic_core.pattern.patterns_nl import PatternNL


def chunk_file_to_token_string(chunk_file: str, pattern: PatternNL, use_lemma: bool = False):
    chunk_json = read_chunk_file(chunk_file)
    doc = trankit_json_to_doc(chunk_json)
    tokens = [clean_token(token, use_lemma=use_lemma) for token in doc.tokens if select_token(token, pattern)]
    return ' '.join(tokens)


def generate_output_fpath(input_fpath: str, output_dir: str) -> str:
    input_fdir, fname = os.path.split(input_fpath)
    match = re.match(r"(.*)-\d+$", fname.replace('.json.gz', ''))
    fbase = match.group(1)
    return os.path.join(output_dir, f"{fbase}-tokens.txt.gz")


def select_token(token: Token, pattern: PatternNL) -> bool:
    select = True
    if pattern.is_punct(token):
        select = False
    if token.ner.endswith('-PER'):
        select = False
    return select


def clean_token(token: Token, use_lemma: bool = False) -> str:
    token_rep = token.lemma if use_lemma is True else token.text
    return token_rep.replace('_', '').lower()


def main():
    input_dir = '../data/books/txts_trankit_parsed/'
    output_dir = '../data/books/novels_tokens'

    if os.path.exists(output_dir) is False:
        os.mkdir(output_dir)

    input_fpaths = glob.glob(os.path.join(input_dir, '**/*.gz'))

    pattern = PatternNL()

    use_lemma = False
    input_output_map = defaultdict(list)

    for input_fpath in input_fpaths:
        output_fpath = generate_output_fpath(input_fpath, output_dir)
        input_output_map[output_fpath].append(input_fpath)

    for output_fpath in tqdm(input_output_map, desc='writing tokens to plain text file'):
        with gzip.open(output_fpath, 'wt') as fh_out:
            for input_fpath in input_output_map[output_fpath]:
                token_string = chunk_file_to_token_string(input_fpath, pattern, use_lemma=use_lemma)
                fh_out.write(f"{token_string}\n")


if __name__ == "__main__":
    main()
