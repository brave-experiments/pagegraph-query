from __future__ import annotations

from dataclasses import dataclass

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase


@dataclass
class Result(ReportBase):
    count: int


class Command(pagegraph.commands.Base):
    def execute(self) -> pagegraph.commands.Result:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        count = 0
        unknown_node = pg.unknown_node()
        if unknown_node:
            count = len(list(unknown_node.outgoing_edges()))
        return pagegraph.commands.Result(pg, Result(count))
