from typing import Any, Optional, TYPE_CHECKING
from json import loads, JSONDecodeError

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.graph.node.script import ScriptNode


class JSResultEdge(FrameIdAttributedEdge):

    def value(self) -> Any:
        value_raw = self.data()[Edge.RawAttrs.VALUE.value]
        try:
            return loads(value_raw)
        except JSONDecodeError:
            return value_raw

    def as_js_result_edge(self) -> Optional["JSResultEdge"]:
        return self

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        script_node = outgoing_node.as_script_node()
        assert script_node
        return script_node

    def incoming_node(self) -> "JSStructureNode":
        incoming_node = super().incoming_node()
        js_structure_node = incoming_node.as_js_structure_node()
        assert js_structure_node
        return js_structure_node