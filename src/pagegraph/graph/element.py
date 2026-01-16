from __future__ import annotations

from abc import ABC
from enum import Enum
import sys
from typing import TYPE_CHECKING

from networkx import MultiDiGraph

if TYPE_CHECKING:
    from typing import Any, Optional, Union

    from pagegraph.graph import PageGraph
    from pagegraph.serialize import JSONAble
    from pagegraph.types import PageGraphId, ElementSummary


class PageGraphElement(ABC):

    class RawAttrs(Enum):
        TIMESTAMP = "timestamp"
        # Child classes should implement this enum with the PageGraph
        # attributes that correspond to node and edge attributes.

    # Class properties

    # Inheriting classes can define this property (at the
    # class level) to include a simple description of the node or edge's
    # attributes in different reports and summaries. Inheriting classes
    # that implement should define a dict, mapping "descriptive name of the
    # value, for use in a JSON dict" to "name of the method to call to get
    # that value".
    summary_methods: Union[dict[str, str], None] = None

    # Instance properties

    # Reference to the PageGraph instance that this graph element is a member
    # of (i.e., the graph this node or edge is a member of.)
    pg: PageGraph

    # The ID of this element in the graph, as defined by the GraphML spec.
    # This will either be "e<int>" or "n<int>", for edges and notes,
    # respectively.
    _id: PageGraphId

    def __init__(self, graph: PageGraph, pg_id: PageGraphId):
        self.pg = graph
        self._id = pg_id

    def __hash__(self) -> int:
        return hash(('<pagegraph>', self._id))

    def id(self) -> int:
        return int(self._id[1:])

    def pg_id(self) -> PageGraphId:
        return self._id

    def summary_fields(self) -> ElementSummary:
        summary: dict[str, JSONAble] = {}
        needle_class = self.__class__
        while needle_class != object and needle_class is not ABC:
            class_summary_methods = needle_class.summary_methods
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

    def validate(self) -> None:
        # Inheriting classes should implement this method to perform correctness
        # checks and similar activities. This is intended as a check that
        # the `pagegraph-query` code correctly understands and abstracts the
        # pagegraph-generated GraphML data.
        raise NotImplementedError()

    def data(self) -> dict[str, Any]:
        raise NotImplementedError()

    def timestamp(self) -> int:
        return int(self.data()[self.__class__.RawAttrs.TIMESTAMP.value])

    def describe(self) -> str:
        # Inheriting classes must implement this method. Its used in debugging
        # and similar situations to describe the node or edge in STDERR
        # and equiv situations.
        raise NotImplementedError()

    def build_caches(self) -> None:
        # Inheriting classes should implement this to perform any
        # expensive, one-time operations. This method is guaranteed to be
        # called after the parent PageGraph graph element is initialized, but
        # before any other, query-related methods are called.
        pass

    def subgraph(self, depth: int = 1) -> MultiDiGraph:
        """Returns a subgraph of the underlying networkx MultiDiGraph,
        that depicts the subgraph, starting from this node or edge, and
        spreading out with the given depth."""

        # This is implemented in the Node and Edge subclasses, with the Edge
        # implementation just calling to the Node implementation.
        raise NotImplementedError()

    def throw(self, desc: str,
              context_exception: Optional[Exception] = None) -> None:
        sys.stderr.write(self.describe())
        sys.stderr.write("\n")
        if context_exception:
            raise ValueError(desc) from context_exception
        raise ValueError(desc)


def sort_elements(elements: list[Any]) -> list[Any]:
    return sorted(elements, key=lambda x: x.id())
