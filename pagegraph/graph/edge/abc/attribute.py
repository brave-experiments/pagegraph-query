from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.types import ActorNode


class AttributeEdge(FrameIdAttributedEdge, ABC):

    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT_LOCAL
        "unknown actor",  # Node.Types.UNKNOWN
        "parser",  # TEMP
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML
    ]

    summary_methods = {
        "key": "key",
    }

    def key(self) -> str:
        return self.data()[self.RawAttrs.KEY.value]

    def incoming_node(self) -> ActorNode:
        incoming_node = super().incoming_node()
        actor_node = incoming_node.as_actor_node()
        assert actor_node
        return actor_node

    def outgoing_node(self) -> ParentDOMElementNode:
        outgoing_node = super().outgoing_node()
        node = outgoing_node.as_parent_dom_element_node()
        assert node
        return node
