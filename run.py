#!/usr/bin/env python3
import argparse
import json
import os
import sys

import pagegraph.commands
import pagegraph.serialize
from pagegraph import VERSION


def scripts_cmd(args):
    return pagegraph.commands.scripts(args.input, args.frame, args.id,
                                      args.source, args.omit_executors,
                                      args.debug)


def effects_cmd(args):
    return pagegraph.commands.effects(args.input, args.id, args.loose,
                                      args.debug)


def element_query_cmd(args):
    return pagegraph.commands.element_query(args.input, args.id, args.depth,
                                            args.debug)


def js_calls_cmd(args):
    return pagegraph.commands.js_calls(args.input, args.frame, args.cross,
                                       args.method, args.id, args.debug)


def request_cmd(args):
    return pagegraph.commands.requests(args.input, args.frame, args.debug)


def subframes_cmd(args):
    return pagegraph.commands.subframes(args.input, args.local, args.debug)


def validate_cmd(args):
    return pagegraph.commands.validate(args.input)


PARSER = argparse.ArgumentParser(
        prog="PageGraph Query",
        description="Extracts information about a Web page's execution from "
                    " a PageGraph recordings.")

PARSER.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {VERSION}")
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

VALIDATE_PARSER = SUBPARSERS.add_parser(
    "validate",
    help="Just runs all validation and structure checks against a graph.")
VALIDATE_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
VALIDATE_PARSER.set_defaults(func=validate_cmd)

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

SCRIPTS_PARSER = SUBPARSERS.add_parser(
    "scripts",
    help="Print information about JS units executed during page execution.")
SCRIPTS_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
SCRIPTS_PARSER.add_argument(
    "-i", "--id",
    default=None,
    help="If provided, only print information about JS units with the given "
         "ID (as described by PageGraph node ids, in the format 'n##').")
SCRIPTS_PARSER.add_argument(
    "-s", "--source",
    default=False,
    action="store_true",
    help="If included, also include script source in each report.")
SCRIPTS_PARSER.add_argument(
    "-f", "--frame",
    default=None,
    help="Only include JS code units executed in a particular frame "
         "context (as described by PageGraph node ids, in the format 'n##'). "
         "Note that this filters on the calling frame context, not the "
         "receiving frame context, which will differ in some cases, such as "
         "same-origin cross-frame calls.")
SCRIPTS_PARSER.add_argument(
    "-o", "--omit-executors",
    default=False,
    action="store_true",
    help="If included, do not append information about why or how each script "
         "was executed.")
SCRIPTS_PARSER.set_defaults(func=scripts_cmd)

JS_CALLS_PARSER = SUBPARSERS.add_parser(
    "js-calls",
    help="Print information about JS calls made during page execution.")
JS_CALLS_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
JS_CALLS_PARSER.add_argument(
    "-f", "--frame",
    default=None,
    help="Only include JS calls made by code running in this frame's context "
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
JS_CALLS_PARSER.add_argument(
    "-i", "--id",
    default=None,
    help="If provided, only print information about JS calls made by the "
         "JS code with the give ID "
         "(as described by PageGraph node ids, in the format 'n##').")
JS_CALLS_PARSER.set_defaults(func=js_calls_cmd)

ELEMENT_QUERY_PARSER = SUBPARSERS.add_parser(
    "elm",
    help="Print information about a node or edge in the graph.")
ELEMENT_QUERY_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
ELEMENT_QUERY_PARSER.add_argument(
    "id",
    help="The id of the node to print information about "
         "(as described by PageGraph node ids, in the format 'n##')")
ELEMENT_QUERY_PARSER.add_argument(
    "-d", "--depth",
    default=0,
    type=int,
    help="Depth of the recursion to summarize in the graph. Defaults to 0 "
         "(only print detailed information about target element).")
ELEMENT_QUERY_PARSER.set_defaults(func=element_query_cmd)

EFFECTS_QUERY_PARSER = SUBPARSERS.add_parser(
    "effects",
    help="Print information about the effects the given element had on "
         "the page. By default only includes requests.")
EFFECTS_QUERY_PARSER.add_argument(
    "input",
    help="Path to PageGraph recording.")
EFFECTS_QUERY_PARSER.add_argument(
    "id",
    help="Id of a frame, script, request, or parser node "
         "(as described by PageGraph node ids, in the format 'n##').")
EFFECTS_QUERY_PARSER.add_argument(
    "-l", "--loose",
    default=False,
    action="store_true",
    help="By default, the 'effects' query includes any action or element "
         "where the target node was the primary cause of the action (i.e., "
         "actions where the target node was the most immediate cause). "
         "Passing this flag loosens that, and includes any action or element "
         "that this node was involved with at all.")
# EFFECTS_QUERY_PARSER.add_argument(
#     "--include-js-builtin-calls",
#     default=False,
#     action="store_true",
#     help="Include calls to JS builtins that occurred because of the target "
#           "node.")
# EFFECTS_QUERY_PARSER.add_argument(
#     "--include-web-api-calls",
#     default=False,
#     action="store_true",
#     help="Include calls to instrumented Web APIs that occurred because of "
#          "the target node.")
# EFFECTS_QUERY_PARSER.add_argument(
#     "--exclude-requests",
#     default=False,
#     action="store_true",
#     help="Do not include requests that occurred because of the target node.")

EFFECTS_QUERY_PARSER.set_defaults(func=effects_cmd)


try:
    ARGS = PARSER.parse_args()
    RESULT = ARGS.func(ARGS)
    REPORT = pagegraph.serialize.to_jsonable(RESULT)
    print(json.dumps(REPORT))
except ValueError as e:
    print(f"Invalid argument: {e}", file=sys.stderr)
    sys.exit(1)
