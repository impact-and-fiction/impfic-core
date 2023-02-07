import re
import gzip
import json

import hashlib

from impfic_core.secrets import salt as secret_salt

QUOTE_PATTERN = r'''(["'].*?["'])'''


USER_HASH_MAP_FILE = '../data/reviews/user_names/user_hash_map.json'
USER_ID_MAP_FILE = '../data/reviews/user_names/user_id_map.json'


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


def get_ids_and_sentences(review, review_hash_id_map, user_hash_id_map):
    """Stay well clear of this function. This should be obsolete, once we get a proper
    review database set up."""
    if 'review_id' not in review and 'review_url' in review:
        review['review_id'] = review['review_url']
    if 'user_id' in review:
        user_string = review['user_id']
    elif 'review_author_url' in review:
        user_string = review['review_author_url']
    elif 'reviewer_id' in review:
        user_string = review['reviewer_id']
    else:
        raise KeyError(f"no user id property found in review {review['review_id']}")
    if user_string not in user_hash_id_map:
        user_hash_id_map[user_string] = len(user_hash_id_map)
    if review['review_id'] not in review_hash_id_map:
        review_hash_id_map[review['review_id']] = len(review_hash_id_map)
    user_id = f"u-{user_hash_id_map[user_string]}"
    review_id = f"r-{review_hash_id_map[review['review_id']]}"
    sentences = review['sentences'] if 'sentences' in review else review['parsed_text']['sentences']
    return user_id, review_id, sentences


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
