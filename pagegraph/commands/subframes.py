from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase
from pagegraph.types import PartyFilterOption

if TYPE_CHECKING:
    from pathlib import Path

    from pagegraph.serialize import DOMElementReport, FrameReport


@dataclass
class Result(ReportBase):
    parent_frame: FrameReport
    iframe: DOMElementReport
    child_frames: list[FrameReport]


class Command(pagegraph.commands.Base):

    def __init__(self, input_path: Path, local_only: bool,
                 party_filter: PartyFilterOption, debug: bool = False) -> None:
        self.local_only = local_only
        self.party_filter = party_filter
        super().__init__(input_path, debug)

    def execute(self) -> pagegraph.commands.Result:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        results: list[Result] = []
        for iframe_node in pg.iframe_nodes():
            if (self.local_only and
                not iframe_node.is_security_origin_inheriting()):
                continue

            child_domroot_nodes = iframe_node.child_domroot_nodes()
            if (self.party_filter != PartyFilterOption.NONE and
                    len(child_domroot_nodes) == 0):
                continue

            if (self.party_filter == PartyFilterOption.FIRST_PARTY and
                    iframe_node.is_third_party_to_root()):
                continue

            if (self.party_filter == PartyFilterOption.THIRD_PARTY and
                    not iframe_node.is_third_party_to_root()):
                continue

            parent_frame_report = iframe_node.execution_context().to_report()
            iframe_elm_report = iframe_node.to_report()
            child_frame_reports: list[FrameReport] = []
            for child_domroot in child_domroot_nodes:
                child_frame_reports.append(child_domroot.to_report())

            subframe_report = Result(parent_frame_report, iframe_elm_report,
                                     child_frame_reports)
            results.append(subframe_report)
        return pagegraph.commands.Result(pg, results)
