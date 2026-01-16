from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
from pagegraph.cli.validate import is_node_id
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from typing import Any, Optional

    from pagegraph.serialize import RequestChainReport, FrameReport
    from pagegraph.types import PageGraphNodeId


@dataclass
class Result(ReportBase):
    request: RequestChainReport
    frame: FrameReport


class RequestsCommand(CommandBase):
    command_name = "requests"
    command_desc = "Print information about requests made during execution."

    frame_nid: Optional[PageGraphNodeId]

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = super(RequestsCommand, cls).add_subparser(subparser_handle)
        parser.add_argument(
            "-f", "--frame",
            default=None,
            help="Only print information about requests made in a specific "
                 "frame (as described by PageGraph node ids, in the format "
                 "'n##').")
        return parser

    @classmethod
    def from_args(cls, args: Namespace) -> RequestsCommand:
        return RequestsCommand(args.input, args.frame, args.debug)

    def __init__(self, input_path: Path, frame_nid: Optional[PageGraphNodeId],
                 debug: bool = False) -> None:
        self.frame_nid = frame_nid
        super().__init__(input_path, debug)

    def validate(self) -> None:
        if self.frame_nid:
            is_node_id(self.frame_nid)
        return super().validate()

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        results: list[Result] = []

        for request_start_edge in pg.request_start_edges():
            request_frame_id = request_start_edge.frame_id()
            request_frame = pg.domroot_for_frame_id(request_frame_id)

            if self.frame_nid and request_frame.pg_id() != self.frame_nid:
                continue
            request_id = request_start_edge.request_id()
            request_chain = pg.request_chain_for_id(request_id)

            request_chain_report = request_chain.to_report()
            frame_report = request_frame.to_report()
            report = Result(request_chain_report, frame_report)
            results.append(report)
        return CommandResult(pg, results)
