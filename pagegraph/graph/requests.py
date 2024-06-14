from dataclasses import dataclass, field
from typing import cast, Optional, TYPE_CHECKING, Union

from pagegraph.serialize import Reportable, RequestCompleteReport
from pagegraph.serialize import RequestErrorReport, RequestChainReport
from pagegraph.serialize import RequestReport
from pagegraph.types import RequestId, Url, PageGraphEdgeId, ResourceType

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import RequestStartEdge, RequestRedirectEdge
    from pagegraph.graph.edge import RequestResponseEdge, RequestCompleteEdge
    from pagegraph.graph.edge import RequestErrorEdge


@dataclass
class RequestResponse:
    request: Union["RequestStartEdge", "RequestRedirectEdge"]
    response: Union["RequestResponseEdge", None] = None


@dataclass
class RequestChain(Reportable):
    request_id: RequestId
    request: "RequestStartEdge"
    redirects: list["RequestRedirectEdge"] = field(default_factory=list)
    result: Union["RequestCompleteEdge", "RequestErrorEdge", None] = None

    def to_report(self) -> RequestChainReport:
        request_id = self.request_id
        resource_type = self.request.resource_type()

        start_report = RequestReport(self.request.pg_id(), self.request.url())
        redirect_reports = []
        for redirect in self.redirects:
            redirect_reports.append(
                RequestReport(redirect.pg_id(), redirect.url()))
        result_report: Union[
            "RequestCompleteReport" | "RequestErrorReport" | None] = None
        result_edge = self.result
        if result_edge:
            if request_complete_edge := result_edge.as_request_complete_edge():
                result_report = RequestCompleteReport(
                    request_complete_edge.pg_id(),
                    request_complete_edge.size(),
                    request_complete_edge.hash(),
                    request_complete_edge.headers())
            elif request_error_edge := result_edge.as_request_error_edge():
                result_report = RequestErrorReport(
                    request_error_edge.pg_id(),
                    request_error_edge.headers())
        return RequestChainReport(
            request_id, resource_type, start_report,  redirect_reports,
            result_report)

    def hash(self) -> Optional[str]:
        if not self.result:
            return None
        if request_complete_edge := self.result.as_request_complete_edge():
            return request_complete_edge.hash()
        return None

    def success_request(self) -> Optional["RequestCompleteEdge"]:
        if not self.result:
            return None
        if request_complete_edge := self.result.as_request_complete_edge():
            return request_complete_edge
        return None

    def error_request(self) -> Optional["RequestErrorEdge"]:
        if not self.result:
            return None
        if request_error_edge := self.result.as_request_error_edge():
            return request_error_edge
        return None

    def resource_type(self) -> ResourceType:
        return self.request.resource_type()

    def final_url(self) -> Url:
        if len(self.redirects) == 0:
            return self.request.url()
        return self.redirects[-1].url()


def request_chain_for_edge(request_edge: "RequestStartEdge") -> RequestChain:
    request_id = request_edge.request_id()
    chain = RequestChain(request_id, request_edge)

    request: Union["RequestStartEdge", "RequestRedirectEdge"] = request_edge
    while resource_node := request.outgoing_node():
        next_edge = resource_node.response_for_id(request_id)
        if not next_edge:
            break

        if request_redirect_edge := next_edge.as_request_redirect_edge():
            chain.redirects.append(request_redirect_edge)
            if request == request_redirect_edge:
                break
            else:
                request = request_redirect_edge
                continue

        if request_complete_edge := next_edge.as_request_complete_edge():
            chain.result = request_complete_edge
        elif request_error_edge := next_edge.as_request_error_edge():
            chain.result = request_error_edge
        else:
            raise ValueError("Should not be reachable")
        break
    return chain
