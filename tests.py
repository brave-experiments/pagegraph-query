#!/usr/bin/env python3
import argparse
import sys

import pagegraph.tests.commands


def serve_cmd(args: argparse.Namespace, other_args: list[str]) -> None:
    pagegraph.tests.commands.serve(
        args.port, args.verbose, other_args)


def setup_cmd(args: argparse.Namespace, other_args: list[str]) -> None:
    pagegraph.tests.commands.setup(
        args.path, args.filter, args.port, args.clear, args.verbose,
        other_args)


def run_cmd(args: argparse.Namespace, other_args: list[str]) -> None:
    pagegraph.tests.commands.run(args.filter, args.verbose)


PARSER = argparse.ArgumentParser(
        prog="Generate PageGraph-query tests",
        description="Tools for setting up and running tests against "
                    "PageGraph graphs")

SUBPARSERS = PARSER.add_subparsers(required=True)

SERVE_PARSER = SUBPARSERS.add_parser(
    "serve",
    help="Just run the HTTP server with the test files.")
SERVE_PARSER.add_argument(
    "--port",
    default=8000,
    help="Port to use for the test server.")
SERVE_PARSER.add_argument(
    "--verbose",
    default=False,
    action="store_true",
    help="Print verbose amounts detail about the test server.")
SERVE_PARSER.set_defaults(func=serve_cmd)

SETUP_PARSER = SUBPARSERS.add_parser(
    "generate",
    help="Generate test data to run tests against.")
SETUP_PARSER.add_argument(
    "path",
    help="Path to the root of the pagegraph-crawl workspace, as cloned  "
         "from https://github.com/brave/pagegraph-crawl.")
SETUP_PARSER.add_argument(
    "--filter",
    default=None,
    help="If provided, will only generate graphs for tests that contain this "
         "argument as a substring (i.e., just uses `str.contains` against "
         "the file names in ./graphs/")
SETUP_PARSER.add_argument(
    "--port",
    default=8000,
    help="Port to use for the test server when generating graphs.")
SETUP_PARSER.add_argument(
    "--clear",
    default=False,
    action="store_true",
    help="If passed, will delete all test graphs before generating new ones.")
SETUP_PARSER.add_argument(
    "--verbose",
    default=False,
    action="store_true",
    help="Print verbose amounts detail of the graph generation process.")
SETUP_PARSER.set_defaults(func=setup_cmd)

RUN_PARSER = SUBPARSERS.add_parser(
    "run",
    help="Run the unittest test suite.")
RUN_PARSER.add_argument(
    "--filter",
    default=None,
    help="If provided, will only run tests that match this name.")
RUN_PARSER.add_argument(
    "-v", "--verbose",
    default=False,
    action="store_true",
    help="If passed, report test statuses with more verbosity.")
RUN_PARSER.set_defaults(func=run_cmd)

try:
    LOCAL_ARGS, OTHER_ARGS = PARSER.parse_known_args()
    RESULT = LOCAL_ARGS.func(LOCAL_ARGS, OTHER_ARGS)
except ValueError as e:
    print(f"Invalid argument: {e}", file=sys.stderr)
    sys.exit(1)
