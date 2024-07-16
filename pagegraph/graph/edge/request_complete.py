from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.abc.request_response import RequestResponseEdge
from pagegraph.graph.requests import parse_headers

if TYPE_CHECKING:
    from pagegraph.types import RequesterNode, RequestHeaders


class RequestCompleteEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "HTML element",  # Node.Types.HTML
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT_LOCAL
    ]

    summary_methods = {
        "size": "size",
        "hash": "hash",
    }

    def as_request_complete_edge(self) -> Optional[RequestCompleteEdge]:
        return self

    def outgoing_node(self) -> RequesterNode:
        node = super().outgoing_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

    def headers_raw(self) -> str:
        return self.data()[self.RawAttrs.HEADERS.value]

    def headers(self) -> RequestHeaders:
        parsed_headers = []
        if header_text := self.headers_raw():
            parsed_headers = parse_headers(header_text)
        return parsed_headers

    def size(self) -> int:
        return int(self.data()[self.RawAttrs.SIZE.value])

    def hash(self) -> str:
        return self.data()[self.RawAttrs.HASH.value]
