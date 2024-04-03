import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Token:

    id: int
    doc_idx: int
    text: str
    lemma: str
    upos: str
    xpos: str
    xpos_dict: Dict[str, any]
    feats: Dict[str, any]
    head: int
    deprel: str
    ner: str
    start: int
    end: int

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, text={self.text}, upos={self.upos}, xpos='{self.xpos}')"


@dataclass
class Entity:

    tokens: List[Token]
    text: str
    start: int
    end: int
    label: str


@dataclass
class Clause:

    id: int
    tokens: List[Token]

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, tokens={self.tokens})"

    def __iter__(self):
        for token in self.tokens:
            yield token


@dataclass
class Sentence:

    id: int
    tokens: List[Token]
    entities: List[Entity]
    text: str
    start: int
    end: int

    def __len__(self):
        return len(self.tokens)

    def __iter__(self):
        for token in self.tokens:
            yield token


@dataclass
class Doc:

    text: str
    sentences: List[Sentence]
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def tokens(self):
        return [token for sent in self.sentences for token in sent.tokens]

    @property
    def entities(self):
        return [ent for sent in self.sentences for ent in sent.entities]

    def __len__(self):
        return len(self.tokens)


def parse_features(features: str) -> Dict[str, any]:
    feats = [feat for feat in features.split('|') if len(feat) > 0]
    feature_dict = {}
    for feat in feats:
        if '=' in feat:
            key, value = feat.split('=')
        else:
            key, value = feat, True
        feature_dict[key] = int(value) if isinstance(value, str) and value.isdigit() else value
    # feats = [feat.split('=') for feat in features.split('|') if len(feat) > 0]
    # for key, value in feats:
    #     feature_dict[key] = int(value) if value.isdigit() else value
    return feature_dict


def trankit_json_to_token(doc_idx: int, sent_idx: int, token: Dict[str, any]) -> Token:
    try:
        return Token(
            id=sent_idx,
            doc_idx=doc_idx,
            text=token['text'],
            lemma=token['lemma'],
            upos=token['upos'],
            xpos=token['xpos'],
            xpos_dict=parse_features(token['xpos']) if '|' in token['xpos'] else {},
            head=token['head'] - 1,
            feats=parse_features(token['feats']) if 'feats' in token else {},
            start=token['dspan'][0],
            end=token['dspan'][1],
            deprel=token['deprel'] if 'deprel' in token else None,
            ner=token['ner'] if 'ner' in token else None
        )
    except ValueError:
        print(f"Error in token with doc_idx '{doc_idx}', sent_idx '{sent_idx}': {token}")
        raise


def spacy_json_to_token(doc_idx: int, sent_idx: int, token: Dict[str, any], doc: Dict[str, any]) -> Token:
    head_shift = doc_idx - sent_idx
    return Token(
        id=sent_idx,
        doc_idx=doc_idx,
        text=doc['text'][token['start']:token['end']],
        lemma=token['lemma'],
        upos=token['pos'],
        xpos=token['tag'],
        xpos_dict=parse_features(token['tag']) if '|' in token['tag'] else {},
        head=token['head'] - head_shift,
        feats=parse_features(token['morph']) if 'morph' in token else {},
        start=token['start'],
        end=token['end'],
        deprel=token['dep'] if 'dep' in token else None,
        ner=token['ner'] if 'ner' in token else None
    )


def init_spacy_sent(sent: Dict[str, any], doc_json: Dict[str, any]):
    return {
        'text': doc_json[sent['start']:sent['end']]
    }


def spacy_json_to_entities(tokens: List[Token], ents: List[Dict[str, any]],
                           doc_json: Dict[str, any]) -> List[Entity]:
    ent_idx = 0
    curr_ent = ents[ent_idx] if len(ents) > ent_idx else None
    entities = []
    entity_tokens = []
    for token in tokens:
        while curr_ent and token.start >= curr_ent['end']:
            if len(entity_tokens) > 0:
                entity = Entity(entity_tokens, doc_json['text'][curr_ent['start']:curr_ent['end']],
                                curr_ent['start'], curr_ent['end'], curr_ent['label'])
                entities.append(entity)
            ent_idx += 1
            curr_ent = ents[ent_idx] if ent_idx < len(ents) else None
        entity_tokens.append(token)
    return entities


def trankit_json_to_entity(entity_tokens: List[Token], sent: Dict[str, any], sent_start: int) -> Entity:
    start_in_doc = entity_tokens[0].start
    end_in_doc = entity_tokens[-1].end
    start_in_sent = start_in_doc - sent_start
    end_in_sent = end_in_doc - sent_start
    entity_text = sent['text'][start_in_sent:end_in_sent]
    label = entity_tokens[0].ner[2:]
    return Entity(entity_tokens, entity_text, start_in_doc, end_in_doc, label)


def trankit_json_to_entities(sent_tokens: List[Token], sent: Dict[str, any]) -> List[Entity]:
    """Turn the tokens of a Trankit sentence with NER labels into entities."""
    entity_tokens = []
    entities = []
    if len(sent_tokens) == 0:
        return entities
    sent_start = sent_tokens[0].start
    for token in sent_tokens:
        if token.ner[0] in 'OBS':
            if len(entity_tokens) > 0:
                entity = trankit_json_to_entity(entity_tokens, sent, sent_start)
                entities.append(entity)
            entity_tokens = []
        if token.ner != 'O':
            entity_tokens.append(token)
    if len(entity_tokens) > 0:
        entity = trankit_json_to_entity(entity_tokens, sent, sent_start)
        entities.append(entity)
    return entities


def spacy_json_to_sentence(sent_idx: int, token_offset: int, sent: Dict[str, any], ents: List[Dict[str, any]],
                           tokens: List[Dict[str, any]], doc_json: Dict[str, any]) -> Sentence:
    tokens = [spacy_json_to_token(ti+token_offset, ti, token, doc_json) for ti, token in enumerate(tokens)]
    entities = spacy_json_to_entities(tokens, ents, doc_json)
    return Sentence(
        id=sent_idx,
        text=doc_json['text'][sent['start']:sent['end']],
        tokens=tokens,
        entities=entities,
        start=sent['start'],
        end=sent['end']
    )


def trankit_json_to_sentence(token_offset: int, sentence: Dict[str, any],
                             skip_bad_tokens: bool = False) -> Sentence:
    if skip_bad_tokens is True:
        tokens = []
        for ti, token in enumerate(sentence['tokens']):
            try:
                token = trankit_json_to_token(ti+token_offset, ti, token)
                tokens.append(token)
            except KeyError:
                continue
    else:
        tokens = [trankit_json_to_token(ti+token_offset, ti, token) for ti, token in enumerate(sentence['tokens'])]
    entities = trankit_json_to_entities(tokens, sentence)
    return Sentence(
        id=sentence['id'],
        text=sentence['text'],
        tokens=tokens,
        entities=entities,
        start=sentence['tokens'][0]['dspan'][0],
        end=sentence['tokens'][-1]['dspan'][1]
    )


def json_to_doc(doc_json: Dict[str, any]) -> Doc:
    if 'sents' in doc_json and 'tokens' in doc_json and 'ents' in doc_json:
        doc = spacy_json_to_doc(doc_json)
    elif 'sentences' in doc_json and 'text' in doc_json and 'ents' not in doc_json:
        doc = trankit_json_to_doc(doc_json)
    else:
        raise TypeError(f"invalid parsed JSON doc, should be a SpaCy or Trankit JSON document.")
    for doc_field in doc_json:
        if doc_field not in {'sents', 'sentences', 'tokens', 'ents', 'text'}:
            doc.metadata[doc_field] = doc_json[doc_field]
    return doc


def sort_spacy_tokens_by_sents(doc_json: Dict[str, any], token_type: str) -> List[List[Dict[str, any]]]:
    sent_idx = 0
    curr_sent = doc_json['sents'][sent_idx]
    sents_tokens = []
    sent_tokens = []
    for token in doc_json[token_type]:
        while token['start'] >= curr_sent['end']:
            sents_tokens.append(sent_tokens)
            sent_tokens = []
            sent_idx += 1
            curr_sent = doc_json['sents'][sent_idx]
        if token['end'] > curr_sent['end']:
            print(f"WARNING: end of token ({token['end']}) beyond end of sentence ({curr_sent['end']}).")
            print('sent_idx:', sent_idx)
            print('curr_sent:', curr_sent)
            print('token:', token)
        assert token['end'] <= curr_sent['end'], f"token['end'] ({token['end']}) " \
                                                 f"after curr_sent['end'] ({curr_sent['end']})"
        sent_tokens.append(token)
    if len(sent_tokens) > 0:
        sents_tokens.append(sent_tokens)
    if len(doc_json[token_type]) == 0:
        for _ in doc_json['sents']:
            sents_tokens.append([])
    return sents_tokens


def spacy_json_to_doc(doc_json: Dict[str, any]) -> Doc:
    sentences = []
    sents_tokens = sort_spacy_tokens_by_sents(doc_json, 'tokens')
    sents_ents = sort_spacy_tokens_by_sents(doc_json, 'ents')
    sent_idxs = [i for i in range(len(doc_json['sents']))]
    token_offset = 0
    for si, sent, tokens, ents in zip(sent_idxs, doc_json['sents'], sents_tokens, sents_ents):
        sentence = spacy_json_to_sentence(si, token_offset, sent, ents, tokens, doc_json)
        sentences.append(sentence)
        token_offset += len(tokens)
    return Doc(text=doc_json['text'], sentences=sentences)


def trankit_json_to_doc(doc_json: Dict[str, any], skip_bad_tokens: bool = False) -> Doc:
    sentences = []
    token_offset = 0
    for sent_json in doc_json['sentences']:
        sent = trankit_json_to_sentence(token_offset, sent_json, skip_bad_tokens=skip_bad_tokens)
        token_offset += len(sent_json['tokens'])
        sentences.append(sent)
    return Doc(text=doc_json['text'], sentences=sentences)


def merge_docs(docs: List[Doc]) -> Doc:
    """Merge a list of Docs into a single Doc instance."""
    return Doc(
        text='\n'.join([chunk.text for chunk in docs]),
        sentences=[sent for chunk in docs for sent in chunk.sentences]
    )
