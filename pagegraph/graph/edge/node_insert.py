from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.graph.node.abc.dom_element import DOMElementNode
    from pagegraph.types import ChildDomNode, BlinkId


class NodeInsertEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT_LOCAL
        "unknown actor",  # Node.Types.UNKNOWN
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML
        "text node",  # Node.Types.TEXT_NODE
    ]

    def as_insert_edge(self) -> Optional[NodeInsertEdge]:
        return self

    def inserted_before_blink_id(self) -> Optional[BlinkId]:
        value = self.data()[Edge.RawAttrs.BEFORE_BLINK_ID.value]
        if value:
            return int(value)
        return None

    def inserted_before_node(self) -> Optional[DOMElementNode]:
        blink_id = self.inserted_before_blink_id()
        if not blink_id:
            return None
        node = self.pg.node_for_blink_id(blink_id)
        return node

    def inserted_below_blink_id(self) -> BlinkId:
        return int(self.data()[Edge.RawAttrs.PARENT_BLINK_ID.value])

    def inserted_below_node(self) -> ParentDOMElementNode:
        blink_id = self.inserted_below_blink_id()
        node = self.pg.node_for_blink_id(blink_id)
        parent_node = node.as_parent_dom_element_node()
        assert parent_node
        return parent_node

    def inserted_node(self) -> ChildDomNode:
        node = self.outgoing_node()
        child_dom_node = node.as_child_dom_node()
        assert child_dom_node
        return child_dom_node
