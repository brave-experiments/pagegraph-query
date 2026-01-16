from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge


class StorageReadResultEdge(FrameIdAttributedEdge):
    def as_storage_read_result_edge(self) -> Optional[StorageReadResultEdge]:
        return self

    def value(self) -> str:
        return self.data()[Edge.RawAttrs.VALUE.value]
