import gzip
import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import networkx as nx

import impfic_core.parse.parse_book_metadata as meta_parse


CRAWL_FILE = '../data/book_metadata/KB_crawl/isbn_metadata.jsonl.gz'


def read_crawl_data() -> List[Dict[str, any]]:
    with gzip.open(CRAWL_FILE, 'rt') as fh:
        for line in fh:
            yield json.loads(line.strip())


def ppn_node_uri(ppn_node: str) -> str:
    ppn = ppn_node[4:]
    return f'http://resolver.kb.nl/resolve?urn=PPN:{ppn}'


def parse_node(node: str) -> List[str]:
    return node.split('_')


def get_ppn_ids(identifiers: Dict[str, Set[str]]) -> List[str]:
    if 'dcterms:URI' not in identifiers:
        return []
    return [id_uri.split('PPN:')[-1] for id_uri in identifiers['dcterms:URI'] if 'resolve?urn=PPN:' in id_uri]


def get_goodreads_ids(work_info: Dict[str, any]) -> Set[str]:
    gr_ids = []
    for isbn_info in work_info['isbns']:
        if isbn_info['in_goodreads']:
            gr_ids.extend(isbn_info['goodreads_book_ids'])
    return set(gr_ids)


def get_work_ids(work_info: Dict[str, any]) -> Dict[str, any]:
    return {
        'work_id': work_info['work_id'],
        'isbns': set([isbn_info['isbn'] for isbn_info in work_info['isbns']]),
        'odbr_ids': set([isbn_info['odbr_book_id'] for isbn_info in work_info['isbns'] if isbn_info['in_odbr']]),
        'gr_ids': get_goodreads_ids(work_info),
    }


def get_work_nurs(work_info: Dict[str, any]) -> Set[int]:
    work_nurs = set()
    for isbn_info in work_info['isbns']:
        if isbn_info['in_kbcb'] and 'nur' in isbn_info['kbcb_info']:
            nurs = set(isbn_info['kbcb_info']['nur'])
            work_nurs = work_nurs.union(nurs)
    assert all([isinstance(nur, int) for nur in work_nurs]), "work_info contains nurs that are not integers"
    return work_nurs


class WorkMetadata:

    def __init__(self):
        self.work_graph = nx.Graph()
        self.vocabs = {'nur'}

    def add_record_nodes(self, record):
        isbns = meta_parse.get_record_isbns(record)
        subjects = meta_parse.get_record_subjects(record)
        identifiers = meta_parse.get_record_field_values(record, 'dc:identifier')
        ppn_ids = get_ppn_ids(identifiers)
        ppn_node_names = [f"ppn__{ppn_id}" for ppn_id in ppn_ids]
        for node_name in ppn_node_names:
            self.work_graph.add_node(node_name, **{'type': 'ppn'})
        for isbn in isbns:
            isbn_node, attr_dict = self.make_isbn_node(isbn, subjects)
            self.work_graph.add_node(isbn_node, **attr_dict)
            for ppn_node in ppn_node_names:
                self.work_graph.add_edge(isbn_node, ppn_node)

    def make_isbn_node(self, isbn: str, subjects: Dict[str, Set[str]]) -> Tuple[str, Dict[str, any]]:
        node_name = f"isbn__{isbn}"
        attr_dict = {'type': 'isbn', 'nur': set()}
        for vocab in subjects:
            plain_vocab = vocab.split(':')[-1].lower()
            self.vocabs.add(plain_vocab)
            attr_dict[plain_vocab] = set(sub for sub in subjects[vocab])
        return node_name, attr_dict

    def get_component_isbns(self, component):
        isbn_nodes = [node for node in component if self.work_graph.nodes[node]['type'] == 'isbn']
        return [node.split('__')[1] for node in isbn_nodes]

    def get_component_nurs(self, component):
        component_nurs = set()
        for node_name in component:
            if self.work_graph.nodes[node_name]['type'] != 'isbn':
                continue
            component_nurs = component_nurs.union(self.work_graph.nodes[node_name]['nur'])
        return component_nurs

    def add_work_links(self, work_info: Dict[str, any]):
        work_ids = get_work_ids(work_info)
        id_work = f"work__{work_ids['work_id']}"
        self.work_graph.add_node(id_work, **{'type': 'apart'})
        work_nurs = get_work_nurs(work_info)
        for isbn in work_ids['isbns']:
            id_isbn = f"isbn__{isbn}"
            attr_dict = {'type': 'isbn', 'nur': set()}
            if len(work_nurs) > 0:
                attr_dict['nur'] = attr_dict['nur'].union(work_nurs)
            self.work_graph.add_node(id_isbn, **attr_dict)
            self.work_graph.add_edge(id_work, id_isbn)
        for odbr_id in work_ids['odbr_ids']:
            id_odbr = f"odbr__{odbr_id}"
            self.work_graph.add_node(id_odbr, **{'type': 'odbr'})
            self.work_graph.add_edge(id_work, id_odbr)
        for gr_id in work_ids['gr_ids']:
            id_gr = f"goodreads__{gr_id}"
            self.work_graph.add_node(id_gr, **{'type': 'goodreads'})
            self.work_graph.add_edge(id_work, id_gr)

    def get_component_subjects(self, component):
        component_subjects = defaultdict(set)
        for node_name in component:
            if self.work_graph.nodes[node_name]['type'] != 'isbn':
                continue
            for vocab in self.vocabs:
                if vocab in self.work_graph.nodes[node_name]:
                    for subject in self.work_graph.nodes[node_name][vocab]:
                        component_subjects[vocab].add(subject)
            break
        return component_subjects
