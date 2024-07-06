from typing import TYPE_CHECKING

from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.graph.node.resource import ResourceNode
    from pagegraph.types import RequestId


class RequestResponseEdge(FrameIdAttributedEdge):

    def request_id(self) -> "RequestId":
        return int(self.data()[self.RawAttrs.REQUEST_ID.value])

    def incoming_node(self) -> "ResourceNode":
        node = super().incoming_node()
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

    def request_start_edge(self) -> "RequestStartEdge":
        request_id = self.request_id()
        request_chain = self.pg.request_chain_for_id(request_id)
        return request_chain.request
