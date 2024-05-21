from dataclasses import dataclass, field
from typing import cast, TYPE_CHECKING, Union

from pagegraph.types import RequestId, Url, PageGraphEdgeId
from pagegraph.serialize import Reportable, RequestCompleteReport
from pagegraph.serialize import RequestErrorReport, RequestChainReport
from pagegraph.serialize import RequestReport

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

        start_report = RequestReport(self.request.id(), self.request.url())
        redirect_reports = []
        for redirect in self.redirects:
            redirect_reports.append(
                RequestReport(redirect.id(), redirect.url()))
        result_report: Union[
            "RequestCompleteReport" | "RequestErrorReport" | None] = None
        result_edge = self.result
        if result_edge:
            if result_edge.is_request_complete_edge():
                result_complete_edge = cast("RequestCompleteEdge", result_edge)
                result_report = RequestCompleteReport(
                    result_complete_edge.id(),
                    result_complete_edge.size(),
                    result_complete_edge.hash(),
                    result_complete_edge.headers())
            else:
                result_error_edge = cast("RequestErrorEdge", result_edge)
                result_report = RequestErrorReport(
                    result_error_edge.id(),
                    result_error_edge.headers())
        return RequestChainReport(
            request_id, resource_type, start_report,  redirect_reports,
            result_report)

    def hash(self) -> str | None:
        if self.result and self.result.is_request_complete_edge():
            return cast("RequestCompleteEdge", self.result).hash()
        return None


def request_chain_for_edge(request_edge: "RequestStartEdge") -> RequestChain:
    request_id = request_edge.request_id()
    chain = RequestChain(request_id, request_edge)

    request: Union["RequestStartEdge", "RequestRedirectEdge"] = request_edge
    while resource_node := request.outgoing_node():
        next_edge = resource_node.response_for_id(request_id)
        if not next_edge:
            break

        if next_edge.is_request_redirect_edge():
            redirect_edge = cast("RequestRedirectEdge", next_edge)
            chain.redirects.append(redirect_edge)
            request = redirect_edge
            continue

        if next_edge.is_request_complete_edge():
            complete_edge = cast("RequestCompleteEdge", next_edge)
            chain.result = complete_edge
        elif next_edge.is_request_error_edge():
            error_edge = cast("RequestErrorEdge", next_edge)
            chain.result = error_edge
        else:
            raise ValueError("Should not be reachable")
        break
    return chain
