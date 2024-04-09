import sys
from typing import Any, Dict, TYPE_CHECKING

from pagegraph.graph.types import PageGraphId
if TYPE_CHECKING:
    from pagegraph.graph import PageGraph



class PageGraphElement:

    pg: "PageGraph"
    _id: PageGraphId

    def __init__(self, graph: "PageGraph", pg_id: PageGraphId):
        self.pg = graph
        self._id = pg_id

    def int_id(self) -> int:
        return int(self._id[1:])

    def id(self) -> PageGraphId:
        return self._id

    def data(self) -> Dict[str, Any]:
        raise NotImplementedError("Child class must implement 'data'")

    def timestamp(self) -> int:
        raise NotImplementedError("Child class must implement 'timestamp'")

    def describe(self) -> str:
        raise NotImplementedError("Child class must implement 'describe'")

    def throw(self, desc: str) -> None:
        sys.stderr.write(self.describe())
        sys.stderr.write("\n")
        raise Exception(desc)
