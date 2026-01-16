from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pagegraph.serialize import ReportBase, to_jsonable

if TYPE_CHECKING:
    from typing import Sequence, Optional

    from pagegraph.graph import PageGraph
    from pagegraph.types import Url


# pylint: disable=too-few-public-methods
class CommandResult:
    tool_version: str
    graph_version: str
    url: Optional[Url]
    report: ReportBase | Sequence[ReportBase]

    def __init__(self, pg: PageGraph,
                 report: ReportBase | Sequence[ReportBase]) -> None:
        self.tool_version = str(pg.tool_version)
        self.graph_version = str(pg.graph_version)
        self.url = pg.url
        self.report = report

    def to_json(self) -> str:
        data = {
            "meta": {
                "versions": {
                    "tool": self.tool_version,
                    "graph": self.graph_version
                },
                "url": self.url
            },
            "report": to_jsonable(self.report)
        }
        return json.dumps(data)
