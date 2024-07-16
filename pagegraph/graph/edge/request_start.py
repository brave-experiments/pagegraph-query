from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.abc.request import RequestEdge
from pagegraph.types import ResourceType

if TYPE_CHECKING:
    from pagegraph.graph.node.resource import ResourceNode
    from pagegraph.types import Url, RequesterNode


class RequestStartEdge(RequestEdge):

    incoming_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "HTML element",  # Node.Types.HTML
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT_LOCAL
    ]

    outgoing_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    summary_methods = {
        "resource type": "resource_type_name",
        "url": "url",
    }

    def as_request_start_edge(self) -> Optional[RequestStartEdge]:
        return self

    def incoming_node(self) -> RequesterNode:
        node = super().incoming_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

    def outgoing_node(self) -> ResourceNode:
        node = super().outgoing_node()
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

    def resource_type(self) -> ResourceType:
        resource_type_raw = self.data()[Edge.RawAttrs.RESOURCE_TYPE.value]
        try:
            return ResourceType(resource_type_raw)
        except ValueError:
            return ResourceType.OTHER

    def resource_type_name(self) -> str:
        return self.resource_type().value

    def url(self) -> Url:
        return self.outgoing_node().url()
