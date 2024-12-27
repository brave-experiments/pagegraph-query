from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Union

    from pagegraph.serialize import ScriptReport, BasicReport, JSCallResultReport
    from pagegraph.types import PageGraphId


@dataclass
class Result(ReportBase):
    caller: Union[ScriptReport, BasicReport]
    call: JSCallResultReport


class Command(pagegraph.commands.Base):
    frame_nid: Optional[PageGraphId]
    cross_frame: bool
    method: Optional[str]
    pg_id: Optional[PageGraphId]

    def __init__(self, input_path: Path, frame_nid: Optional[PageGraphId],
                 cross_frame: bool, method: Optional[str],
                 pg_id: Optional[PageGraphId], debug: bool = False) -> None:
        self.frame_nid = frame_nid
        self.cross_frame = cross_frame
        self.method = method
        self.pg_id = pg_id
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
        return pagegraph.commands.Result(pg, reports)
