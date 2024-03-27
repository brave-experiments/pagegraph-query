#!/usr/bin/env python3
import argparse
import json
import sys

import pagegraph.commands


def frametree_cmd(args):
    return pagegraph.commands.frametree(args.input)


def subframes_cmd(args):
    return pagegraph.commands.subframes(args.input, args.local)


def request_cmd(args):
    return pagegraph.commands.requests(args.input, args.frame)


PARSER = argparse.ArgumentParser(
        prog="PageGraph query",
        description="Extracts information about a Web page's execution from "
                    " a PageGraph recordings.")

SUBPARSERS = PARSER.add_subparsers(required=True)

FRAME_TREE_PARSER = SUBPARSERS.add_parser(
    "frametree",
    help="Prints the frame tree of all documents in the recording.")
FRAME_TREE_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
FRAME_TREE_PARSER.set_defaults(func=frametree_cmd)

SUBFRAMES_PARSER = SUBPARSERS.add_parser(
    "subframes",
    help="Print information about subframes created and loaded by page.")
SUBFRAMES_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
SUBFRAMES_PARSER.add_argument(
    "-l", "--local",
    action="store_true",
    help="Only print information about about frames that are local at "
         "serialization time.")
SUBFRAMES_PARSER.set_defaults(func=subframes_cmd)

REQUEST_PARSER = SUBPARSERS.add_parser(
    "requests",
    help="Print information about requests made during page execution.")
REQUEST_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
REQUEST_PARSER.add_argument(
    "-f", "--frame",
    default=None,
    help="Only print information about requests made in a specific frames "
         "(as described by PageGraph node ids, in the format 'n##'). "
         "By default, all requests, in all frames, are described.")
REQUEST_PARSER.set_defaults(func=request_cmd)

ARGS = PARSER.parse_args()
try:
    RESULT = ARGS.func(ARGS)
    print(json.dumps(RESULT))
except ValueError as e:
    print(f"Invalid argument: {e}", file=sys.stderr)
    sys.exit(1)
