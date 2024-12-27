from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport
from pagegraph.urls import are_urls_same_site
from pagegraph.versions import Feature

if TYPE_CHECKING:
    from pagegraph.graph.edge.cross_dom import CrossDOMEdge
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.parser import ParserNode


class FrameOwnerNode(ParentDOMElementNode, Reportable):

    def as_frame_owner_node(self) -> Optional[FrameOwnerNode]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def child_parser_nodes(self) -> list[ParserNode]:
        child_parser_nodes = []
        for child_node in self.child_nodes():
            if parser_node := child_node.as_parser_node():
                child_parser_nodes.append(parser_node)
        return child_parser_nodes

    def child_domroot_nodes(self) -> list[DOMRootNode]:
        domroots = []
        if self.pg.feature_check(Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS):
            for edge in self.outgoing_edges():
                if cross_dom_edge := edge.as_cross_dom_edge():
                    node = cross_dom_edge.outgoing_node().as_domroot_node()
                    assert node
                    domroots.append(node)
        else:
            for parser_node in self.child_parser_nodes():
                nodes = list(parser_node.domroots())
                domroots_sorted = sorted(nodes, key=lambda x: x.id())
                for domroot_node in domroots_sorted:
                    domroots.append(domroot_node)
        return domroots

    def is_security_origin_inheriting(self) -> bool:
        """Checks if all the domroots that this frame has displayed have
        origins that cause the security origin to be inherited."""
        for child_domroot_node in self.child_domroot_nodes():
            if not child_domroot_node.is_security_origin_inheriting():
                return False
        return True

    def is_third_party_to_root(self) -> bool:
        """Whether this element ever contained a document that was third-party
        relative to the top-level document in the page."""
        top_level_url = self.pg.url
        if not top_level_url:
            return False
        for child_domroot_node in self.child_domroot_nodes():
            child_security_origin = child_domroot_node.security_origin()
            if not child_security_origin:
                continue
            if not are_urls_same_site(top_level_url, child_security_origin):
                return True
        return False

    def domroot_node(self) -> DOMRootNode:
        """Returns the last domroot node that was executed in this frame
        owner."""
        domroot_nodes: list[DOMRootNode] = []
        for edge in self.outgoing_edges():
            if cross_dom_edge := edge.as_cross_dom_edge():
                outgoing_node = cross_dom_edge.outgoing_node()
                if domroot_node := outgoing_node.as_domroot_node():
                    domroot_nodes.append(domroot_node)
        return sorted(domroot_nodes, key=lambda x: x.id())[-1]
