#!/usr/bin/env python3
import argparse
import json

import pagegraph.io as PG_IO
import pagegraph.queries as PG_Q

PARSER = argparse.ArgumentParser(
        prog="PageGraph <iframe> extractor",
        description="Extracts iframes from PageGraph recordings.")
PARSER.add_argument(
        "-i", "--input",
        required=True,
        help="Path to PageGraph file on disk.")
ARGS = PARSER.parse_args()
GRAPH = PG_IO.read_pagegraph(ARGS.input)
SUMMARY = PG_Q.summarize_iframes_in_graph(GRAPH)
print(json.dumps(SUMMARY))
