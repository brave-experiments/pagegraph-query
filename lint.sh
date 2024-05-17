#!/usr/bin/env bash

pycodestyle **/*.py
pycodestyle *.py
mypy --strict pagegraph/
