#!/usr/bin/env bash

pycodestyle **/*.py
mypy --strict pagegraph/
