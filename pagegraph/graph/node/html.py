from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node import Node
from pagegraph.graph.node.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport

if TYPE_CHECKING:
    from pagegraph.graph.requests import RequestChain


class HTMLNode(DOMElementNode, Reportable):

    summary_methods = {
        "tag name": "tag_name"
    }

    def as_html_node(self) -> Optional["HTMLNode"]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def requests(self) -> list["RequestChain"]:
        chains: list["RequestChain"] = []
        for outgoing_edge in self.outgoing_edges():
            if request_start_edge := outgoing_edge.as_request_start_edge():
                request_id = request_start_edge.request_id()
                request_chain = self.pg.request_chain_for_id(request_id)
                chains.append(request_chain)
        return chains
