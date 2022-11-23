from typing import Dict, Generator, List, Tuple
from collections import defaultdict


def group_tokens_by_head(tokens: Dict[int, Dict[str, any]]) -> Dict[int, List[Dict[str, any]]]:
    """Group a list of tokens by their head tokens."""
    head_group = defaultdict(list)
    for token_id, token in tokens.items():
        head_group[token['head']].append(token)
    for head_id in head_group:
        if head_id not in tokens:
            continue
        head_token = tokens[head_id]
        head_group[head_id].append(head_token)
    return head_group


def get_head_verb_id(head_id: int, tokens: Dict[int, Dict[str, any]]) -> int:
    """Return the id of the head verb of a set of tokens for a given head id,
    or 0 if the head id is 0."""
    if head_id == 0:
        return 0
    head_token = tokens[head_id]
    if head_token['upos'] in VERB_POS and head_token['deprel'] != 'xcomp':
        return head_token['id']
    else:
        return get_head_verb_id(head_token['head'], tokens)


def group_tokens_by_head_verb(tokens: Dict[int, Dict[str, any]]) -> Dict[int, List[Dict[str, any]]]:
    """Group a list of tokens by their head verb tokens."""
    head_group = group_tokens_by_head(tokens)
    head_verb_group = defaultdict(list)
    for head_id in head_group:
        head_verb_id = get_head_verb_id(head_id, tokens)
        for token in head_group[head_id]:
            if token['id'] in head_group and token['upos'] in VERB_POS and token['deprel'] != 'xcomp':
                if token not in head_verb_group[token['id']]:
                    head_verb_group[token['id']].append(token)
            elif token not in head_verb_group[head_verb_id]:
                head_verb_group[head_verb_id].append(token)
    head_verb_group = copy_subject_across_conjunctions(head_verb_group)
    return head_verb_group


def copy_subject_across_conjunctions(head_verb_group: Dict[int, List[Dict[str, any]]]) -> Dict[int, List[Dict[str, any]]]:
    for head_id in head_verb_group:
        if head_id == 0:
            continue
        for t in head_verb_group[head_id]:
            if 'deprel' not in t:
                print('MISSING DEPREL:', t)
        subjs = [t for t in head_verb_group[head_id] if
                 'deprel' in t and t['deprel'] in {'nsubj', 'csubj', 'nsubj:pass'}]
        if len(subjs) == 0:
            head_token = [t for t in head_verb_group[head_id] if t['id'] == head_id][0]
            connected_group_id = head_token['head']
            if connected_group_id not in head_verb_group:
                continue
            connected_subjs = [t for t in head_verb_group[connected_group_id] if
                               t['deprel'] in {'nsubj', 'csubj', 'nsubj:pass'}]
            head_verb_group[head_id].extend(connected_subjs)
    return head_verb_group


def get_pronoun_info(pron_token: Dict[str, any]) -> Dict[str, any]:
    # person_fields = 'pt', 'vw_type', 'pos', 'case', 'status', 'person', 'card', 'genus'
    # seven_fields 'pt', 'vw_type', 'pos', 'case', 'status', 'person', 'card'
    # six_fields 'pt', 'vw_type', 'pos', 'case', 'position', 'inflection'
    xpos_fields = ['pt', 'vw_type', 'pos', 'case', 'status', 'person', 'card']
    xpos_values = pron_token['xpos'].split('|')
    pron_info = {field: xpos_values[fi] for fi, field in enumerate(xpos_fields)}
    if pron_info['vw_type'] == 'pers':
        pron_info['genus'] = xpos_values[-1]
    for part in pron_token['feats'].split('|'):
        key, value = part.split('=')
        pron_info[key.lower()] = value.lower()
    pron_info['word'] = pron_token['text']
    pron_info['lemma'] = pron_token['lemma']
    return pron_info


def get_verb_info(verb_token: Dict[str, any]) -> Dict[str, any]:
    xpos_fields = ['pt', 'w_form', 'pv_time', 'card']
    xpos_values = verb_token['xpos'].split('|')
    verb_info = {field: xpos_values[fi] for fi, field in enumerate(xpos_fields)}
    if 'feats' in verb_token:
        for part in verb_token['feats'].split('|'):
            key, value = part.split('=')
            verb_info[key.lower()] = value.lower()
    verb_info['word'] = verb_token['text']
    verb_info['lemma'] = verb_token['lemma']
    verb_info['verb_word_index'] = verb_token['id']
    return verb_info


def is_person_pronoun(token: Dict[str, any]) -> bool:
    if token['upos'] != 'PRON':
        return False
    if 'feats' not in token:
        return False
    if 'PronType=Prs' not in token['feats']:
        return False
    return True


def get_pronoun_verb_pairs(sent: Dict[str, any]) -> Generator[Tuple[Dict[str, any], Dict[str, any]], None, None]:
    word_field = 'tokens' if 'tokens' in sent else 'words'
    tokens = {token['id']: token for token in sent[word_field]}
    head_group = group_tokens_by_head_verb(tokens)
    for head_id in head_group:
        # print(head_id)
        # for token in sorted(head_group[head_id], key = lambda x: x['id']):
        #    print('\t', token['id'], token['text'], token['upos'], token['deprel'], token['head'])
        sub_objs = [token for token in head_group[head_id] if 'deprel' in token and token['deprel'] in SUB_OBJS]
        verbs = [token for token in head_group[head_id] if token['upos'] in VERB_POS]
        pron_sub_objs = [token for token in sub_objs if is_person_pronoun(token)]
        if len(verbs) == 0:
            continue
        for sub_obj in pron_sub_objs:
            try:
                pron_info = get_pronoun_info(sub_obj)
            except IndexError:
                continue
            for verb in verbs:
                try:
                    verb_info = get_verb_info(verb)
                except IndexError:
                    print('UNPARSEABLE VERB')
                    print(verb)
                    continue
                yield pron_info, verb_info
    return None


pos_tags = [
    'DET', 'NOUN', 'AUX', 'ADJ', 'CCONJ',
    'PUNCT', 'PRON', 'VERB', 'ADV', 'NUM',
    'SCONJ', 'ADP', 'PROPN', 'SYM', 'INTJ', 'X'
]

rel_tags = [
    'det', 'nsubj', 'cop', 'advmod', 'root', 'cc',
    'conj', 'punct', 'parataxis', 'nummod', 'obj',
    'aux', 'mark', 'case', 'nmod', 'flat', 'amod',
    'obl', 'acl:relcl', 'compound:prt', 'xcomp',
    'appos', 'advcl', 'acl', 'nmod:poss', 'expl',
    'ccomp', 'nsubj:pass', 'aux:pass', 'fixed',
    'csubj', 'iobj', 'expl:pv', 'obl:agent',
    'orphan', 'other'
]

clause_rel = {'advcl'}
VERB_POS = {'VERB', 'AUX'}
SUB_OBJS = {'nsubj', 'nsubj:pass', 'csubj', 'obj', 'iobj', 'obl:agent'}

headers = [
    'source', 'user_id', 'review_id', 'sentence_id', 'sentence_num', 'review_num_words', 'sent_num_words',
    'pron_pt', 'pron_vw_type', 'pron_pos', 'pron_case',
    'pron_status', 'pron_person', 'pron_card', 'pron_reflex',
    'pron_genus', 'pron_prontype', 'pron_word', 'pron_lemma',
    # pron_poss
    'verb_word_index',
    'verb_pt', 'verb_w_form', 'verb_pv_time', 'verb_card',
    'verb_number', 'verb_tense', 'verb_verbform', 'verb_word',
    'verb_lemma',
    # verb_foreign, verb_degree, verb_gender
]

