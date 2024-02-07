import gzip
import json
import os
import re
from typing import Dict, Tuple, Union

from impfic_core.parse.doc import Doc, json_to_doc


def parse_chunk_file(chunk_file: str) -> Doc:
    chunk_json = read_chunk_file(chunk_file)
    return json_to_doc(chunk_json)


def read_chunk_file(chunk_file: str) -> Dict[str, any]:
    """Read a parsed chunk of book text from file and return as a Doc instance."""
    if chunk_file.endswith('.gz'):
        with gzip.open(chunk_file, 'rt') as fh:
            chunk_json = json.load(fh)
    elif chunk_file.endswith('.docbin'):
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
