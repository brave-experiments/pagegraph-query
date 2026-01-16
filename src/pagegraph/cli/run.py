from __future__ import annotations

import argparse
import sys

from pagegraph.cli.commands.element import ElementCommand
from pagegraph.cli.commands.html import HTMLCommand
from pagegraph.cli.commands.js_calls import JSCallsCommand
from pagegraph.cli.commands.requests import RequestsCommand
from pagegraph.cli.commands.scripts import ScriptsCommand
from pagegraph.cli.commands.subframes import SubFramesCommand
from pagegraph.cli.commands.unknown import UnknownCommand
from pagegraph.cli.commands.validate import ValidateCommand
from pagegraph import __version__


def run() -> int:
    parser = argparse.ArgumentParser(
        prog="PageGraph Query",
        description="Extracts information about a Web page's execution from "
                    "a PageGraph recordings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}")
    parser.add_argument("--debug", action="store_true", default=False)

    subparsers = parser.add_subparsers(required=True)
    ElementCommand.add_subparser(subparsers)
    HTMLCommand.add_subparser(subparsers)
    JSCallsCommand.add_subparser(subparsers)
    RequestsCommand.add_subparser(subparsers)
    ScriptsCommand.add_subparser(subparsers)
    SubFramesCommand.add_subparser(subparsers)
    UnknownCommand.add_subparser(subparsers)
    ValidateCommand.add_subparser(subparsers)

    args = parser.parse_args()
    try:
        result = args.command_cls.run(args)
        print(result)
        return 0
    except ValueError as e:
        print(f"Invalid argument: {e}", file=sys.stderr)
        return 1
