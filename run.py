#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys

import pagegraph.commands
import pagegraph.commands.element
import pagegraph.commands.html
import pagegraph.commands.js_calls
import pagegraph.commands.requests
import pagegraph.commands.scripts
import pagegraph.commands.subframes
import pagegraph.commands.unknown
import pagegraph.commands.validate
import pagegraph.serialize
import pagegraph.types
from pagegraph import __version__


# pylint: disable=too-many-return-statements
def get_command(args: argparse.Namespace) -> pagegraph.commands.Base:
    match args.command_name:
        case "subframes":
            return pagegraph.commands.subframes.Command(
                args.input, args.local, args.party_filter, args.debug)
        case "validate":
            return pagegraph.commands.validate.Command(args.input)
        case "requests":
            return pagegraph.commands.requests.Command(
                args.input, args.frame, args.debug)
        case "scripts":
            return pagegraph.commands.scripts.Command(
                args.input, args.frame, args.id, args.source,
                args.omit_executors, args.debug)
        case "js_calls":
            return pagegraph.commands.js_calls.Command(
                args.input, args.frame, args.cross, args.method, args.id,
                args.debug)
        case "element":
            return pagegraph.commands.element.Command(
                args.input, args.id, args.depth, args.graphml, args.debug)
        case "html":
            return pagegraph.commands.html.Command(
                args.input, args.frame, args.at_serialization,
                args.body_content, args.debug)
        case "unknown":
            return pagegraph.commands.unknown.Command(args.input)
        case _:
            raise ValueError(f"Unknown command name: {args.command_name}")


PARSER = argparse.ArgumentParser(
    prog="PageGraph Query",
    description="Extracts information about a Web page's execution from "
                " a PageGraph recordings.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

PARSER.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {__version__}")
PARSER.add_argument("--debug", action="store_true", default=False)
PARSER.set_defaults(command_name="")

SUBPARSERS = PARSER.add_subparsers(required=True)

SUBFRAMES_PARSER = SUBPARSERS.add_parser(
    "subframes",
    help="Print information about subframes created and loaded by page.")
SUBFRAMES_PARSER.add_argument(
    "input",
    type=pathlib.Path,
    help="Path to PageGraph recording.")
SUBFRAMES_PARSER.add_argument(
    "-l", "--local",
    action="store_true",
    help="Print information about frames that are inherit their parent "
         "frame's security context (i.e., about:blank, about:srcdoc) at "
         "serialization time.")
SUBFRAMES_PARSER.add_argument(
    "--party-filter",
    choices=pagegraph.types.PartyFilterOption,
    default=pagegraph.types.PartyFilterOption.NONE.value,
    help="Only return frames that have the same (first-party) or different "
         "(third-party) security origin as the top-level document.")
SUBFRAMES_PARSER.set_defaults(command_name="subframes")

VALIDATE_PARSER = SUBPARSERS.add_parser(
    "validate",
    help="Just runs all validation and structure checks against a graph.")
VALIDATE_PARSER.add_argument(
    "input",
    type=pathlib.Path,
    help="Path to PageGraph recording.")
VALIDATE_PARSER.set_defaults(command_name="validate")

REQUEST_PARSER = SUBPARSERS.add_parser(
    "requests",
    help="Print information about requests made during page execution.")
REQUEST_PARSER.add_argument(
    "input",
    type=pathlib.Path,
    help="Path to PageGraph recording.")
REQUEST_PARSER.add_argument(
    "-f", "--frame",
    default=None,
    help="Only print information about requests made in a specific frame "
         "(as described by PageGraph node ids, in the format 'n##').")
REQUEST_PARSER.set_defaults(command_name="requests")

SCRIPTS_PARSER = SUBPARSERS.add_parser(
    "scripts",
    help="Print information about JS units executed during page execution.")
SCRIPTS_PARSER.add_argument(
    "input",
    type=pathlib.Path,
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
SCRIPTS_PARSER.set_defaults(command_name="scripts")

JS_CALLS_PARSER = SUBPARSERS.add_parser(
    "js-calls",
    help="Print information about JS calls made during page execution.")
JS_CALLS_PARSER.add_argument(
    "input",
    type=pathlib.Path,
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
         "Script node with the given ID "
         "(as described by PageGraph node ids, in the format 'n##').")
JS_CALLS_PARSER.set_defaults(command_name="js_calls")

ELEMENT_QUERY_PARSER = SUBPARSERS.add_parser(
    "elm",
    help="Print information about a node or edge in the graph.")
ELEMENT_QUERY_PARSER.add_argument(
    "input",
    type=pathlib.Path,
    help="Path to PageGraph recording.")
ELEMENT_QUERY_PARSER.add_argument(
    "id",
    help="The id of the node to print information about "
         "(as described by PageGraph node ids, in the format 'n##')")
ELEMENT_QUERY_PARSER.add_argument(
    "-d", "--depth",
    default=1,
    type=int,
    help="Depth of the recursion to summarize in the graph. Defaults to 1 "
         "(only print detailed information about target element).")
ELEMENT_QUERY_PARSER.add_argument(
    "--graphml", "-g",
    type=pathlib.Path,
    help="Write the element (and its surrounding subgraph, as determined by "
         "the depth argument) to disk as a graphml encoded graph at the given "
         "path.")
ELEMENT_QUERY_PARSER.set_defaults(command_name="element")

HTML_QUERY_PARSER = SUBPARSERS.add_parser(
    "html",
    help="Print information about the HTML elements in a document.")
HTML_QUERY_PARSER.add_argument(
    "input",
    type=pathlib.Path,
    help="Path to PageGraph recording.")
HTML_QUERY_PARSER.add_argument(
    "-f", "--frame",
    default=None,
    help="Only include HTML elements that were inserted into the document in "
         "a given frame (as described by PageGraph node ids, in the format "
         "'n##').")
HTML_QUERY_PARSER.add_argument(
    "-s", "--at-serialization",
    default=False,
    action="store_true",
    help="If passed, only include HTML elements that were presented in the "
         "document when the document was serialized (i.e., they weren't "
         "inserted and then later deleted.).")
HTML_QUERY_PARSER.add_argument(
    "-b", "--body-content",
    default=False,
    action="store_true",
    help="Only return elements that appear in the body of the document, "
         "meaning elements that are a child of the <body> element.")
HTML_QUERY_PARSER.set_defaults(command_name="html")

UNKNOWN_QUERY_PARSER = SUBPARSERS.add_parser(
    "unknown",
    help="Print information about any events that occurred where we "
         "could not attribute the script event to a running script. (note "
         "this is different from the 'validate' command, which only checks "
         "if the structure of the graph is as expected).")
UNKNOWN_QUERY_PARSER.add_argument(
    "input",
    type=pathlib.Path,
    help="Path to PageGraph recording.")
UNKNOWN_QUERY_PARSER.set_defaults(command_name="unknown")


try:
    ARGS = PARSER.parse_args()
    command = get_command(ARGS)
    command.validate()
    RESULT = command.execute()
    print(command.format(RESULT))
except ValueError as e:
    print(f"Invalid argument: {e}", file=sys.stderr)
    sys.exit(1)
