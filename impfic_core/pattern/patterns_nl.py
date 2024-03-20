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
        return self.is_perfect_tense_clause(clause) is False

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
