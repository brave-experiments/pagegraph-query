from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
from pagegraph.cli.validate import is_node_id, is_pg_id
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from pathlib import Path
    from typing import Any, Optional, Union

    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.serialize import ScriptReport, BasicReport, JSCallResultReport
    from pagegraph.types import PageGraphId


@dataclass
class Result(ReportBase):
    caller: Union[ScriptReport, BasicReport]
    call: JSCallResultReport


class JSCallsCommand(CommandBase):
    command_name = "js-calls"
    command_desc = "Print information about JS calls made during page execution."

    frame_nid: Optional[PageGraphId]
    cross_frame: bool
    method: Optional[str]
    pg_id: Optional[PageGraphId]

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = super(JSCallsCommand, cls).add_subparser(subparser_handle)
        parser.add_argument(
            "-f", "--frame",
            default=None,
            help="Only include JS calls made by code running in this frame's "
                 "context (as described by PageGraph node ids, in the format "
                 "'n##'). Note that this filters on the calling frame context, "
                 "not the receiving frame context, which will differ in some "
                 "cases, such as same-origin cross-frame calls.")
        parser.add_argument(
            "-c", "--cross",
            default=False,
            action="store_true",
            help="Only include JS calls where the calling frame context and "
                 "the receiving frame context differ.")
        parser.add_argument(
            "-m", "--method",
            default=None,
            help="Only include JS calls where the function or method being "
                 "called includes this value as a substring.")
        parser.add_argument(
            "-i", "--id",
            default=None,
            help="If provided, only print information about JS calls made by "
                 "the Script node with the given ID "
                 "(as described by PageGraph node ids, in the format 'n##').")
        return parser

    @classmethod
    def from_args(cls, args: Namespace) -> JSCallsCommand:
        return JSCallsCommand(args.input, args.frame, args.cross, args.method,
                              args.id, args.debug)

    # pylint: disable=too-many-positional-arguments
    def __init__(self, input_path: Path, frame_nid: Optional[PageGraphId],
                 cross_frame: bool, method: Optional[str],
                 pg_id: Optional[PageGraphId], debug: bool = False) -> None:
        self.frame_nid = frame_nid
        self.cross_frame = cross_frame
        self.method = method
        self.pg_id = pg_id
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

        domroot_node: Optional[DOMRootNode] = None
        if self.frame_nid:
            domroot_node = pg.node(self.frame_nid).as_domroot_node()
            if not domroot_node:
                raise ValueError("The PageGraph id provided is not " +
                    f"a DOMRootNode, nid={self.frame_nid}")
        assert domroot_node

        can_do_fast_path = (domroot_node is not None and
            not self.cross_frame and not self.pg_id and not self.method)
        if can_do_fast_path:
            for call_edge in pg.js_call_edges():
                if call_edge.frame_id() != domroot_node.frame_id():
                    continue
                js_result = call_edge.call_result()
                result_report = js_result.to_report()
                script_node = js_result.call.incoming_node()
                script_report = script_node.to_report()
                reports.append(Result(script_report, result_report))
            return CommandResult(pg, reports)

        js_structure_nodes = pg.js_structure_nodes()
        for js_node in js_structure_nodes:
            if self.method and self.method not in js_node.name():
                continue

            for call_result in js_node.call_results():
                if (self.frame_nid and
                        call_result.call_context().pg_id() != self.frame_nid):
                    continue
                if (self.cross_frame and
                        not call_result.is_cross_frame_call()):
                    continue
                script_node = call_result.call.incoming_node()
                if self.pg_id and script_node.pg_id() != self.pg_id:
                    continue
                call_report = call_result.to_report()
                script_report = script_node.to_report()
                reports.append(Result(script_report, call_report))
        return CommandResult(pg, reports)
