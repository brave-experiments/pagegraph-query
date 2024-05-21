from abc import abstractmethod
import sys
from typing import Any, Dict, TYPE_CHECKING

from pagegraph.types import PageGraphId

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

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def data(self) -> Dict[str, Any]:
        raise NotImplementedError("Child class must implement 'data'")

    @abstractmethod
    def timestamp(self) -> int:
        raise NotImplementedError("Child class must implement 'timestamp'")

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError("Child class must implement 'describe'")

    def build_caches(self) -> None:
        pass

    def throw(self, desc: str) -> None:
        sys.stderr.write(self.describe())
        sys.stderr.write("\n")
        raise Exception(desc)
