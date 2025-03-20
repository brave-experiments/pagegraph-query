#!/usr/bin/env bash

pylint --rcfile pylintrc pagegraph run.py tests.py
mypy --config-file mypy.ini --strict run.py tests.py pagegraph/
