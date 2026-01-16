from __future__ import annotations

from abc import ABC
from typing import Optional, TYPE_CHECKING

from pagegraph.graph.element import sort_elements
from pagegraph.graph.node import Node
from pagegraph.versions import Feature

if TYPE_CHECKING:
    from pagegraph.graph.edge.node_create import NodeCreateEdge
    from pagegraph.graph.edge.node_insert import NodeInsertEdge
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.requests import RequestChain
    from pagegraph.serialize import DOMNodeReport, JSONAble
    from pagegraph.types import BlinkId, ActorNode


class DOMElementNode(Node, ABC):

    summary_methods = {
        "tag name": "tag_name"
    }

    def as_dom_element_node(self) -> Optional[DOMElementNode]:
        return self

    def blink_id(self) -> BlinkId:
        return int(self.data()[self.RawAttrs.BLINK_ID.value])

    def to_report(self) -> DOMNodeReport:
        raise NotImplementedError()

    def insertion_edges(self) -> list[NodeInsertEdge]:
        insertion_edges: list[NodeInsertEdge] = []
        for edge in self.incoming_edges():
            if insert_edge := edge.as_insert_edge():
                insertion_edges.append(insert_edge)
        return sort_elements(insertion_edges)

    def insert_edge(self) -> Optional[NodeInsertEdge]:
        """Return the most recent edge describing when this element
        was appended to a document."""
        insertion_edges = self.insertion_edges()
        try:
            return insertion_edges[-1]
        except IndexError:
            return None

    def is_body_content(self) -> bool:
        # Returns True if the element was both 1. in the document
        # at serialization time, and 2. was a child of the <body> element.
        parent_node = self.parent_at_serialization()
        if not parent_node:
            return False
        needle_node: Optional[ParentDOMElementNode] = parent_node
        while needle_node is not None:
            needle_html_node = needle_node.as_html_node()
            if not needle_html_node:
                return False
            if needle_html_node.tag_name() == "BODY":
                return True
            needle_node = needle_html_node.parent_at_serialization()
        return False

    def is_present_at_serialization(self) -> bool:
        parent_node_at_serialization = self.parent_at_serialization()
        return parent_node_at_serialization is not None

    def parent_at_serialization(self) -> Optional[ParentDOMElementNode]:
        if self.pg.feature_check(Feature.DOCUMENT_EDGES):
            for edge in self.incoming_edges():
                if document_edge := edge.as_document_edge():
                    return document_edge.incoming_node()
        else:
            for edge in self.incoming_edges():
                structure_edge = edge.as_structure_edge()
                if not structure_edge:
                    continue
                incoming_node = structure_edge.incoming_node()
                parent_node = incoming_node.as_parent_dom_element_node()
                assert parent_node
                return parent_node
        return None

    def creation_edge(self) -> NodeCreateEdge:
        creation_edge = None
        for edge in self.incoming_edges():
            if creation_edge := edge.as_create_edge():
                break
        assert creation_edge
        return creation_edge

    def creator_node(self) -> ActorNode:
        return self.creation_edge().incoming_node()

    def execution_context(self) -> DOMRootNode:
        """Returns a best effort of what frame / DOMRootNode to associate
        this element with. Since an DOM element can be attached to
        multiple documents / multiple frames, this may not be what you're
        looking for."""
        return (
            self.domroot_for_serialization() or
            self.domroot_for_document() or
            self.domroot_for_creation()
        )

    def domroot_for_creation(self) -> DOMRootNode:
        """Returns the DOMRootNode that is the execution context
        that this element was created in. Node that this could differ
        from the DOMRootNode / frame that the element was inserted into."""
        creation_frame_id = self.creation_edge().frame_id()
        return self.pg.domroot_for_frame_id(creation_frame_id)

    def domroot_for_document(self) -> Optional[DOMRootNode]:
        """Returns the DOMRootNode for the most last document the element
        was attached to. Note that this *does not* mean the this element
        was attached to the document at serialization (since the element
        could have been attached and then removed), *nor* does it mean
        that this was the only document this element was attached to
        (since the element could have been moved between documents)."""
        insert_edge = self.insert_edge()
        if not insert_edge:
            return None
        return insert_edge.domroot_for_frame_id()

    def domroot_from_parent_node_path(self) -> Optional[DOMRootNode]:
        """Tries to follow all chains of nodes that this node was inserted
        as a child of. Its possible that we cannot get to a docroot node
        in this path though (for example, nodes trees created in script
        but not inserted in a document), in which case, we return None."""
        for parent_node in self.parent_html_nodes():
            if domroot_node := parent_node.as_domroot_node():
                return domroot_node
            if html_node := parent_node.as_html_node():
                return html_node.domroot_from_parent_node_path()
        return None

    def domroot_for_serialization(self) -> Optional[DOMRootNode]:
        """Get the DOMRootNode for the document this element is attached
        to at serialization time. Note that this could be `None` (if
        this element is not attached to a document at serialization),
        and could differ from the domroot of the context the element
        was created in (if this element was moved between documents
        during page execution)."""
        current_node = self.parent_at_serialization()
        while current_node:
            if domroot_node := current_node.as_domroot_node():
                return domroot_node
            current_node = current_node.parent_at_serialization()

        parent_node_from_structure = self.domroot_from_parent_node_path()
        if parent_node_from_structure:
            return parent_node_from_structure
        return None

    def parent_html_nodes(self) -> list[ParentDOMElementNode]:
        """Return every node this node was ever inserted under. This can be
        zero nodes (if the node was created but never inserted in the
        document), or more than one node (if the node was moved around the
        document during execution)."""
        parent_html_nodes = []
        for edge in self.incoming_edges():
            if insert_edge := edge.as_insert_edge():
                parent_html_nodes.append(insert_edge.inserted_below_node())
        return parent_html_nodes

    def requests(self) -> list[RequestChain]:
        chains: list[RequestChain] = []
        for outgoing_edge in self.outgoing_edges():
            if request_start_edge := outgoing_edge.as_request_start_edge():
                request_id = request_start_edge.request_id()
                request_chain = self.pg.request_chain_for_id(request_id)
                chains.append(request_chain)
        return chains
