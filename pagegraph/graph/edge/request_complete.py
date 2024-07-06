from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.request_response import RequestResponseEdge

if TYPE_CHECKING:
    from pagegraph.types import RequesterNode


class RequestCompleteEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    summary_methods = {
        "size": "size",
        "hash": "hash",
    }

    def as_request_complete_edge(self) -> Optional["RequestCompleteEdge"]:
        return self

    def outgoing_node(self) -> "RequesterNode":
        node = super().outgoing_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

    def headers(self) -> str:
        return self.data()[self.RawAttrs.HEADERS.value]

    def size(self) -> int:
        return int(self.data()[self.RawAttrs.SIZE.value])

    def hash(self) -> str:
        return self.data()[self.RawAttrs.HASH.value]
