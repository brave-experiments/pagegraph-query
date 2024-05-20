#!/usr/bin/env bash

pycodestyle .
mypy --strict pagegraph/
