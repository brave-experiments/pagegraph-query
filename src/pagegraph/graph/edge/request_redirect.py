from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.abc.request_response import RequestResponseEdge
from pagegraph.types import Url

if TYPE_CHECKING:
    from pagegraph.graph.node.resource import ResourceNode


class RequestRedirectEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    summary_methods = {
        "url": "url",
    }

    def outgoing_node(self) -> ResourceNode:
        node = super().outgoing_node()
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

    def as_request_redirect_edge(self) -> Optional[RequestRedirectEdge]:
        return self

    def url(self) -> Url:
        return self.outgoing_node().url()
