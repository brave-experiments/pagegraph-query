from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
from pagegraph.cli.validate import is_node_id
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from pathlib import Path
    from typing import Any, Optional

    from pagegraph.serialize import DOMNodeReport
    from pagegraph.types import PageGraphNodeId


@dataclass
class Result(ReportBase):
    elements: list[DOMNodeReport]


class HTMLCommand(CommandBase):
    command_name = "html"
    command_desc = "Print information about the HTML elements in a document."

    frame_filter: Optional[PageGraphNodeId]
    at_serialization: bool
    only_body_content: bool

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = super(HTMLCommand, cls).add_subparser(subparser_handle)
        parser.add_argument(
            "-f", "--frame",
            default=None,
            help="Only include HTML elements that were inserted into the "
                 "document in a given frame (as described by PageGraph node "
                 "ids, in the format 'n##').")
        parser.add_argument(
            "-s", "--at-serialization",
            default=False,
            action="store_true",
            help="If passed, only include HTML elements that were presented "
                 "in the document when the document was serialized (i.e., "
                 "they weren't inserted and then later deleted.).")
        parser.add_argument(
            "-b", "--body-content",
            default=False,
            action="store_true",
            help="Only return elements that appear in the body of the "
                 "document, meaning elements that are a child of the <body> "
                 "element.")
        return parser

    @classmethod
    def from_args(cls, args: Namespace) -> HTMLCommand:
        return HTMLCommand(args.input, args.frame, args.at_serialization,
                           args.body_content, args.debug)

    # pylint: disable=too-many-positional-arguments
    def __init__(self, input_path: Path,
                 frame_filter: Optional[PageGraphNodeId],
                 at_serialization: bool, only_body_content: bool,
                 debug: bool) -> None:
        self.frame_filter = frame_filter
        self.at_serialization = at_serialization
        self.only_body_content = only_body_content
        super().__init__(input_path, debug)

    def validate(self) -> None:
        if self.frame_filter:
            is_node_id(self.frame_filter)
        return super().validate()

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        dom_nodes = pg.dom_nodes()
        reports = []
        for node in dom_nodes:
            if self.frame_filter:
                domroot_for_insertion = node.domroot_for_document()
                if not domroot_for_insertion:
                    continue
                if self.frame_filter != domroot_for_insertion.pg_id():
                    continue
            if self.at_serialization and not node.is_present_at_serialization():
                continue
            if self.only_body_content and not node.is_body_content():
                continue
            reports.append(node.to_report())
        return CommandResult(pg, Result(reports))
