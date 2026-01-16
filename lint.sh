#!/usr/bin/env bash

pylint --rcfile pylintrc run.py src/pagegraph tests/
mypy --config-file mypy.ini --strict run.py tests.py src/pagegraph tests/**/*.py
