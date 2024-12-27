from __future__ import annotations

from abc import ABC
import json
from typing import TYPE_CHECKING

from pagegraph.serialize import ReportBase, to_jsonable

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Union, Sequence, Optional

    from pagegraph.graph import PageGraph
    from pagegraph.types import Url, PageGraphId, PageGraphNodeId


# pylint: disable=too-few-public-methods
class Result:
    tool_version: str
    graph_version: str
    url: Optional[Url]
    report: Union[ReportBase, Sequence[ReportBase]]

    def __init__(self, pg: PageGraph,
                 report: Union[ReportBase, Sequence[ReportBase]]) -> None:
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


def validate_node_id(node_id: PageGraphNodeId) -> bool:
    if node_id[0] != "n":
        raise ValueError(
            f"Node ids must start with a 'n': {node_id}")
    return True

def validate_pg_id(pg_id: PageGraphId) -> bool:
    if pg_id[0] not in ["n", "e"]:
        raise ValueError(
            f"PageGraph element ids start with either 'n' or 'e': {pg_id}")
    return True


class Base(ABC):
    input_path: Path
    debug: bool

    def __init__(self, input_path: Path, debug: bool = False) -> None:
        self.input_path = input_path
        self.debug = debug

    def validate(self) -> bool:
        if not self.input_path.is_file():
            raise ValueError(
                f"Unable to read from input file: {self.input_path.name}")
        return True

    def execute(self) -> Result:
        raise NotImplementedError()

    def format(self, result: Result) -> Optional[str]:
        return result.to_json()
