from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

    from pagegraph.serialize import RequestChainReport, FrameReport
    from pagegraph.types import PageGraphNodeId


@dataclass
class Result(ReportBase):
    request: RequestChainReport
    frame: FrameReport


class Command(pagegraph.commands.Base):
    frame_nid: Optional[PageGraphNodeId]

    def __init__(self, input_path: Path, frame_nid: Optional[PageGraphNodeId],
                 debug: bool = False) -> None:
        self.frame_nid = frame_nid
        super().__init__(input_path, debug)

    def validate(self) -> None:
        if self.frame_nid:
            pagegraph.commands.validate_node_id(self.frame_nid)
        return super().validate()

    def execute(self) -> pagegraph.commands.Result:
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
        return pagegraph.commands.Result(pg, results)
