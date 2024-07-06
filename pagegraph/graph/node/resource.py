from typing import cast, Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node
from pagegraph.graph.requests import RequestResponse

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge.request_response import RequestResponseEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.types import RequesterNode, Url, PageGraphId, RequestId


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
    requests_map: dict["RequestId", "RequestResponse"]

    def __init__(self, graph: "PageGraph", pg_id: "PageGraphId"):
        self.requests_map = {}
        super().__init__(graph, pg_id)

    def as_resource_node(self) -> Optional["ResourceNode"]:
        return self

    def url(self) -> "Url":
        return self.data()[self.RawAttrs.URL.value]

    def incoming_edges(self) -> list["RequestStartEdge"]:
        return cast(list["RequestStartEdge"], super().incoming_edges())

    def outgoing_edges(self) -> list["RequestResponseEdge"]:
        outgoing_edges: list["RequestResponseEdge"] = []
        for edge in super().outgoing_edges():
            if request_complete_edge := edge.as_request_complete_edge():
                outgoing_edges.append(request_complete_edge)
            elif request_redirect_edge := edge.as_request_redirect_edge():
                outgoing_edges.append(request_redirect_edge)
            elif request_error_edge := edge.as_request_error_edge():
                outgoing_edges.append(request_error_edge)
        return outgoing_edges

    def requesters(self) -> list["RequesterNode"]:
        requesters = []
        for edge in self.incoming_edges():
            requesters.append(edge.incoming_node())
        return requesters

    def build_caches(self) -> None:
        for incoming_edge in self.incoming_edges():
            request_id = incoming_edge.request_id()
            if self.pg.debug:
                if request_id in self.requests_map:
                    self.throw("Found duplicate request id")
            request_response = RequestResponse(incoming_edge)
            self.requests_map[request_id] = request_response

        for outgoing_edge in self.outgoing_edges():
            request_id = outgoing_edge.request_id()
            if self.pg.debug:
                if request_id not in self.requests_map:
                    self.throw("Response without request for resource")
                if self.requests_map[request_id].response is not None:
                    self.throw("Second response for request for resource")
            self.requests_map[request_id].response = outgoing_edge

    def response_for_id(self,
                        request_id: "RequestId") -> Optional["RequestResponseEdge"]:
        if self.pg.debug:
            if request_id not in self.requests_map:
                self.throw("Unexpected request id")
        return self.requests_map[request_id].response
