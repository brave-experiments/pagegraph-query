from typing import Any, Optional, TYPE_CHECKING
from json import loads, JSONDecodeError

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.graph.node.script import ScriptNode


class JSCallEdge(FrameIdAttributedEdge):

    def args(self) -> Any:
        args_raw = self.data()[Edge.RawAttrs.ARGS.value]
        return_result = None
        try:
            return_result = loads(args_raw)
        except JSONDecodeError:
            return_result = args_raw
        return return_result

    def as_js_call_edge(self) -> Optional["JSCallEdge"]:
        return self

    def incoming_node(self) -> "ScriptNode":
        incoming_node = super().incoming_node()
        script_node = incoming_node.as_script_node()
        assert script_node
        return script_node

    def outgoing_node(self) -> "JSStructureNode":
        outgoing_node = super().outgoing_node()
        js_structure_node = outgoing_node.as_js_structure_node()
        assert js_structure_node
        return js_structure_node
