from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge


class StorageBucketEdge(Edge):
    def as_storage_bucket_edge(self) -> Optional[StorageBucketEdge]:
        return self
