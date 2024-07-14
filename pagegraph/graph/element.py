from abc import ABC
from enum import Enum
import sys
from typing import Any, TYPE_CHECKING, Union


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.serialize import JSONAble
    from pagegraph.types import PageGraphId, ElementSummary


class PageGraphElement(ABC):

    class RawAttrs(Enum):
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

    def summary_fields(self) -> "ElementSummary":
        summary: dict[str, "JSONAble"] = {}
        needle_class = self.__class__
        while needle_class != object:
            class_summary_methods = self.__class__.summary_methods
            if class_summary_methods is not None:
                for name, method_name in class_summary_methods.items():
                    func = getattr(self, method_name)
                    result_value = func()
                    if isinstance(result_value, int):
                        summary[name] = result_value
                    else:
                        summary[name] = str(result_value)
            needle_class = needle_class.__bases__[0]
        return summary

    def validate(self) -> bool:
        raise NotImplementedError()

    def data(self) -> dict[str, Any]:
        raise NotImplementedError("Child class must implement 'data'")

    def timestamp(self) -> int:
        return int(self.data()[self.__class__.RawAttrs.TIMESTAMP.value])

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
