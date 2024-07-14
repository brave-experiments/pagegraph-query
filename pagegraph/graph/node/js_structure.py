from typing import cast, Optional, TYPE_CHECKING
from itertools import chain

from pagegraph.graph.node import Node
from pagegraph.serialize import Reportable
from pagegraph.graph.js import JSCallResult
from pagegraph.serialize import JSStructureReport

if TYPE_CHECKING:
    from pagegraph.graph.edge.js_call import JSCallEdge
    from pagegraph.graph.edge.js_result import JSResultEdge

class JSStructureNode(Node, Reportable):
    __cached_call_map: dict["JSCallEdge", "JSCallResult"] = {}

    def to_report(self) -> "JSStructureReport":
        return JSStructureReport(self.name(), self.type_name())

    def as_js_structure_node(self) -> Optional["JSStructureNode"]:
        return self

    def name(self) -> str:
        return self.data()[self.RawAttrs.METHOD.value]

    def build_caches(self) -> None:
        js_calls = self.incoming_edges()
        js_results = self.outgoing_edges()
        calls_and_results_unsorted = list(chain(js_calls, js_results))
        calls_and_results = sorted(
            calls_and_results_unsorted, key=lambda x: x.id())

        if self.pg.debug:
            num_calls = len(list(js_calls))
            num_results = len(list(js_results))
            if num_results > num_calls:
                self.throw("Found more results than calls to this builtin, "
                            f"calls={num_calls}, results={num_results}")

        last_edge = calls_and_results[0]
        for edge in calls_and_results[1:]:
            if edge.as_js_result_edge() is not None:
                if last_edge.as_js_result_edge() is not None:
                    self.throw("Found two adjacent result edges: "
                                f"{last_edge.pg_id()} and {edge.pg_id()}")
            last_edge = edge

        last_call_result = None
        for edge in calls_and_results:
            if js_call_edge := edge.as_js_call_edge():
                a_call_result = JSCallResult(js_call_edge, None)
                last_call_result = a_call_result
                self.__cached_call_map[js_call_edge] = a_call_result
            elif js_result_edge := edge.as_js_result_edge():
                assert last_call_result
                last_call_result.result = js_result_edge
                last_call_result = None
        super().build_caches()

    def call_results(self) -> list["JSCallResult"]:
        return list(self.__cached_call_map.values())

    def call_result(self, edge: "JSCallEdge") -> "JSCallResult":
        try:
            return self.__cached_call_map[edge]
        except KeyError as exc:
            msg = f"Unable to find call {edge}"
            raise ValueError(msg) from exc

    def incoming_edges(self) -> list["JSCallEdge"]:
        return cast(list["JSCallEdge"], super().incoming_edges())

    def outgoing_edges(self) -> list["JSResultEdge"]:
        return cast(list["JSResultEdge"], super().outgoing_edges())
