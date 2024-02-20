# impfic-core

[![GitHub Actions](https://github.com/impact-and-fiction/impfic-core/workflows/tests/badge.svg)](https://github.com/impact-and-fiction/impfic-core/actions)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![PyPI](https://img.shields.io/pypi/v/impfic-core)](https://pypi.org/project/impfic-core/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/impfic-core)](https://pypi.org/project/impfic-core/)

Core code base for common functionalities

## Installing

```shell
pip install impfic-core
```


## Usage

### Dealing with output from different parsers

The Doc class of `impfic-core` offers a unified API to parsed document from different parsers (currently SpaCy and Trankit).

```python
import spacy
from trankit import Pipeline

import impfic_core.parse.doc as parse_doc

spacy_nlp = spacy.load('en_core_web_lg')

trankit_nlp = Pipeline('english')

# First paragraph of Moby Dick, taken from Project Gutenberg (https://www.gutenberg.org/cache/epub/2701/pg2701-images.html)
text = """Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world. It is a way I have of driving off the spleen and regulating the circulation. Whenever I find myself growing grim about the mouth; whenever it is a damp, drizzly November in my soul; whenever I find myself involuntarily pausing before coffin warehouses, and bringing up the rear of every funeral I meet; and especially whenever my hypos get such an upper hand of me, that it requires a strong moral principle to prevent me from deliberately stepping into the street, and methodically knocking people’s hats off—then, I account it high time to get to sea as soon as I can. This is my substitute for pistol and ball. With a philosophical flourish Cato throws himself upon his sword; I quietly take to the ship. There is nothing surprising in this. If they but knew it, almost all men in their degree, some time or other, cherish very nearly the same feelings towards the ocean with me."""
```

`Document` objects have the following properties: `text` (the whole text string) `sentences`, `tokens`, `entities` and optional `metadata` (a dictionary with whatever keys and values).

```python
# parse with both SpaCy and Trankit
spacy_doc = spacy_nlp(text)
trankit_doc = trankit_nlp(text)

# First, turn SpaCy document object to an impfic Doc
impfic_doc1 = parse_doc.spacy_json_to_doc(spacy_doc.to_json())

# Next, turn Trankit document object to an impfic Doc
impfic_doc2 = parse_doc.trankit_json_to_doc(trankit_doc)

# Show type and length of impfic_core Doc
# Doc length is number of tokens
print('impfic Doc of SpaCy parse:', type(impfic_doc1), len(impfic_doc1))

print('impfic Doc of Trankit parse:', type(impfic_doc2), len(impfic_doc2))
```

Outputs:
```python
>>> impfic Doc of SpaCy parse: <class 'impfic_core.parse.doc.Doc'> 190
>>> impfic Doc of Trankit parse: <class 'impfic_core.parse.doc.Doc'> 226
```

`Sentence` objects have the following properties:

- `id`: ID of the sentence in the document (running numbers)
- `tokens`: a list of `Token` objects
- `entitites`: a list of `Entity` objects (named entities identified by the parser)
- `text`: the sentence as text string 
- `start`: the character offset of the start of the sentence within the document
- `end`: the character offset of the end of the sentence within the document

### Extracting Clausal Units

```python
sent = doc.sentences[5]
for sent in doc.sentences:
    print(sent.text)
    clauses = pattern.get_verb_clauses(sent)
    for clause in clauses:
        print([t.text for t in clause])
```

```python
With a philosophical flourish Cato throws himself upon his sword; I quietly take to the ship.
clause: ['With', 'a', 'philosophical', 'flourish', 'Cato', 'throws', 'himself', 'upon', 'his', 'sword', ';', '.']
clause: ['I', 'quietly', 'take', 'to', 'the', 'ship']
```


### External Resources

To use utilities for external resources such as the RBN, you need to point to your copy of those resources 
in the settings (`settings.py`). Once you have done that, you can use them with:

```python
from settings import rbn_file
from impfic_core.resources.rbn import RBN

rbn = RBN(rbn_file)

rbn.has_term('aanbiddelijk') # returns True
```

## Anonymisation

For review anonymisation you need a salt hash in a file called `impfic_core/secrets.py`. The repository doesn't contain this file to ensure other cannot recreate the user ID mapping. 
An example file is available as `impfic_core/secrets_example.py`. Copy this file to `impfic_core/secrets.py` and update the salt hash to do your own user ID mapping.

