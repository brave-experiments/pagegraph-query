from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Union

    from pagegraph.serialize import ScriptReport, BasicReport, FrameReport
    from pagegraph.types import PageGraphId, PageGraphNodeId


@dataclass
class Result(ReportBase):
    script: ScriptReport
    frame: Optional[FrameReport] = None


class Command(pagegraph.commands.Base):
    frame_nid: Optional[PageGraphNodeId]
    pg_id: Optional[PageGraphId]
    include_source: bool
    omit_executors: bool

    def __init__(self, input_path: Path, frame_nid: Optional[PageGraphNodeId],
                 pg_id: Optional[PageGraphId], include_source: bool,
                 omit_executors: bool, debug: bool) -> None:
        self.frame_nid = frame_nid
        self.pg_id = pg_id
        self.include_source = include_source
        self.omit_executors = omit_executors
        super().__init__(input_path, debug)

    def validate(self) -> bool:
        if self.frame_nid:
            pagegraph.commands.validate_node_id(self.frame_nid)
        if self.pg_id:
            pagegraph.commands.validate_pg_id(self.pg_id)
        return super().validate()

    def execute(self) -> pagegraph.commands.Result:
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
        return pagegraph.commands.Result(pg, reports)
