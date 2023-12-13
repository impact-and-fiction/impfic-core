import copy
import re
import datetime
from collections import defaultdict
from typing import Dict, List, Set, Union


CURRENT_YEAR = datetime.date.today().year

def get_record_field_values(record: Dict[str, any], field: str) -> Dict[str, Set[str]]:
    dc_data = record['srw:recordData']['srw_dc:dc']
    values = defaultdict(set)
    if field not in dc_data:
        return values
    if isinstance(dc_data[field], dict):
        dc_data[field] = [dc_data[field]]
    for rec_id in dc_data[field]:
            values[rec_id['@xsi:type']].add(rec_id['#text'])
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
        elif m := re.match(r'\[(\d{4})\]', date):
            year = m.group(1)
        elif m := re.match(r'.*(\d{4})$', date):
            year = m.group(1)
        elif m := re.match(r'.*(\d{4})\]$', date):
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
