from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Optional, TYPE_CHECKING, Union

from pagegraph.serialize import Reportable, RequestCompleteReport
from pagegraph.serialize import RequestErrorReport, RequestChainReport
from pagegraph.serialize import RequestReport

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge.abc.request import RequestEdge
    from pagegraph.graph.edge.abc.request_response import RequestResponseEdge
    from pagegraph.graph.edge.request_complete import RequestCompleteEdge
    from pagegraph.graph.edge.request_error import RequestErrorEdge
    from pagegraph.graph.edge.request_redirect import RequestRedirectEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.types import RequestId, RequestHeaders, Url, ResourceType
    from pagegraph.types import RequestIncoming, RequestOutgoing


@dataclass
class RequestChain(Reportable):
    request_id: RequestId
    request: RequestStartEdge
    redirects: list[RequestRedirectEdge] = field(default_factory=list)
    result: Union[RequestCompleteEdge, RequestErrorEdge, None] = None

    def to_report(self) -> RequestChainReport:
        request_id = self.request_id
        resource_type = self.request.resource_type()

        start_report = RequestReport(self.request.pg_id(), self.request.url())
        redirect_reports = []
        for redirect in self.redirects:
            redirect_reports.append(
                RequestReport(redirect.pg_id(), redirect.url()))
        result_report: Union[
            RequestCompleteReport, RequestErrorReport, None] = None
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
            request_id, resource_type.value, start_report,  redirect_reports,
            result_report)

    def hash(self) -> Optional[str]:
        if not self.result:
            return None
        if request_complete_edge := self.result.as_request_complete_edge():
            return request_complete_edge.hash()
        return None

    def success_request(self) -> Optional[RequestCompleteEdge]:
        if not self.result:
            return None
        if request_complete_edge := self.result.as_request_complete_edge():
            return request_complete_edge
        return None

    def error_request(self) -> Optional[RequestErrorEdge]:
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

    def add_redirect(self, edge: RequestRedirectEdge) -> None:
        self.redirects.append(edge)

    def all_requests(self) -> set[RequestEdge]:
        requests: set[RequestEdge] = set()
        requests.add(self.request)
        requests |= set(self.redirects)
        if self.result:
            requests.add(self.result)
        return requests


def request_chain_for_edge(request_edge: RequestStartEdge) -> RequestChain:
    request_id = request_edge.request_id()
    chain = RequestChain(request_id, request_edge)
    resource_node = request_edge.outgoing_node()

    while True:
        next_edge = resource_node.next_response_for_id(request_id,
                                                       chain.all_requests())

        if not next_edge:
            return chain

        if request_redirect_edge := next_edge.as_request_redirect_edge():
            chain.add_redirect(request_redirect_edge)
            resource_node = request_redirect_edge.outgoing_node()
            continue

        if request_complete_edge := next_edge.as_request_complete_edge():
            chain.result = request_complete_edge
            break

        if request_error_edge := next_edge.as_request_error_edge():
            chain.result = request_error_edge
            break

        raise ValueError("Should not be reachable")
    return chain


def parse_headers(headers_text: str) -> RequestHeaders:
    headers = []
    for line in headers_text.split("\n"):
        match = re.search(r'"(.+)" "(.*)"', line)
        if match:
            headers.append((match.group(1), match.group(2)))
    return headers
