from __future__ import annotations

from typing import cast, Optional, TYPE_CHECKING
from json import loads, JSONDecodeError

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge
from pagegraph.serialize import JSONAble

if TYPE_CHECKING:
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.types import JSCallingNode


class JSResultEdge(FrameIdAttributedEdge):

    def value(self) -> JSONAble:
        value_raw = self.data()[Edge.RawAttrs.VALUE.value]
        try:
            return cast(JSONAble, loads(value_raw))
        except JSONDecodeError:
            return value_raw

    def as_js_result_edge(self) -> Optional[JSResultEdge]:
        return self

    def outgoing_node(self) -> JSCallingNode:
        outgoing_node = super().outgoing_node()
        executor_node = outgoing_node.as_executor_node()
        assert executor_node
        return executor_node

    def incoming_node(self) -> JSStructureNode:
        incoming_node = super().incoming_node()
        js_structure_node = incoming_node.as_js_structure_node()
        assert js_structure_node
        return js_structure_node
