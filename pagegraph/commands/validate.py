from __future__ import annotations

from dataclasses import dataclass

import pagegraph.commands
import pagegraph.graph
from pagegraph.serialize import ReportBase


@dataclass
class Result(ReportBase):
    success: bool


class Command(pagegraph.commands.Base):
    def execute(self) -> pagegraph.commands.Result:
        pg = pagegraph.graph.from_path(self.input_path, True)
        return pagegraph.commands.Result(pg, Result(True))
