from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.types import RequestId


class RequestEdge(FrameIdAttributedEdge, ABC):

    summary_methods = {
        "request id": "request_id",
    }

    def request_id(self) -> RequestId:
        return int(self.data()[self.RawAttrs.REQUEST_ID.value])
