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
PARSER.add_argument(
        "-l", "--local",
        action="store_true",
        help="Only print information about about frames that are local at "
             "serialization time.")
ARGS = PARSER.parse_args()
GRAPH = PG_IO.read_pagegraph(ARGS.input)
SUMMARY = PG_Q.summarize_iframes_in_graph(GRAPH, ARGS.local)
print(json.dumps(SUMMARY))
