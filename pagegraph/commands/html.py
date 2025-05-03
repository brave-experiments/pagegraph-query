from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

    from pagegraph.serialize import DOMNodeReport
    from pagegraph.types import PageGraphNodeId


@dataclass
class Result(ReportBase):
    elements: list[DOMNodeReport]


class Command(pagegraph.commands.Base):
    frame_filter: Optional[PageGraphNodeId]
    at_serialization: bool
    only_body_content: bool

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
            pagegraph.commands.validate_node_id(self.frame_filter)
        return super().validate()

    def execute(self) -> pagegraph.commands.Result:
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
        return pagegraph.commands.Result(pg, Result(reports))
