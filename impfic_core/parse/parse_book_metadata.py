import copy
import json
import re
import datetime
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Set, Union


CURRENT_YEAR = datetime.date.today().year


def get_record_field_values(record: Dict[str, any], field: str) -> Dict[str, Set[str]]:
    dc_data = record['srw:recordData']['srw_dc:dc']
    values = defaultdict(set)
    if field not in dc_data:
        return values
    if isinstance(dc_data[field], dict):
        dc_data[field] = [dc_data[field]]
    try:
        for rec_id in dc_data[field]:
            values[rec_id['@xsi:type']].add(rec_id['#text'])
    except KeyError:
        print('field:', field)
        print('dc_data:', dc_data[field])
        raise
    return values


def get_record_title(record: Dict[str, any]) -> Dict[str, str]:
    dc_data = record['srw:recordData']['srw_dc:dc']
    values = {}
    if 'dc:title' not in dc_data:
        return values
    if isinstance(dc_data['dc:title'], dict):
        dc_data['dc:title'] = [dc_data['dc:title']]
    if isinstance(dc_data['dc:title'], str):
        values['dcx:maintitle'] = dc_data['dc:title']
        return values
    for rec_id in dc_data['dc:title']:
        if '@xsi:type' in rec_id and '#text' in rec_id:
            values[rec_id['@xsi:type']] = rec_id['#text']
        elif '#text' in rec_id:
            values['dcx:maintitle'] = rec_id['#text']
        else:
            print('dc_data:', dc_data['dc:title'])
            raise KeyError(f'missing #text field in dc:title\n:{json.dumps(rec_id, indent=4)}')
    return values


def get_record_identifiers(record: Dict[str, any]) -> Dict[str, Set[str]]:
    dc_data = record['srw:recordData']['srw_dc:dc']
    identifiers = defaultdict(set)
    if 'dc:identifier' not in dc_data:
        return identifiers
    if isinstance(dc_data['dc:identifier'], dict):
        dc_data['dc:identifier'] = [dc_data['dc:identifier']]
    for rec_id in dc_data['dc:identifier']:
        identifiers[rec_id['@xsi:type']].add(rec_id['#text'])
    return identifiers


def get_record_creators(record: Dict[str, any]) -> Dict[str, Set[str]]:
    dc_data = copy.deepcopy(record['srw:recordData']['srw_dc:dc'])
    creators = defaultdict(set)
    creator_types = {'dc:creator': 'aut', 'dc:contributor': 'contributor'}
    for field in creator_types:
        if field not in dc_data:
            return creators
        if isinstance(dc_data[field], list) is False:
            dc_data[field] = [dc_data[field]]
        for rec_id in dc_data[field]:
            if isinstance(rec_id, str):
                rec_id = {'#text': rec_id}
            creator_type = rec_id['@dcx:role'] if '@dcx:role' in rec_id else creator_types[field]
            try:
                creators[creator_type].add(rec_id['#text'])
            except TypeError:
                print(record['srw:recordData']['srw_dc:dc'][field])
                print(dc_data[field])
                raise
    return creators


def get_record_isbns(record: Dict[str, any]) -> List[str]:
    dc_data = record['srw:recordData']['srw_dc:dc']
    isbns = []
    if 'dc:identifier' not in dc_data:
        return isbns
    if isinstance(dc_data['dc:identifier'], dict):
        dc_data['dc:identifier'] = [dc_data['dc:identifier']]
    for rec_id in dc_data['dc:identifier']:
        if rec_id['@xsi:type'] == 'dcterms:ISBN':
            isbns.append(rec_id['#text'])
    return isbns


def get_record_publication_year(record: Dict[str, any]) -> Union[int, None]:
    if 'dc:date' not in record['srw:recordData']['srw_dc:dc']:
        return None
    else:
        date = record['srw:recordData']['srw_dc:dc']['dc:date']
        if re.match(r'^\d{4}$', date):
            year = date
        elif m := re.match(r'\[(\d{4})]', date):
            year = m.group(1)
        elif m := re.match(r'.*(\d{4})$', date):
            year = m.group(1)
        elif m := re.match(r'.*(\d{4})]$', date):
            year = m.group(1)
        elif m := re.match(r'^(\d{4})-\.\.\.$', date):
            year = m.group(1)
        else:
            return None
    if year.isdigit() and len(year) == 4:
        year = int(year)
    if 1500 <= year <= CURRENT_YEAR:
        return year
    return None


def get_record_nurs(record: Dict[str, any]) -> List[int]:
    nurs = []
    for rec_subject in record['srw:recordData']['srw_dc:dc']['dc:subject']:
        if rec_subject['@xsi:type'] == 'dcx:NUR':
            nurs.append(int(rec_subject['#text']))
    return nurs


def get_record_subjects(record: Dict[str, any]) -> Dict[str, Set[str]]:
    dc_data = record['srw:recordData']['srw_dc:dc']
    subjects = defaultdict(set)
    if 'dc:subject' not in dc_data:
        return subjects
    if isinstance(dc_data['dc:subject'], dict):
        dc_data['dc:subject'] = [dc_data['dc:subject']]
    for rec_subject in dc_data['dc:subject']:
        if '#text' not in rec_subject:
            continue
        subjects[rec_subject['@xsi:type']].add(rec_subject['#text'])
    return subjects


def get_ppn_ids(identifiers):
    if 'dcterms:URI' not in identifiers:
        return []
    return [id_uri.split('PPN:')[-1] for id_uri in identifiers['dcterms:URI'] if 'resolve?urn=PPN:' in id_uri]


def init_attr_dict() -> Dict[str, any]:
    return {
        'type': 'isbn',
        'nur': set(),
        'year': set(),
        'creator': set(),
        'author': set(),
        'title': set(),
    }


def make_isbn_node(isbn: str,
                   subjects: Dict[str, Set[str]],
                   creators: Dict[str, Set[str]],
                   title: Dict[str, str], year: Union[str, int, float]):
    node_name = f"isbn__{isbn}"
    attr_dict = init_attr_dict()
    if year:
        attr_dict['year'].add(year)
    for vocab in subjects:
        plain_vocab = vocab.split(':')[-1].lower()
        attr_dict[plain_vocab] = subjects[vocab]
    if 'dcx:maintitle' in title:
        if 'dcx:subtitle' in title:
            title = f"{title['dcx:maintitle']} -- {title['dcx:subtitle']}"
        else:
            title = title['dcx:maintitle']
        attr_dict['title'].add(title)
    if 'aut' in creators:
        for author in creators['aut']:
            attr_dict['author'].add(author)
    # if isbn in has_subject:
    #     for vocab in has_subject[isbn]:
    #         plain_vocab = vocab.split(':')[-1].lower()
    #         attr_dict[plain_vocab] = has_subject[isbn][vocab]
    return node_name, attr_dict


def add_record_nodes(work_graph, record):
    isbns = get_record_isbns(record)
    subjects = get_record_subjects(record)
    identifiers = get_record_field_values(record, 'dc:identifier')
    creators = get_record_creators(record)
    title = get_record_title(record)
    # print('title:', title)
    ppn_ids = get_ppn_ids(identifiers)
    ppn_node_names = [f"ppn__{ppn_id}" for ppn_id in ppn_ids]
    year = get_record_publication_year(record)
    for node_name in ppn_node_names:
        work_graph.add_node(node_name, **{'type': 'ppn', 'nur': set()})
    for isbn in isbns:
        isbn_node, attr_dict = make_isbn_node(isbn, subjects, creators, title, year)
        node_name = f"isbn__{isbn}"
        if node_name in work_graph.nodes:
            # print("ISBN exists, don't make a new node!")
            # print(attr_dict)
            # print(work_graph.nodes[node_name])
            # print('\n')
            for attr in attr_dict:
                if attr not in work_graph.nodes[node_name]:
                    work_graph.nodes[node_name][attr] = set()
                    for attr_value in attr_dict[attr]:
                        work_graph.nodes[node_name][attr].add(attr_value)
        else:
            work_graph.add_node(isbn_node, **attr_dict)
        for ppn_node in ppn_node_names:
            work_graph.add_edge(isbn_node, ppn_node)
    for isbn1, isbn2 in combinations(isbns, 2):
        isbn1_node = f"isbn__{isbn1}"
        isbn2_node = f"isbn__{isbn2}"
        work_graph.add_edge(isbn1_node, isbn2_node)
