from typing import Optional

from pagegraph.graph.edge.storage_call import StorageCallEdge


class StorageClearEdge(StorageCallEdge):
    def as_storage_clear_edge(self) -> Optional["StorageClearEdge"]:
        return self
