from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
from pagegraph.cli.validate import is_node_id, is_pg_id
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from typing import Any, Optional, Union

    from pagegraph.serialize import ScriptReport, BasicReport, FrameReport
    from pagegraph.types import PageGraphId, PageGraphNodeId


@dataclass
class Result(ReportBase):
    script: ScriptReport
    frame: Optional[FrameReport] = None


class ScriptsCommand(CommandBase):
    command_name = "scripts"
    command_desc = "Print information about JS execution during page execution."

    frame_nid: Optional[PageGraphNodeId]
    pg_id: Optional[PageGraphId]
    include_source: bool
    omit_executors: bool

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = super(ScriptsCommand, cls).add_subparser(subparser_handle)
        parser.add_argument(
            "-i", "--id",
            default=None,
            help="If provided, only print information about JS units with the "
                 "given ID (as described by PageGraph node ids, in the format "
                 "'n##').")
        parser.add_argument(
            "-s", "--source",
            default=False,
            action="store_true",
            help="If included, also include script source in each report.")
        parser.add_argument(
            "-f", "--frame",
            default=None,
            help="Only include JS code units executed in a particular frame "
                "context (as described by PageGraph node ids, in the format "
                "'n##'). Note that this filters on the calling frame context, "
                "not the receiving frame context, which will differ in some "
                "cases, such as same-origin cross-frame calls.")
        parser.add_argument(
            "-o", "--omit-executors",
            default=False,
            action="store_true",
            help="If included, do not append information about why or how "
                 "each script was executed.")
        return parser

    @classmethod
    def from_args(cls, args: Namespace) -> ScriptsCommand:
        return ScriptsCommand(args.input, args.frame, args.id, args.source,
                              args.omit_executors, args.debug)

    # pylint: disable=too-many-positional-arguments
    def __init__(self, input_path: Path, frame_nid: Optional[PageGraphNodeId],
                 pg_id: Optional[PageGraphId], include_source: bool,
                 omit_executors: bool, debug: bool) -> None:
        self.frame_nid = frame_nid
        self.pg_id = pg_id
        self.include_source = include_source
        self.omit_executors = omit_executors
        super().__init__(input_path, debug)

    def validate(self) -> None:
        if self.frame_nid:
            is_node_id(self.frame_nid)
        if self.pg_id:
            is_pg_id(self.pg_id)
        return super().validate()

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        reports: list[Result] = []
        for script_node in pg.script_local_nodes():
            if self.pg_id and script_node.pg_id() != self.pg_id:
                continue

            script_report = script_node.to_report(self.include_source)
            report = Result(script_report)

            frame_id = script_node.execute_edge().frame_id()
            if self.frame_nid and ("n" + str(frame_id)) != self.frame_nid:
                continue
            frame_report = pg.domroot_for_frame_id(frame_id).to_report()
            report.frame = frame_report

            if self.omit_executors:
                report.script.executor = None
            reports.append(report)
        return CommandResult(pg, reports)
