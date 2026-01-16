#!/usr/bin/env python3
"""Test runner and utility. Has three commands:
- run: runs all the tests (defined in tests/cases/*.py)
- generate: uses pagegraph-crawl to generate pagegraph-format graphml files,
            which are the datasets tests are run against.
- serve: launches the server used to run the `generate` command against. Only
         really useful when debugging the .html pages tested against.

Run ./tests.py --help for more information.
"""
import argparse
import sys

import tests.commands


def serve_cmd(args: argparse.Namespace, other_args: list[str]) -> None:
    # pylint: disable=unused-argument
    tests.commands.serve(args.port, args.verbose)


def generate_cmd(args: argparse.Namespace, other_args: list[str]) -> None:
    tests.commands.generate(
        args.path, args.filter, args.port, args.clear, args.verbose,
        other_args)


def run_cmd(args: argparse.Namespace, other_args: list[str]) -> None:
    # pylint: disable=unused-argument
    tests.commands.run(args.filter, args.verbose)


PARSER = argparse.ArgumentParser(
        prog="Generate pageqraph-query tests",
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

GENERATE_PARSER = SUBPARSERS.add_parser(
    "generate",
    help="Generate test data to run tests against.")
GENERATE_PARSER.add_argument(
    "path",
    help="Path to the root of the pagegraph-crawl workspace, as cloned  "
         "from https://github.com/brave/pagegraph-crawl.")
GENERATE_PARSER.add_argument(
    "--filter",
    default=None,
    help="If provided, will only generate graphs for tests that contain this "
         "argument as a substring (i.e., just uses `str.contains` against "
         "the file names in ./graphs/")
GENERATE_PARSER.add_argument(
    "--port",
    default=8000,
    help="Port to use for the test server when generating graphs.")
GENERATE_PARSER.add_argument(
    "--clear",
    default=False,
    action="store_true",
    help="If passed, will delete all test graphs before generating new ones.")
GENERATE_PARSER.add_argument(
    "--verbose",
    default=False,
    action="store_true",
    help="Print verbose amounts detail of the graph generation process.")
GENERATE_PARSER.set_defaults(func=generate_cmd)

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
