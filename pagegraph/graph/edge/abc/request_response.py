from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.request import RequestEdge

if TYPE_CHECKING:
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.graph.node.resource import ResourceNode


class RequestResponseEdge(RequestEdge, ABC):

    def incoming_node(self) -> ResourceNode:
        node = super().incoming_node()
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

    def request_start_edge(self) -> RequestStartEdge:
        request_id = self.request_id()
        request_chain = self.pg.request_chain_for_id(request_id)
        return request_chain.request
