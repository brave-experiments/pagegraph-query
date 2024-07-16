from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge.abc.storage_call import StorageCallEdge


class StorageDeleteEdge(StorageCallEdge):
    def as_storage_delete_edge(self) -> Optional[StorageDeleteEdge]:
        return self

    def key(self) -> str:
        return self.data()[self.RawAttrs.KEY.value]
