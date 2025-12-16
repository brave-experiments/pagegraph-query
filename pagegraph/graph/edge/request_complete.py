from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.abc.request_response import RequestResponseEdge

if TYPE_CHECKING:
    from pagegraph.types import RequesterNode


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

    def hash(self) -> str:
        return self.data()[self.RawAttrs.HASH.value]
