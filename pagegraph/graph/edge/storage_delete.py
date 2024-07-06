from typing import Optional

from pagegraph.graph.edge.storage_call import StorageCallEdge


class StorageDeleteEdge(StorageCallEdge):
    def as_storage_delete_edge(self) -> Optional["StorageDeleteEdge"]:
        return self

    def key(self) -> str:
        return self.data()[self.RawAttrs.KEY.value]
