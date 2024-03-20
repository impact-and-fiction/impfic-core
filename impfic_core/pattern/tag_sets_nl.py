# HEAD_VERB_DEPRELS = {'xcomp', 'cc', 'conj', 'nsubj:pass'}
VERB_POS = {'VERB', 'AUX'}
SUBS = {'nsubj', 'nsubj:pass', 'csubj'}
OBJS = {'obj', 'iobj', 'dobj', 'pobj', 'obl', 'obl:agent'}
SUB_OBJS = {'nsubj', 'nsubj:pass', 'csubj', 'obj', 'iobj', 'obl', 'obl:agent'}
NON_HEAD_VERB_DEPRELS = {'xcomp', 'nsubj:pass', 'aux:pass', None}

# pv
# inf in beknopte bijzin

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
    'is_head_verb', 'head_verb_id'
    # verb_foreign, verb_degree, verb_gender
]

