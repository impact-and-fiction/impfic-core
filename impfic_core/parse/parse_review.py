import gzip
import json
import os
import re
from collections import defaultdict

import ast
import hashlib

from impfic_core.secrets import salt as secret_salt

QUOTE_PATTERN = r'''(["'].*?["'])'''


USER_HASH_MAP_FILE = '../../data/mappings/user_names/user_hash_map.json'
USER_ID_MAP_FILE = '../../data/mappings/user_names/user_id_map.json'
REVIEW_ID_MAP_FILE = '../../data/mappings/review_ids/review_id_map.json'
WORK_ID_MAP_FILE = '../../data/book_metadata/work_isbn_genre.tsv.gz'


def read_work_isbn_genre(genre_file: str):
    with gzip.open(genre_file, 'rt') as fh:
        headers = next(fh).strip('\n').split('\t')
        for line in fh:
            row = line.strip('\n').split('\t')
            if len(row) != len(headers):
                print(len(headers), headers)
                print(len(row), row)
            row_json = {header: row[hi] for hi, header in enumerate(headers)}
            yield row_json
    return None


def read_work_id_map(work_id_map_file: str = None):
    if work_id_map_file is None:
        work_id_map_file = WORK_ID_MAP_FILE
    book_has_work_id = {}
    work_has_book_id = defaultdict(dict)
    work_has_genre = defaultdict(lambda: defaultdict(set))

    genre_fields = [
        'nur', 'thema', 'bisac', 'brinkman', 'unesco'
    ]

    for work_isbn_genre in read_work_isbn_genre(work_id_map_file):
        book_id = work_isbn_genre['record_id']
        book_id_type = work_isbn_genre['record_id_type']
        work_id = work_isbn_genre['work_id']
        book_has_work_id[f"{book_id_type}__{book_id}"] = work_id
        work_has_book_id[work_id][book_id] = book_id_type
        for vocab in genre_fields:
            if work_isbn_genre[vocab] == '':
                genres = []
            else:
                genres = ast.literal_eval(work_isbn_genre[vocab])
            for genre in genres:
                work_has_genre[work_id][vocab].add(genre)
    return book_has_work_id, work_has_book_id, work_has_genre


def write_user_maps(user_hash_map, user_id_map, user_hash_map_file: str = None,
                    user_id_map_file: str = None):
    if user_hash_map_file is None:
        user_hash_map_file = USER_HASH_MAP_FILE
    if user_id_map_file is None:
        user_id_map_file = USER_ID_MAP_FILE
    with open(user_hash_map_file, 'wt') as fh:
        json.dump(user_hash_map, fh)

    with open(user_id_map_file, 'wt') as fh:
        json.dump(user_id_map, fh)


def write_review_id_map(review_id_map, review_id_map_file: str = None):
    if review_id_map_file is None:
        review_id_map_file = REVIEW_ID_MAP_FILE
    with open(review_id_map_file, 'wt') as fh:
        json.dump(review_id_map, fh)


def write_user_id_map(user_id_map, user_id_map_file: str = None):
    if user_id_map_file is None:
        user_id_map_file = USER_ID_MAP_FILE
    with open(user_id_map_file, 'wt') as fh:
        json.dump(user_id_map, fh)


def read_review_id_map(review_id_map_file: str = None):
    if review_id_map_file is None:
        review_id_map_file = REVIEW_ID_MAP_FILE
    if os.path.exists(review_id_map_file):
        with open(review_id_map_file, 'rt') as fh:
            review_id_map = json.load(fh)
    else:
        review_id_map = {}
    return review_id_map


def read_user_id_map(user_id_map_file: str = None):
    if user_id_map_file is None:
        user_id_map_file = USER_ID_MAP_FILE
    with open(user_id_map_file, 'rt') as fh:
        user_id_map = json.load(fh)
    return user_id_map


def read_user_maps(user_hash_map_file: str = None, user_id_map_file: str = None):
    if user_hash_map_file is None:
        user_hash_map_file = USER_HASH_MAP_FILE
    if user_id_map_file is None:
        user_id_map_file = USER_ID_MAP_FILE
    with open(user_hash_map_file, 'rt') as fh:
        user_hash_map = json.load(fh)

    with open(user_id_map_file, 'rt') as fh:
        user_id_map = json.load(fh)
    return user_hash_map, user_id_map


def hash_reviewer_id(reviewer_id: str, collection_id: str = None,
                     collection_prefix: str = '__', salt: str = None):
    if salt is None:
        salt = secret_salt
    if isinstance(reviewer_id, str) is False:
        return reviewer_id
    reviewer_string = str(reviewer_id)
    if collection_id is not None:
        reviewer_string = f"{reviewer_string}{collection_prefix}{collection_id}"
    try:
        return hashlib.sha512(reviewer_string.encode() + salt.encode()).hexdigest()
    except AttributeError:
        print(f'reviewer_id #{reviewer_id}#')
        print(f'reviewer_string #{reviewer_string}#')
    raise


def get_sentences(review):
    return review['sentences'] if 'sentences' in review else review['parsed_text']['sentences']


def get_user_id(review, user_id_map, add_unseen: bool = False):
    if 'user_id' in review:
        user_string = review['user_id']
    elif 'review_author_url' in review:
        user_string = review['review_author_url']
    elif 'reviewer_id' in review:
        user_string = review['reviewer_id']
    else:
        raise KeyError(f"no user id property found in review {review['review_id']}")
    if user_string.startswith('impfic-user-'):
        return user_string
    elif user_string.startswith('impfic-'):
        raise ValueError(f'Non-user_id found as impfic user_id: {user_string}')
    if user_string not in user_id_map:
        if add_unseen is True:
            user_id_map[user_string] = f"impfic-user-{len(user_id_map) + 1}"
        else:
            return None
    return user_id_map[user_string]


def get_review_id(review, review_id_map, add_unseen: bool = False):
    if 'review_id' in review:
        review_string = review['review_id']
    elif 'reviewid' in review:
        review_string = review['reviewid']
    elif 'review_url' in review:
        review_string = review['review_url']
    else:
        print(review)
        raise KeyError(f"no review id property found in review.")
    if review_string.startswith('impfic-review-'):
        return review['review_id']
    elif review_string.startswith('impfic-'):
        raise ValueError(f'Non-review_id found as impfic review_id: {review_string}')
    if review_string not in review_id_map:
        if add_unseen is True:
            review_id_map[review_string] = f"impfic-review-{len(review_id_map) + 1}"
        else:
            print(f'review_string {review_string} not in review_id_map')
            return None
    return review_id_map[review_string]


def get_book_work_id(review, book_has_work_id):
    book_ids = []
    book_id = None
    if 'work_id' in review and review['work_id'].startswith('impfic-work-'):
        return review['work_id']
    elif 'work_id' in review and review['work_id'].startswith('impfic-'):
        raise ValueError(f"Non-review_id found as impfic review_id: {review['work_id']}")
    if 'bookid' in review:
        book_id = f"odbr__{str(review['bookid'])}"
    elif 'odbr_book_id' in review:
        book_id = f"odbr__{str(review['odbr_book_id'])}"
    elif 'goodreads_book_id' in review:
        book_id = f"goodreads__{str(review['goodreads_book_id'])}"
    elif 'book_id' in review and 'source' in review and review['source'] == 'goodreads':
        book_id = f"goodreads__{str(review['book_id'])}"
    elif 'book_id' in review:
        book_id = f"bvr__{str(review['book_id'])}"
    elif 'isbn' in review:
        book_id = f"isbn__{str(review['isbn'])}"
    if book_id in book_has_work_id:
        return book_has_work_id[book_id]
    else:
        print('unknown book id:', book_id, type(book_id))
        if 'review_id' in review:
            print('review', review['review_id'])
        raise KeyError(f'no work_id for book_id {book_id}')


def get_ids(review, review_id_map, user_id_map, book_has_work_id):
    """Stay well clear of this function. This should be obsolete, once we get a proper
    review database set up."""
    user_id = get_user_id(review, user_id_map)
    review_id = get_review_id(review, review_id_map)
    work_id = get_book_work_id(review, book_has_work_id)
    return user_id, review_id, work_id


def normalise_hebban_review_url(url):
    if isinstance(url, str) is False:
        return url
    if 'hebban.nl/' not in url:
        return url
    url = url.replace('/main', '')
    return url.replace('/recensies/', '/recensie/')


def get_doc_sentences(doc):
    if isinstance(doc, list):
        return doc
    elif 'sentences' in doc:
        return doc['sentences']
    else:
        return [doc]


def get_num_words(doc):
    num_words = 0
    for sent in get_doc_sentences(doc):
        num_words += len([t for t in sent['tokens'] if t['upos'] != 'PUNCT'])
    return num_words


def get_num_terms(doc):
    num_terms = 0
    for sent in get_doc_sentences(doc):
        num_terms += len([t for t in sent['tokens']])
    return num_terms


def read_jsonl_reviews(review_file):
    nbd_review_num = 0
    with gzip.open(review_file['file'], 'rt') as fh:
        for line in fh:
            review = json.loads(line.strip())
            if 'source' not in review:
                review['source'] = review_file['source']
            if review['source'] == 'nbd_biblion':
                nbd_review_num += 1
                review['review_id'] = f'nbd_r-{nbd_review_num}'
            yield review


def has_quote(review):
    review_text = review["text"] if "text" in review else review["review_text"]
    for match in re.finditer(QUOTE_PATTERN, review_text):
        if len(match.group(1)) > 40:
            return True
    else:
        return False


def split_on_quotes(review):
    quotes = []
    review_text = review["text"] if "text" in review else review["review_text"]
    for match in re.finditer(QUOTE_PATTERN, review_text):
        if len(match.group(1)) > 40:
            quote_string = match.group(1)
            quote_offset = match.start()
            quotes.append({"offset": quote_offset, "end": quote_offset + len(match.group(1)), "text": match.group(1),
                           "is_quote": True})
        # else:
        #    print(match.start(), match.group(1))
    review["split_text"] = []
    full_text = review_text
    for quote in quotes[::-1]:
        # print(quote["offset"])
        postfix_offset = quote["offset"] + len(quote["text"])
        postfix_text = full_text[postfix_offset:]
        review["split_text"].append(
            {"offset": postfix_offset, "end": postfix_offset + len(postfix_text), "text": postfix_text,
             "is_quote": False})
        review["split_text"].append(quote)
        review_text = review_text[:quote["offset"]]
    # If the review doesn't start with a quote, add the first part to the list
    if len(review_text) > 0:
        review["split_text"].append({"offset": 0, "end": len(review_text), "text": review_text, "is_quote": False})
    review["split_text"].sort(key=lambda x: x["offset"])
    return review


