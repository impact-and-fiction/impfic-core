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

For review anonymisation you need a salt hash in a file called `impfic_core/secrets.py`. The repository doesn't contain this file to ensure other cannot recreate the user ID mapping. 
An example file is available as `impfic_core/secrets_example.py`. Copy this file to `impfic_core/secrets.py` and update the salt hash to do your own user ID mapping.

## Usage

To use utilities for external resources such as the RBN, you need to point to your copy of those resources 
in the settings (`settings.py`). Once you have done that, you can use them with:

```python
from settings import rbn_file
from impfic_core.resources.rbn import RBN

rbn = RBN(rbn_file)

rbn.has_term('aanbiddelijk') # returns True
```
