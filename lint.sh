#!/usr/bin/env bash

pylint pagegraph *.py
mypy --strict pagegraph/
