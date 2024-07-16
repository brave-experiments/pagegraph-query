from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from json import loads, JSONDecodeError

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.js import JSCallResult
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.graph.node.script_local import ScriptLocalNode
    from pagegraph.serialize import JSONAble
    from pagegraph.types import JSCallingNode


class JSCallEdge(FrameIdAttributedEdge):

    def args(self) -> JSONAble:
        args_raw = self.data()[Edge.RawAttrs.ARGS.value]
        return_result = None
        try:
            return_result = loads(args_raw)
        except JSONDecodeError:
            return_result = args_raw
        return return_result

    def as_js_call_edge(self) -> Optional[JSCallEdge]:
        return self

    def incoming_node(self) -> JSCallingNode:
        incoming_node = super().incoming_node()
        executor_node = incoming_node.as_executor_node()
        assert executor_node
        return executor_node

    def outgoing_node(self) -> JSStructureNode:
        outgoing_node = super().outgoing_node()
        js_structure_node = outgoing_node.as_js_structure_node()
        assert js_structure_node
        return js_structure_node

    def call_result(self) -> JSCallResult:
        return self.outgoing_node().call_result(self)
