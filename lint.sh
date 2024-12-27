#!/usr/bin/env bash

pylint pagegraph run.py tests.py
mypy --strict pagegraph/
