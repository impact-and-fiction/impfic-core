from collections import defaultdict
from typing import Dict, List, Union

from impfic_core.parse.doc import Clause, Sentence, Token
from impfic_core.pattern.patterns import Pattern


def sequence_to_list(sequence: Union[Sentence, Clause, List[Token]]):
    return sequence if isinstance(sequence, list) else sequence.tokens


class PatternNL(Pattern):

    def __init__(self):
        super().__init__('nl')

    #######################
    # Token-level methods #
    #######################

    def is_person_pronoun(self, token: Token) -> bool:
        if token.upos != 'PRON':
            return False
        if token.feats is None:
            return False
        if 'PronType' not in token.feats:
            return False
        return token.feats['PronType'] == 'Prs'

    @staticmethod
    def is_past_tense(token: Token) -> bool:
        return 'Tense' in token.feats and token.feats['Tense'] == 'Past'

    @staticmethod
    def is_present_tense(token: Token) -> bool:
        return 'Tense' in token.feats and token.feats['Tense'] == 'Pres'

    @staticmethod
    def is_perfect_aux(token: Token) -> bool:
        return token.lemma in {'hebben', 'zijn'} and token.upos == 'AUX'

    def is_past_perfect_aux(self, token: Token) -> bool:
        return self.is_perfect_aux(token) and self.is_past_tense(token)

    def is_present_perfect_aux(self, token: Token) -> bool:
        return self.is_perfect_aux(token) and self.is_present_tense(token)

    @staticmethod
    def is_finite_verb(token: Token) -> bool:
        return token.upos in {'VERB', 'AUX'} and 'VerbForm' in token.feats and token.feats['VerbForm'] == 'Fin'

    @staticmethod
    def is_infinitive_verb(token: Token) -> bool:
        return token.upos in {'VERB', 'AUX'} and 'VerbForm' in token.feats and token.feats['VerbForm'] == 'Inf'

    @staticmethod
    def is_participle_verb(token: Token) -> bool:
        return token.upos == 'VERB' and 'VerbForm' in token.feats and token.feats['VerbForm'] == 'Part' and \
               'vd' in token.xpos_dict and 'vrij' in token.xpos_dict

    def _has_aux_perfect(self, verbs: List[Token]) -> bool:
        return any(self.is_perfect_aux(token) for token in verbs)

    def _has_verb_participle(self, verbs: List[Token]) -> bool:
        return any(self.is_participle_verb(token) for token in verbs)

    def _has_verb_inf(self, verbs: List[Token]) -> bool:
        return any(self.is_infinitive_verb(token) for token in verbs)

    def _has_verb_finite(self, verbs: List[Token]) -> bool:
        return any(self.is_finite_verb(token) for token in verbs)

    def is_present_tense_clause(self, clause: Clause):
        return any(self.is_present_tense(token) for token in clause)

    def is_past_tense_clause(self, clause: Clause):
        return any(self.is_past_tense(token) for token in clause)

    def is_perfect_tense_clause(self, clause: Clause):
        if isinstance(clause, Clause) is False:
            raise TypeError(f"past perfect can only be determined for Clause, not for {type(clause)}")
        verbs = self.get_verbs(clause)
        if self._has_aux_perfect(verbs):
            if self._has_verb_participle(verbs):
                return True
            elif [self.is_infinitive_verb(token) for token in verbs].count(True) >= 2:
                return True
        return False

    def is_simple_tense_clause(self, clause: Clause):
        verbs = self.get_verbs(clause)
        if len(verbs) == 0:
            return False
        return self.is_perfect_tense_clause(clause) is False and self._has_verb_finite(verbs)

    def is_past_perfect_clause(self, clause: Clause):
        return self.is_perfect_tense_clause(clause) and self.has_aux_past(clause)

    def is_present_perfect_clause(self, clause: Clause):
        return self.is_perfect_tense_clause(clause) and self.has_aux_present(clause)

    def is_past_simple_clause(self, clause: Clause):
        has_past_tense_verb = any(self.is_past_tense(token) for token in self.get_verbs(clause))
        return has_past_tense_verb and self.is_simple_tense_clause(clause)

    def is_present_simple_clause(self, clause: Clause):
        has_present_tense_verb = any(self.is_present_tense(token) for token in self.get_verbs(clause))
        return has_present_tense_verb and self.is_simple_tense_clause(clause)

    #######################
    # Group-level methods #
    #######################

    @staticmethod
    def get_pronoun_info(pron_token: Token) -> Dict[str, any]:
        """Old and tag set specific."""
        # person_fields = 'pt', 'vw_type', 'pos', 'case', 'status', 'person', 'card', 'genus'
        # seven_fields 'pt', 'vw_type', 'pos', 'case', 'status', 'person', 'card'
        # six_fields 'pt', 'vw_type', 'pos', 'case', 'position', 'inflection'
        xpos_fields = ['pt', 'vw_type', 'pos', 'case', 'status', 'person', 'card']
        # xpos_fields = ['Person', 'Poss', 'PronType', 'Case']
        xpos_values = pron_token.xpos.split('|')
        pron_info = {field: xpos_values[fi] if fi in xpos_fields else None for fi, field in enumerate(xpos_fields)}
        if pron_info['vw_type'] == 'pers':
            pron_info['genus'] = xpos_values[-1]
        for key in pron_token.feats:
            pron_info[key.lower()] = pron_token.feats[key].lower()
        pron_info['word'] = pron_token.text
        pron_info['lemma'] = pron_token.lemma
        return pron_info

    def get_person_pronouns(self, sent: Sentence) -> List[Token]:
        return [token for token in self.get_pronouns(sent.tokens) if self.is_person_pronoun(token)]

    @staticmethod
    def get_verb_info(verb_token: Token, head_id: int) -> Dict[str, any]:
        xpos_fields = ['pt', 'w_form', 'pv_time', 'card']
        # xpos_fields = ['VerbForm', 'Number', 'Tense']
        xpos_values = verb_token.xpos.split('|')
        verb_info = {field: xpos_values[fi] if fi in xpos_fields else None for fi, field in enumerate(xpos_fields)}
        for key in verb_token.feats:
            verb_info[key.lower()] = verb_token.feats[key].lower()
        verb_info['pos'] = verb_token.upos
        verb_info['word'] = verb_token.text
        verb_info['lemma'] = verb_token.lemma
        verb_info['word_index'] = verb_token.id
        verb_info['is_head_verb'] = verb_token.id == head_id
        verb_info['head_verb_id'] = head_id
        return verb_info

    def get_head_finite_verb_id(self, head_id: int, tokens: List[Token]) -> int:
        """Find the nearest head verb that is finite, or the root of the sentence."""
        head_verb = tokens[head_id]
        if head_verb.deprel == 'root':
            return head_id
        if head_id == -1:
            return head_id
        if self.is_finite_verb(head_verb):
            return head_id
        else:
            return self.get_head_finite_verb_id(head_verb.head, tokens)

    def group_tokens_by_finite_verb(self, tokens: List[Token], copy_conj_subject: bool = False,
                                    debug: int = 0):
        """Group all sentence tokens by verb groups that contain a finite verb."""
        head_verb_group = self.group_tokens_by_head_verb(tokens, copy_conj_subject=copy_conj_subject,
                                                         debug=debug-1)
        finite_verb_group = defaultdict(list)
        for head_verb_id in head_verb_group:
            if debug > 0:
                print(f"PatternNL.group_tokens_by_finite_verb - head_verb_id: {head_verb_id}")
            for token in head_verb_group[head_verb_id]:
                if debug > 0:
                    print(f"\ttoken for head_verb_group: {token.id} {token.text} {token.deprel}")
            if any(self.is_finite_verb(token) for token in head_verb_group[head_verb_id]):
                # this group has a finite-verb, so is a finite-verb group
                if debug > 0:
                    print('\t\thas finite verb - keeping group')
                finite_verb_group[head_verb_id] = [token for token in head_verb_group[head_verb_id]]
            elif any(token.deprel == 'root' for token in head_verb_group[head_verb_id]):
                # this is the top-level group but it has no finite verb
                if debug > 0:
                    print('\t\thas root - keeping group')
                finite_verb_group[head_verb_id] = [token for token in head_verb_group[head_verb_id]]
            else:
                # this group has no finite verb, so merge it with the
                # lowest ancestor finite verb group
                if debug > 0:
                    print('\t\thas no root nor finite verb - merging group')
                head_finite_verb_id = self.get_head_finite_verb_id(head_verb_id, tokens)
                finite_verb_group[head_finite_verb_id].extend(head_verb_group[head_verb_id])
        if copy_conj_subject is True:
            finite_verb_group = self.copy_subject_across_conjunctions(head_verb_group)
        return finite_verb_group

    def get_verb_clauses(self, sent: Sentence, copy_conj_subject: bool = False, debug: int = 0) -> List[Clause]:
        """Return all clausal units in the sentence that contain a head verb.

        A verb is the head of a clause if it is a finite verb (PV in Dutch).
        Here we follow the interpretation in the Lassy annotation scheme.
        See: https://www.let.rug.nl/vannoord/Lassy/sa-man_lassy.pdf"""
        finite_verb_group = self.group_tokens_by_finite_verb(sent.tokens, copy_conj_subject=copy_conj_subject,
                                                             debug=debug)
        clauses = []
        for head_id in sorted(finite_verb_group):
            clause = Clause(head_id, sorted(finite_verb_group[head_id], key=lambda t: t.id))
            clauses.append(clause)
        return clauses

