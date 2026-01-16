from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge.abc.storage_call import StorageCallEdge


class StorageClearEdge(StorageCallEdge):
    def as_storage_clear_edge(self) -> Optional[StorageClearEdge]:
        return self
