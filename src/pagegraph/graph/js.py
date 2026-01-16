from __future__ import annotations

from typing import TYPE_CHECKING, Union

from pagegraph.serialize import Reportable, JSCallResultReport

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge.js_call import JSCallEdge
    from pagegraph.graph.edge.js_result import JSResultEdge
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.serialize import JSONAble


class JSCallResult(Reportable):
    call: JSCallEdge
    structure: JSStructureNode
    result: Union[JSResultEdge, None]
    pg: PageGraph

    def __init__(self, call_edge: JSCallEdge,
                 result_edge: Union[JSResultEdge, None]):
        self.call = call_edge
        self.structure = call_edge.outgoing_node()
        self.result = result_edge
        self.pg = self.structure.pg

    def pretty_print(self) -> str:
        msg = self.structure.name() + f"({str(self.call.args())})"
        if self.result:
            msg += " -> " + str(self.result.value())
        return msg

    def args(self) -> JSONAble:
        return self.call.args()

    def return_value(self) -> JSONAble:
        if not self.result:
            return None
        return self.result.value()

    def to_report(self) -> JSCallResultReport:
        call_context = self.call_context()
        receiver_context = self.receiver_context()

        execution_context_report = None
        if call_context != receiver_context:
            execution_context_report = receiver_context.to_report()

        report = JSCallResultReport(self.structure.name(), self.args(),
            self.return_value(), call_context.to_report(), execution_context_report)
        return report

    def call_context(self) -> DOMRootNode:
        return self.call.domroot_for_frame_id()

    def receiver_context(self) -> DOMRootNode:
        receiver_context_frame_id = self.call.frame_id()
        return self.pg.domroot_for_frame_id(receiver_context_frame_id)

    def is_cross_frame_call(self) -> bool:
        return self.call_context() != self.receiver_context()
