from typing import Dict, Generator, List, Tuple, Union
from collections import defaultdict

import impfic_core.pattern.tag_sets_en as tag_sets


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
    if 'upos' in head_token and 'deprel' not in head_token:
        print(head_token)
    if head_token['upos'] in tag_sets.VERB_POS and 'deprel' in head_token \
            and head_token['deprel'] not in tag_sets.NON_HEAD_VERB_DEPRELS:
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
            if token['id'] in head_group and token['upos'] in tag_sets.VERB_POS \
                    and 'deprel' in token and token['deprel'] not in tag_sets.NON_HEAD_VERB_DEPRELS:
                if token not in head_verb_group[token['id']]:
                    # print('HEAD VERB:', token['id'], token['text'], token['deprel'])
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
    # xpos_fields = ['Person', 'Poss', 'PronType', 'Case']
    xpos_values = pron_token['xpos'].split('|')
    pron_info = {field: xpos_values[fi] if fi in xpos_fields else None for fi, field in enumerate(xpos_fields)}
    if pron_info['vw_type'] == 'pers':
        pron_info['genus'] = xpos_values[-1]
    for part in pron_token['feats'].split('|'):
        key, value = part.split('=')
        pron_info[key.lower()] = value.lower()
    pron_info['word'] = pron_token['text']
    pron_info['lemma'] = pron_token['lemma']
    return pron_info


def get_pronouns(sent: Dict[str, any]) -> List[Dict[str, any]]:
    pronouns = []
    for token in sent['tokens']:
        if is_person_pronoun(token):
            try:
                pron_info = get_pronoun_info(token)
            except IndexError:
                print(token)
                raise
            pronouns.append(pron_info)
    return pronouns


def get_verbs(sent: Dict[str, any]) -> List[Dict[str, any]]:
    verbs = []
    tokens = token_list_to_dict(sent)
    verb_groups = group_tokens_by_head_verb(tokens)
    for head_id in verb_groups:
        for token in verb_groups[head_id]:
            if token['upos'] in tag_sets.VERB_POS:
                verb_info = get_verb_info(token, head_id=head_id)
                verbs.append(verb_info)
    return verbs


def get_verb_info(verb_token: Dict[str, any], head_id: int) -> Dict[str, any]:
    xpos_fields = ['pt', 'w_form', 'pv_time', 'card']
    # xpos_fields = ['VerbForm', 'Number', 'Tense']
    xpos_values = verb_token['xpos'].split('|')
    verb_info = {field: xpos_values[fi] if fi in xpos_fields else None for fi, field in enumerate(xpos_fields)}
    if 'feats' in verb_token:
        for part in verb_token['feats'].split('|'):
            key, value = part.split('=')
            verb_info[key.lower()] = value.lower()
    verb_info['pos'] = verb_token['upos']
    verb_info['word'] = verb_token['text']
    verb_info['lemma'] = verb_token['lemma']
    verb_info['word_index'] = verb_token['id']
    verb_info['is_head_verb'] = verb_token['id'] == head_id
    verb_info['head_verb_id'] = head_id
    return verb_info


def is_person_pronoun(token: Dict[str, any]) -> bool:
    if token['upos'] != 'PRON':
        return False
    if 'feats' not in token:
        return False
    if 'PronType=Prs' not in token['feats']:
        return False
    return True


def prep_tokens(sent: Dict[str, any]):
    word_field = 'tokens' if 'tokens' in sent else 'words'
    return {token['id']: token for token in sent[word_field]}


def get_verb_clauses(sent: Dict[str, any]) -> List[List[Dict[str, any]]]:
    """Return all clausal units in the sentence that contain a head verb."""
    tokens = token_list_to_dict(sent)
    head_group = group_tokens_by_head_verb(tokens)
    clauses = []
    for head_id in sorted(head_group):
        clause = {
            'id': head_id,
            'tokens': sorted(head_group[head_id], key=lambda t: t['id'])
        }
        clauses.append(clause)
    return clauses


def get_verb_clusters(sent: Dict[str, any]):
    """Return all verbs per clausal unit in the sentence that contains a head verb."""
    verb_clauses = get_verb_clauses(sent)
    verb_clusters = []
    for clause in verb_clauses:
        verbs = [token for token in clause if token['upos'] in tag_sets.VERB_POS]
        if len(verbs) > 0:
            verb_clusters.append(verbs)
    return verb_clusters


def get_subject_object_verb_clusters(sent: Dict[str, any]):
    tokens = token_list_to_dict(sent)
    head_group = group_tokens_by_head_verb(tokens)
    clusters = []
    for head_id in head_group:
        cluster = {
            'subject': [token for token in head_group[head_id]
                        if 'deprel' in token and token['deprel'] in tag_sets.SUBS],
            'object': [token for token in head_group[head_id]
                       if 'deprel' in token and token['deprel'] in tag_sets.OBJS],
            'verbs': [token for token in head_group[head_id] if token['upos'] in tag_sets.VERB_POS]
        }
        if len(cluster['verbs']) > 0:
            clusters.append(cluster)
    return clusters


def token_list_to_dict(tokens: Union[List[Dict[str, any]], Dict[str, any]]) -> Dict[int, Dict[str, any]]:
    if isinstance(tokens, list):
        return {token['id']: token for token in tokens}
    elif 'tokens' in tokens:
        return {token['id']: token for token in tokens['tokens']}
    elif 'words' in tokens:
        return {token['id']: token for token in tokens['words']}
    elif isinstance(tokens, dict) and 1 in tokens:
        return tokens
    else:
        raise TypeError(f"invalid type for tokens, must be list of tokens of sentence dictionary.")


def get_pronoun_verb_pairs(sent: Dict[str, any]) -> Generator[Tuple[Dict[str, any], Dict[str, any]], None, None]:
    tokens = token_list_to_dict(sent)
    head_group = group_tokens_by_head_verb(tokens)
    for head_id in head_group:
        # print(head_id)
        # for token in sorted(head_group[head_id], key = lambda x: x['id']):
        #    print('\t', token['id'], token['text'], token['upos'], token['deprel'], token['head'])
        sub_objs = [token for token in head_group[head_id]
                    if 'deprel' in token and token['deprel'] in tag_sets.SUB_OBJS]
        verbs = [token for token in head_group[head_id] if token['upos'] in tag_sets.VERB_POS]
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
                    verb_info = get_verb_info(verb, head_id)
                except IndexError:
                    print('UNPARSEABLE VERB')
                    print(verb)
                    continue
                yield pron_info, verb_info
    return None

