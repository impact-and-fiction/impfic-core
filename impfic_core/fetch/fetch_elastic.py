from typing import Union

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ElasticsearchException


def scroll_hits(es: Elasticsearch, query: Union[None, dict], index: str,
                size: int = 100, scroll: str = '2m', in_bulk: bool = False) -> iter:
    if query is None or len(query.keys()) == 0:
        response = es.search(index=index, scroll=scroll, size=size)
    else:
        response = es.search(index=index, scroll=scroll, size=size, query=query)
    sid = response['_scroll_id']
    scroll_size = response['hits']['total']
    print('total hits:', scroll_size, "\thits per scroll:", len(response['hits']['hits']))
    if type(scroll_size) == dict:
        scroll_size = scroll_size['value']
    # Start scrolling
    while scroll_size > 0:
        if in_bulk:
            yield response['hits']['hits']
        else:
            for hit in response['hits']['hits']:
                yield hit
        try:
            response = es.scroll(scroll_id=sid, scroll=scroll)
        except ElasticsearchException:
            print("retrieval failed for query:")
            print(query)
            print("last successful hit:", response["hits"]["hits"][0]["_id"])
            raise
        # Update the scroll ID
        sid = response['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(response['hits']['hits'])
        # Do something with the obtained page
    # remove scroll context
    try:
        es.clear_scroll(scroll_id=sid)
    except ElasticsearchException:
        print('WARNING: no scroll id found when clearing scroll at end of scroll with query:')
        print(query)
        pass


def get_normalised_review_id(review):
    review_id = review['response_id'] if 'response_id' in review else review['responseid']
    return f"r-{review_id.replace('review_', '')}"


def get_reviews():
    gr_parse_index = 'goodreads-crawl-review-trankit-parsed'
    gr_metadata_index = 'goodreads-crawl-review-doc'
    odbr_index = 'odbr-trankit-parsed'
    es = Elasticsearch()
    for hi, hit in enumerate(scroll_hits(es, None, gr_parse_index)):
        parsed = hit['_source']
        response = es.get(index=gr_metadata_index, id=parsed['response_id'])
        review = response['_source']
        review['review_id'] = get_normalised_review_id(review)
        review['parsed_text'] = {'sentences': parsed['parsed']['sentences']}
        yield review
        if (hi+1) % 10000 == 0:
            print(hi+1, 'goodreads reviews processed')
    for hi, hit in enumerate(scroll_hits(es, None, odbr_index)):
        review = hit['_source']
        review['review_id'] = get_normalised_review_id(review)
        review['parsed_text'] = {
            review['sentences']
        }
        del review['sentences']
        yield review
        if (hi+1) % 10000 == 0:
            print(hi+1, 'odbr reviews processed')
