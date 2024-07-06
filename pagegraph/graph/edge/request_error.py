from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.request_response import RequestResponseEdge

if TYPE_CHECKING:
    from pagegraph.types import RequesterNode


class RequestErrorEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    def as_request_error_edge(self) -> Optional["RequestErrorEdge"]:
        return self

    def outgoing_node(self) -> "RequesterNode":
        node = super().outgoing_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

    def headers(self) -> str | None:
        try:
            return self.data()[self.RawAttrs.HEADERS.value]
        except KeyError:
            return None
