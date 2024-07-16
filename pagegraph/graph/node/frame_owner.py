from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node.abc.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport
from pagegraph.versions import Feature

if TYPE_CHECKING:
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.parser import ParserNode


class FrameOwnerNode(DOMElementNode, Reportable):

    def as_frame_owner_node(self) -> Optional["FrameOwnerNode"]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def child_parser_nodes(self) -> list["ParserNode"]:
        child_parser_nodes = []
        for child_node in self.child_nodes():
            if parser_node := child_node.as_parser_node():
                child_parser_nodes.append(parser_node)
        return child_parser_nodes

    def domroot_nodes(self) -> list["DOMRootNode"]:
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

    def tag_name(self) -> str:
        return self.data()[self.RawAttrs.TAG.value]
