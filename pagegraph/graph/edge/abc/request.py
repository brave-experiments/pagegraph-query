from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge
from pagegraph.graph.requests import parse_headers

if TYPE_CHECKING:
    from typing import Optional

    from pagegraph.types import RequestId, ResponseHeaders


class RequestEdge(FrameIdAttributedEdge, ABC):

    summary_methods = {
        "request id": "request_id",
        "headers": "headers",
        "size": "size"
    }

    def headers_raw(self) -> Optional[str]:
        return self.data()[self.RawAttrs.HEADERS.value]

    def headers(self) -> Optional[ResponseHeaders]:
        parsed_headers = []
        if header_text := self.headers_raw():
            parsed_headers = parse_headers(header_text)
        return parsed_headers

    def size(self) -> int:
        return int(self.data()[self.RawAttrs.SIZE.value])

    def request_id(self) -> RequestId:
        return int(self.data()[self.RawAttrs.REQUEST_ID.value])
