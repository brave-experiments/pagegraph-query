from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import networkx

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Union





    from pagegraph.serialize import ScriptReport, BasicReport, FrameReport
    from pagegraph.types import PageGraphId


@dataclass
class BytesWrittenResult(ReportBase):
    num_bytes: int


class Command(pagegraph.commands.Base):
    pg_id: PageGraphId
    depth: int
    output_path: Optional[Path]

    def __init__(self, input_path: Path, pg_id: PageGraphId, depth: int,
                 output_path: Optional[Path], debug: bool) -> None:
        self.pg_id = pg_id
        self.depth = depth
        self.output_path = output_path
        super().__init__(input_path, debug)

    def validate(self) -> None:
        if self.pg_id:
            pagegraph.commands.validate_pg_id(self.pg_id)
        return super().validate()

    def execute(self) -> pagegraph.commands.Result:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        if self.pg_id.startswith("n"):
            target_node = pg.node(self.pg_id)
            if self.output_path:
                subgraph = target_node.subgraph(self.depth)
                text = "\n".join(list(networkx.generate_graphml(subgraph)))
                num_bytes = self.output_path.write_text(text)
                report = BytesWrittenResult(num_bytes)
                return pagegraph.commands.Result(pg, report)

            node_report = target_node.to_node_report(self.depth)
            return pagegraph.commands.Result(pg, node_report)

        target_edge = pg.edge(self.pg_id)
        if self.output_path:
            subgraph = target_edge.subgraph(self.depth)
            text = "\n".join(list(networkx.generate_graphml(subgraph)))
            num_bytes = self.output_path.write_text(text)
            report = BytesWrittenResult(num_bytes)
            return pagegraph.commands.Result(pg, report)

        edge_report = target_edge.to_edge_report(self.depth)
        return pagegraph.commands.Result(pg, edge_report)
