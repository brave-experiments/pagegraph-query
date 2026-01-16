#!/usr/bin/env python3
import os
import sys

from pagegraph.cli.run import run

DEPRECATION_MSG = """
---

Deprecated: Future versions will remove this script. Please use built
executable instead. You can do so as follows:

1. Build this package:
    pip install .
2. Run the `pagegraph-query` script, which will be in your (VENV) $PATH.
    pagegraph-query --help

You can suppress this query by having PAGEGRAPH_QUERY_DEPRECATION=1 in your
environment.

---
"""

def is_deprecation_env_set() -> bool:
    env_key = "PAGEGRAPH_QUERY_DEPRECATION"
    if env_key not in os.environ:
        return False
    return os.environ[env_key] == "1"

if not is_deprecation_env_set():
    print(DEPRECATION_MSG, file=sys.stderr)

sys.exit(run())
