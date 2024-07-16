from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.abc.storage_call import StorageCallEdge


class StorageReadCallEdge(StorageCallEdge):
    def as_storage_read_call_edge(self) -> Optional[StorageReadCallEdge]:
        return self

    def key(self) -> str:
        return self.data()[Edge.RawAttrs.KEY.value]
