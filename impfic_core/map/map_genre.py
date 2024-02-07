import gzip
from collections import defaultdict

import ast
import pandas as pd
import numpy as np


GENRE_VOCABS = ['nur', 'thema', 'bisac', 'brinkman', 'unesco']

DTYPE = {
    'record_id': str,
    'brinkman': str,
    'unesco': str
}

NUR_MAPPINGS = {
    300: "Literary_fiction",
    301: "Literary_fiction",
    302: "Literary_fiction",
    312: "Literary_fiction",
    305: "Literary_thriller",
    313: "Suspense",
    330: "Suspense",
    331: "Suspense",
    332: "Suspense",
    339: "Suspense",
    334: "Fantasy_fiction",
    280: "Children_fiction",
    281: "Children_fiction",
    282: "Children_fiction",
    283: "Children_fiction",
    284: "Young_adult",
    285: "Young_adult",
    342: "Historical_fiction",
    343: "Romanticism",
    344: "Regional_fiction"
}

genre_order = []
for genre in NUR_MAPPINGS.values():
    if genre not in genre_order:
        genre_order.append(genre)


def read_genre_file(genre_file: str):
    dtype = {vocab: str for vocab in GENRE_VOCABS}
    genre_df = pd.read_csv(genre_file, sep='\t', compression='gzip', dtype=dtype)
    for vocab in GENRE_VOCABS:
        genre_df[vocab] = genre_df[vocab].apply(map_list)
    genre_df['nur_genre'] = genre_df.nur.apply(map_genre)
    return genre_df


def nur_genre(nur) -> str:
    if isinstance(nur, str) and nur.isdigit():
        nur = int(nur)
    if pd.isna(nur):
        return np.nan
    elif nur in NUR_MAPPINGS:
        return NUR_MAPPINGS[nur]
    elif 280 <= nur <= 350:
        return "Other fiction"
    else:
        return "Non-fiction"


def map_list(value):
    if isinstance(value, str):
        return ast.literal_eval(value)
    elif isinstance(value, list):
        return value
    if pd.isna(value):
        return value
    print(value, pd.isna(value))
    return value


def map_genre(nurs):
    if isinstance(nurs, list):
        nurs = [nur for nur in nurs if nur != '']
        for nur in NUR_MAPPINGS:
            if str(nur) in nurs:
                return NUR_MAPPINGS[nur]
        if any([280 <= int(nur) <= 350 for nur in nurs]):
            return "Other fiction"
        else:
            return "Non-fiction"
    elif pd.isna(nurs):
        return nurs
    else:
        print(nurs, type(nurs))
    return None


def make_work_genre_map():
    genre_file = '../../data/book_metadata/work_isbn_title_genre.tsv.gz'

    genre_fields = [
        'nur', 'thema', 'bisac', 'brinkman', 'unesco'
    ]

    work_genre = pd.read_csv(genre_file, sep='\t', compression='gzip', dtype=DTYPE)
    for genre_field in genre_fields:
        work_genre[genre_field] = work_genre[genre_field].apply(map_list)
    d = work_genre[['record_id', 'nur_genre']].to_dict()

    work_genre_map = {d['record_id'][i]: d['nur_genre'][i] for i in d['record_id'] if
                      pd.isna(d['nur_genre'][i]) is False}
    len(work_genre_map)
    return work_genre_map


def read_work_genre_file(work_genre_file: str, as_dataframe: bool = False):
    if as_dataframe is True:
        return pd.read_csv(work_genre_file, sep='\t', compression='gzip', dtype=DTYPE)
    else:
        return read_work_genre_file_generator(work_genre_file)


def read_work_genre_file_generator(work_genre_file: str):
    with gzip.open(work_genre_file, 'rt') as fh:
        headers = next(fh).strip().split('\t')
        for line in fh:
            row = line.strip().split('\t')
            work_info = {header: row[hi] for hi, header in enumerate(headers)}
            yield work_info
    return None


def make_typed_book_id(book_id: str, id_type: str):
    return f"{id_type}__{book_id}"


class WorkGenre:

    def __init__(self, work_genre_file: str):
        self.work_genre_file = work_genre_file
        self.work_id_has_book_id = defaultdict(set)
        self.book_id_has_work_id = {}
        self.book_id_has_type = defaultdict(set)
        self.work_id_has_genre = defaultdict(lambda: defaultdict(set))
        for work_info in read_work_genre_file(work_genre_file):
            work_id = work_info['work_id']
            self.book_id_has_type[work_info['record_id']].add(work_info['record_type'])
            book_id = make_typed_book_id(work_info['record_type'], work_info['record_id'])
            self.work_id_has_book_id[work_id].add(book_id)
            self.book_id_has_work_id[book_id] = work_id
            for vocab in GENRE_VOCABS:
                if work_info['vocab']:
                    self.work_id_has_genre[work_id][vocab].update(work_info['vocab'])

    def get_work_id(self, book_id: str, id_type: str = None):
        typed_book_id = make_typed_book_id(book_id, id_type)
        if typed_book_id not in self.book_id_has_work_id:
            return None
        else:
            return self.book_id_has_work_id[typed_book_id]

    def work_nur(self, work_id: str):
        if work_id in self.work_id_has_genre:
            return self.work_id_has_genre[work_id]['nur']
        else:
            return set()


def map_id_to_genre(row, work_genre_map):
    genres = set()
    # keep nur if review already has one
    if pd.isna(row['genre']) is False:
        # print('adding row genre:', row['genre'])
        genres.add(row['genre'])
    if row['book_id'] in work_genre_map and pd.isna(work_genre_map[row['book_id']]) is False:
        # print('adding book_id genre:', work_genre_map[row['book_id']])
        genres.add(work_genre_map[row['book_id']])
    if row['isbn'] in work_genre_map and pd.isna(work_genre_map[row['isbn']]) is False:
        # print('adding isbn genre:', work_genre_map[row['isbn']])
        genres.add(work_genre_map[row['isbn']])
    # print(genres)
    if len(genres) == 0:
        return np.nan
    elif len(genres) == 1:
        return list(genres)[0]
    for genre in genre_order:
        if genre in genres:
            return genre
    return list(genres)[0]
