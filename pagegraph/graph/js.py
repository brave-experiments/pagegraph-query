from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from pagegraph.types import FrameId
from pagegraph.serialize import Reportable, JSInvokeReport

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import JSCallEdge, JSResultEdge
    from pagegraph.graph.node import JSStructureNode, DOMRootNode


class JSCallResult(Reportable):
    call_edge: "JSCallEdge"
    js_structure: "JSStructureNode"
    result_edge: Union["JSResultEdge", None]
    pg: "PageGraph"

    def __init__(self, call_edge: "JSCallEdge",
                 result_edge: Union["JSResultEdge", None]):
        self.call_edge = call_edge
        self.js_structure = call_edge.outgoing_node()
        self.result_edge = result_edge
        self.pg = self.js_structure.pg

    def to_report(self) -> JSInvokeReport:
        report = JSInvokeReport(self.call_edge.args(), None)
        if self.result_edge:
            report.result = self.result_edge.value()
        return report

    def call_context(self) -> "DOMRootNode":
        return self.call_edge.domroot_for_frame_id()

    def receiver_context(self) -> "DOMRootNode":
        receiver_context_frame_id = self.call_edge.frame_id()
        return self.pg.domroot_for_frame_id(receiver_context_frame_id)

    def is_cross_frame_call(self) -> bool:
        return self.call_context() != self.receiver_context()
