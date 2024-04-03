from typing import Dict, Generator, List, Tuple, Union
from collections import defaultdict
from string import punctuation

from impfic_core.parse.doc import Clause, Sentence, Token
import impfic_core.pattern.tag_sets as tag_sets


def sequence_to_list(sequence: Union[Sentence, Clause, List[Token]]):
    return sequence if isinstance(sequence, list) else sequence.tokens


class Pattern:

    def __init__(self, lang: str):
        self.lang = lang
        if lang not in tag_sets.lang_tag_sets:
            raise KeyError(f'unknown language code "{lang}"')
        self.tag_sets = tag_sets.lang_tag_sets[lang]

    #######################
    # Token-level methods #
    #######################

    def is_punct(self, token: Token) -> bool:
        return token.text in punctuation or all([char in punctuation for char in token.text])

    def is_subject(self, token: Token) -> bool:
        return token.deprel in self.tag_sets.SUBS

    def is_object(self, token: Token) -> bool:
        return token.deprel in self.tag_sets.OBJS

    def is_verb(self, token: Token) -> bool:
        return token.upos in self.tag_sets.VERB_POS

    def is_head_verb(self, token: Token) -> bool:
        """Determine whether a verb is the head of a clause."""
        return self.is_verb(token) and token.deprel not in self.tag_sets.NON_HEAD_VERB_DEPRELS

    def is_person_pronoun(self, token: Token) -> bool:
        """Language specific."""
        return False

    @staticmethod
    def is_past_tense(token: Token) -> bool:
        """Language specific."""
        return False

    @staticmethod
    def is_present_tense(token: Token) -> bool:
        """Language specific."""
        return False

    @staticmethod
    def is_perfect_aux(token: Token) -> bool:
        """Language specific."""
        return False

    def is_past_perfect_aux(self, token: Token) -> bool:
        """Language specific."""
        return False

    def is_present_perfect_aux(self, token: Token) -> bool:
        """Language specific."""
        return False

    @staticmethod
    def is_infinitive_verb(token: Token) -> bool:
        """Language specific."""
        return False

    @staticmethod
    def is_participle_verb(token: Token) -> bool:
        """Language specific."""
        return False

    ##########################
    # Sequence-level methods #
    ##########################

    def get_verbs(self, sequence: Union[Sentence, Clause, List[Token]]) -> List[Token]:
        return [token for token in sequence_to_list(sequence) if self.is_verb(token)]

    @staticmethod
    def get_aux_verbs(sequence: Union[Sentence, Clause, List[Token]]) -> List[Token]:
        return [token for token in sequence_to_list(sequence) if token.upos == 'AUX']

    def get_perfect_aux_verbs(self, sequence: Union[Sentence, Clause, List[Token]]) -> List[Token]:
        return [token for token in sequence_to_list(sequence) if self.is_perfect_aux(token)]

    def get_inf_verbs(self, sequence: Union[Sentence, Clause, List[Token]]) -> List[Token]:
        return [token for token in sequence_to_list(sequence) if self.is_infinitive_verb(token)]

    def get_participle_verbs(self, sequence: Union[Sentence, Clause, List[Token]]) -> List[Token]:
        return [token for token in sequence_to_list(sequence) if self.is_participle_verb(token)]

    @staticmethod
    def get_pronouns(sequence: Union[Sentence, Clause, List[Token]]) -> List[Token]:
        return [token for token in sequence_to_list(sequence) if token.upos == 'PRON']

    def has_aux_past(self, sequence: Union[Sentence, Clause, List[Token]]):
        if any(self.is_past_tense(token) for token in sequence) is True:
            return any(self.is_perfect_aux(token) for token in sequence)
        else:
            return False

    def has_aux_present(self, sequence: Union[Sentence, Clause, List[Token]]):
        if any(self.is_present_tense(token) for token in sequence) is True:
            return any(self.is_perfect_aux(token) for token in sequence)
        else:
            return False

    def is_perfect_tense_clause(self, clause: Clause):
        """Language specific."""
        return False

    def is_simple_tense_clause(self, clause: Clause):
        """Language specific."""
        return False

    def is_past_perfect_clause(self, clause: Clause):
        """Language specific."""
        return False

    def is_present_perfect_clause(self, clause: Clause):
        """Language specific."""
        return False

    def is_past_simple_clause(self, clause: Clause):
        """Language specific."""
        return False

    def is_present_simple_clause(self, clause: Clause):
        """Language specific."""
        return False

    ####################
    # Grouping methods #
    ####################

    @staticmethod
    def group_tokens_by_head(tokens: List[Token], debug: int = 0) -> Dict[int, List[Token]]:
        """Group a list of tokens by their head tokens."""
        head_group = defaultdict(list)
        if len(tokens) == 0:
            if debug > 1:
                print('Pattern.group_tokens_by_head - no tokens, returning no groups')
            return head_group
        for token in tokens:
            head_group[token.head].append(token)
        for head_id in head_group:
            if head_id != -1:
                head_token = tokens[head_id]
                head_group[head_id].append(head_token)
        return head_group

    def get_head_verb_id(self, head_id: int, tokens: List[Token]) -> int:
        """Return the id of the head verb of a set of tokens for a given head id,
        or -1 if the head id is -1 (the root node)."""
        if head_id == -1:
            return -1
        # print(f'patterns.get_head_ver_id - head_id: {head_id}')
        head_token = tokens[head_id]
        # print(f'patterns.get_head_ver_id - head_token: {head_token}')
        # print('patterns.get_head_ver_id - is_head_verb:', self.is_head_verb(head_token))
        if self.is_head_verb(head_token):
            # print('\thead_token is head_verb')
            return head_id
        elif head_token.id == head_id and self.is_verb(head_token):
            # print('\ttoken head is token id AND thead_token is verb')
            return head_id
        # elif head_token.id == head_id and not self.is_verb(head_token):
        #     print('\ttoken head is token id AND thead_token is not a verb')
        #     return -1
        else:
            # print('\trecursing to head of head_token')
            return self.get_head_verb_id(head_token.head, tokens)

    def group_tokens_by_head_verb(self, tokens: List[Token],
                                  copy_conj_subject: bool = False,
                                  debug: int = 0) -> Dict[int, List[Token]]:
        """Group a list of tokens by their head verb tokens."""
        head_group = self.group_tokens_by_head(tokens)
        head_verb_group = defaultdict(list)
        if len(tokens) == 0:
            return head_verb_group
        for head_id in head_group:
            if debug > 0:
                print(f'Pattern.group_tokens_by_head_verb - 1 - head_id: {head_id}')
            if head_id > len(tokens):
                print('Pattern.group_tokens_by_head_verb - head_id larger than number of tokens:')
                print('Pattern.group_tokens_by_head_verb - head_id:', head_id)
                print('Pattern.group_tokens_by_head_verb - tokens:', tokens)
            head_verb_id = self.get_head_verb_id(head_id, tokens)
            if debug > 0:
                print(f'Pattern.roup_tokens_by_head_verb - 2 - head_verb_id: {head_verb_id}\n\n')
            # if head_verb_id == -1:
                # list of tokens has no verb
            #     continue
            for token in head_group[head_id]:
                if debug > 0:
                    print(f'Pattern.group_tokens_by_head_verb - 3 - head_id: {head_id}\thead_verb_id: {head_verb_id}'
                          f'\ttoken:', token.text, token.id, token.head)
                    print('\t\ttoken (upos, deprel):', (token.upos, token.deprel))
                    print('\t\ttoken.id in head_group:', token.id in head_group)
                    print('\t\ttoken.id is_head_verb:', self.is_head_verb(token))
                if token.id in head_group and self.is_head_verb(token):
                    if token not in head_verb_group[token.id]:
                        if debug > 0:
                            print('Pattern.group_token_by_head_verb - HEAD VERB:', token.id, token.text, token.deprel)
                        head_verb_group[token.id].append(token)
                elif token not in head_verb_group[head_verb_id]:
                    head_verb_group[head_verb_id].append(token)
                    if debug > 0:
                        print(f'\tadding token: {token.id} {token.text} to head_verb_id {head_verb_id}')
                else:
                    if debug > 0:
                        print('\tskipping token:', token)
                    pass
            if debug > 1:
                for head_verb_id in sorted(head_verb_group):
                    print('\n\t---------------------\n')
                    print('\tcontent of head_verb_group with head_verb_id:', head_verb_id)
                    for token in sorted(head_verb_group[head_verb_id], key=lambda t: t.id):
                        print('\t', token.id, token.text)
                    print('\n---------------------\n')
        if copy_conj_subject is True:
            head_verb_group = self.copy_subject_across_conjunctions(head_verb_group)
        for head_verb_id in head_verb_group:
            head_verb_group[head_verb_id].sort(key=lambda t: t.id)
        head_verb_group = self.merge_verb_groups(head_verb_group)
        return head_verb_group

    @staticmethod
    def merge_verb_groups(head_verb_group: Dict[int, List[Token]]):
        merge_into = {}
        for head_verb_id in head_verb_group:
            for other_head_verb_id in head_verb_group:
                if head_verb_id == other_head_verb_id:
                    continue
                if head_verb_id in [token.id for token in head_verb_group[other_head_verb_id]]:
                    if other_head_verb_id in merge_into:
                        merge_into[head_verb_id] = merge_into[other_head_verb_id]
                    else:
                        merge_into[head_verb_id] = other_head_verb_id
        for head_verb_id in merge_into:
            new_head_verb_id = merge_into[head_verb_id]
            merge_tokens = [token for token in head_verb_group[head_verb_id]
                            if token not in head_verb_group[new_head_verb_id]]
            head_verb_group[new_head_verb_id].extend(merge_tokens)
            del head_verb_group[head_verb_id]
        return head_verb_group

    def copy_subject_across_conjunctions(self, head_verb_group: Dict[int, List[Token]]) -> Dict[int, List[Token]]:
        for head_id in head_verb_group:
            if head_id == -1:
                continue
            for t in head_verb_group[head_id]:
                if t.deprel is None:
                    print('MISSING DEPREL:', t)
            subjs = [token for token in head_verb_group[head_id] if self.is_subject(token)]
            if len(subjs) == 0:
                # print('\n-------------------')
                # print('NO SUBJECTS')
                head_token = [token for token in head_verb_group[head_id] if token.id == head_id][0]
                if head_token.deprel != 'conj':
                    # print('-------------------\n')
                    continue
                # print(f'\thead_token: {head_token}')
                connected_group_id = head_token.head
                # print(f'\tconnected_group_id: {connected_group_id}')
                if connected_group_id not in head_verb_group:
                    continue
                connected_subjs = [token for token in head_verb_group[connected_group_id] if self.is_subject(token)]
                # print(f'\tconnected_subjs: {connected_subjs}')
                head_verb_group[head_id].extend(connected_subjs)
                # print('-------------------\n')
        return head_verb_group

    def get_verb_clauses(self, sent: Sentence, copy_conj_subject: bool = False) -> List[Clause]:
        """Return all clausal units in the sentence that contain a head verb."""
        head_group = self.group_tokens_by_head_verb(sent.tokens, copy_conj_subject=copy_conj_subject)
        clauses = []
        for head_id in sorted(head_group):
            clause = Clause(head_id, sorted(head_group[head_id], key=lambda t: t.id))
            clauses.append(clause)
        return clauses

    def get_verb_clusters(self, sent: Sentence, copy_conj_subject: bool = False) -> List[List[Token]]:
        """Return all verbs per clausal unit in the sentence that contains a head verb."""
        verb_clauses = self.get_verb_clauses(sent, copy_conj_subject=copy_conj_subject)
        verb_clusters = []
        for clause in verb_clauses:
            verbs = [token for token in clause.tokens if self.is_verb(token)]
            if len(verbs) > 0:
                verb_clusters.append(verbs)
        return verb_clusters

    def get_subject_object_verb_clusters(self, sent: Sentence):
        tokens = sent.tokens
        head_group = self.group_tokens_by_head_verb(tokens)
        clusters = []
        for head_id in head_group:
            cluster = {
                'subject': [token for token in head_group[head_id] if self.is_subject(token)],
                'object': [token for token in head_group[head_id] if self.is_object(token)],
                'verbs': [token for token in head_group[head_id] if self.is_verb(token)]
            }
            if len(cluster['verbs']) > 0:
                clusters.append(cluster)
        return clusters

    def get_pronoun_verb_pairs(self, sent: Sentence) -> Generator[Tuple[Dict[str, any], Dict[str, any]], None, None]:
        head_group = self.group_tokens_by_head_verb(sent.tokens)
        for head_id in head_group:
            # print(head_id)
            # for token in sorted(head_group[head_id], key = lambda x: x['id']):
            #    print('\t', token['id'], token['text'], token['upos'], token['deprel'], token['head'])
            sub_objs = [token for token in head_group[head_id] if self.is_subject(token) or self.is_object(token)]
            verbs = [token for token in head_group[head_id] if self.is_verb(token)]
            pron_sub_objs = [token for token in sub_objs if self.is_person_pronoun(token)]
            if len(verbs) == 0:
                continue
            for pron in pron_sub_objs:
                for verb in verbs:
                    yield pron, verb
        return None
