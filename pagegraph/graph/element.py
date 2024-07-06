from abc import ABC
from enum import StrEnum
import sys
from typing import Any, TYPE_CHECKING, Union


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.types import PageGraphId


class PageGraphElement(ABC):

    class RawAttrs(StrEnum):
        TIMESTAMP = "timestamp"
        # Child classes should implement this enum with the PageGraph
        # attributes that correspond to node and edge attributes.

    # Class properties
    summary_methods: Union[dict[str, str], None] = None

    # Instance properties
    pg: "PageGraph"
    _id: "PageGraphId"

    def __init__(self, graph: "PageGraph", pg_id: "PageGraphId"):
        self.pg = graph
        self._id = pg_id

    def __hash__(self) -> int:
        return hash(('<pagegraph>', self._id))

    def id(self) -> int:
        return int(self._id[1:])

    def pg_id(self) -> "PageGraphId":
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
        return int(self.data()[self.__class__.RawAttrs.TIMESTAMP])

    def describe(self) -> str:
        raise NotImplementedError("Child class must implement 'describe'")

    def build_caches(self) -> None:
        pass

    def throw(self, desc: str) -> None:
        sys.stderr.write(self.describe())
        sys.stderr.write("\n")
        raise ValueError(desc)


def sort_elements(elements: list[Any]) -> list[Any]:
    return sorted(elements, key=lambda x: x.id())
