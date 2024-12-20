from __future__ import annotations

from typing import cast, Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge.abc.request import RequestEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.types import RequesterNode, Url, PageGraphId, RequestId
    from pagegraph.types import RequestIncoming, RequestOutgoing


class ResourceNode(Node):

    outgoing_edge_types = [
        Edge.Types.REQUEST_COMPLETE,
        Edge.Types.REQUEST_ERROR,
        Edge.Types.REQUEST_REDIRECT,
    ]

    incoming_edge_types = [
        # Incoming redirect edges denote a request that was redirected
        # to this resource, from another resource. In this case,
        # both the incoming and outgoing node for the redirect edge
        # will be `ResourceNode` nodes.
        Edge.Types.REQUEST_REDIRECT,
        Edge.Types.REQUEST_START,
    ]

    summary_methods = {
        "url": "url"
    }

    # Instance properties
    requests_map: dict[RequestId, list[RequestOutgoing]]

    def __init__(self, graph: PageGraph, pg_id: PageGraphId):
        self.requests_map = {}
        super().__init__(graph, pg_id)

    def as_resource_node(self) -> Optional[ResourceNode]:
        return self

    def url(self) -> Url:
        return self.data()[self.RawAttrs.URL.value]

    def incoming_edges(self) -> list[RequestStartEdge]:
        return cast(list["RequestStartEdge"], super().incoming_edges())

    def outgoing_edges(self) -> list[RequestOutgoing]:
        outgoing_edges: list[RequestOutgoing] = []
        for edge in super().outgoing_edges():
            if request_complete_edge := edge.as_request_complete_edge():
                outgoing_edges.append(request_complete_edge)
            elif request_redirect_edge := edge.as_request_redirect_edge():
                outgoing_edges.append(request_redirect_edge)
            elif request_error_edge := edge.as_request_error_edge():
                outgoing_edges.append(request_error_edge)
        return outgoing_edges

    def requesters(self) -> list[RequesterNode]:
        requesters = []
        for edge in self.incoming_edges():
            requesters.append(edge.incoming_node())
        return requesters

    def build_caches(self) -> None:
        for incoming_edge in self.incoming_edges():
            request_id = incoming_edge.request_id()
            if request_id not in self.requests_map:
                self.requests_map[request_id] = []

        for outgoing_edge in self.outgoing_edges():
            request_id = outgoing_edge.request_id()
            if self.pg.debug:
                if request_id not in self.requests_map:
                    self.throw("Response without request for resource")
            self.requests_map[request_id].append(outgoing_edge)
        super().build_caches()

    def next_response_for_id(
            self, request_id: RequestId,
            prev_requests: set[RequestEdge]) -> Optional[RequestOutgoing]:
        if self.pg.debug:
            if request_id not in self.requests_map:
                self.throw("Unexpected request id")
        outgoing_responses = self.requests_map[request_id]
        for a_response in outgoing_responses:
            if a_response not in prev_requests:
                return a_response
        return None
