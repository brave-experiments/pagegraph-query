import sys
from typing import Any, TYPE_CHECKING, Union

from pagegraph.types import PageGraphId

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph


class PageGraphElement:

    # Class properties
    summary_methods: Union[dict[str, str], None] = None

    # Instance properties
    pg: "PageGraph"
    _id: PageGraphId

    def __init__(self, graph: "PageGraph", pg_id: PageGraphId):
        self.pg = graph
        self._id = pg_id

    def int_id(self) -> int:
        return int(self._id[1:])

    def id(self) -> PageGraphId:
        return self._id

    def summary_fields(self) -> Union[None, dict[str, str]]:
        if self.__class__.summary_methods is None:
            return None
        summary: dict[str, str] = {}
        for name, method_name in self.__class__.summary_methods.items():
            func = getattr(self, method_name)
            summary[name] = str(func())
        return summary

    def validate(self) -> bool:
        raise NotImplementedError()

    def data(self) -> dict[str, Any]:
        raise NotImplementedError("Child class must implement 'data'")

    def timestamp(self) -> int:
        raise NotImplementedError("Child class must implement 'timestamp'")

    def describe(self) -> str:
        raise NotImplementedError("Child class must implement 'describe'")

    def build_caches(self) -> None:
        pass

    def throw(self, desc: str) -> None:
        sys.stderr.write(self.describe())
        sys.stderr.write("\n")
        raise Exception(desc)
