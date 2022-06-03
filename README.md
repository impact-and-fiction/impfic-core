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

To use utilities for external resources such as the RBN, you need to point to your copy of those resources 
in the settings (`settings.py`). Once you have done that, you can use them with:

```python
from settings import rbn_file
from impfic_core.resources.rbn import RBN

rbn = RBN(rbn_file)

rbn.has_term('aanbiddelijk') # returns True
```
