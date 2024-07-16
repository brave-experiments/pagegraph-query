from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge


if TYPE_CHECKING:
    from pagegraph.types import ParentDomNode, ChildDomNode


class DocumentEdge(Edge):

    def as_document_edge(self) -> Optional[DocumentEdge]:
        return self

    def incoming_node(self) -> ParentDomNode:
        incoming_node = super().incoming_node()
        parent_dom_node = incoming_node.as_parent_dom_node()
        assert parent_dom_node
        return parent_dom_node

    def outgoing_node(self) -> ChildDomNode:
        outgoing_node = super().outgoing_node()
        child_dom_node = outgoing_node.as_child_dom_node()
        assert child_dom_node
        return child_dom_node
