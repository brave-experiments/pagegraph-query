#!/usr/bin/env python3
import argparse
import json
import os
import sys

import pagegraph.commands
import pagegraph.serialize


def subframes_cmd(args):
    return pagegraph.commands.subframes(args.input, args.local, args.debug)


def request_cmd(args):
    return pagegraph.commands.requests(args.input, args.frame, args.debug)


def js_calls_cmd(args):
    return pagegraph.commands.js_calls(args.input, args.frame, args.cross,
                                       args.method, args.debug)


PARSER = argparse.ArgumentParser(
        prog="PageGraph query",
        description="Extracts information about a Web page's execution from "
                    " a PageGraph recordings.")

PARSER.add_argument("--version", action="version", version="%(prog)s 0.6.1")
PARSER.add_argument("--debug", action="store_true", default=False)

SUBPARSERS = PARSER.add_subparsers(required=True)

SUBFRAMES_PARSER = SUBPARSERS.add_parser(
    "subframes",
    help="Print information about subframes created and loaded by page.")
SUBFRAMES_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
SUBFRAMES_PARSER.add_argument(
    "-l", "--local",
    action="store_true",
    help="Only print information about about frames that are local to"
         " the top level frame at serialization time.")
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
    help="Only print information about requests made in a specific frame "
         "(as described by PageGraph node ids, in the format 'n##').")
REQUEST_PARSER.set_defaults(func=request_cmd)

JS_CALLS_PARSER = SUBPARSERS.add_parser(
    "js-calls",
    help="Print information about JS calls made during page execution.")
JS_CALLS_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
JS_CALLS_PARSER.add_argument(
    "-f", "--frame",
    default=None,
    help="Only include JS calls made by code running in this frame's context"
         "(as described by PageGraph node ids, in the format 'n##'). "
         "Note that this filters on the calling frame context, not the "
         "receiving frame context, which will differ in some cases, such as "
         "same-origin cross-frame calls.")
JS_CALLS_PARSER.add_argument(
    "-c", "--cross",
    default=False,
    action="store_true",
    help="Only include JS calls where the calling frame context and the "
         "receiving frame context differ.")
JS_CALLS_PARSER.add_argument(
    "-m", "--method",
    default=None,
    help="Only include JS calls where the function or method being called "
         "includes this value as a substring.")
JS_CALLS_PARSER.set_defaults(func=js_calls_cmd)

try:
    ARGS = PARSER.parse_args()
    RESULT = ARGS.func(ARGS)
    REPORT = pagegraph.serialize.to_jsonable(RESULT)
    print(json.dumps(REPORT))
except ValueError as e:
    print(f"Invalid argument: {e}", file=sys.stderr)
    sys.exit(1)
