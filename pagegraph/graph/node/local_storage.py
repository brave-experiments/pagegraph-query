from __future__ import annotations

from typing import Optional

from pagegraph.graph.node.storage_area import StorageAreaNode


class LocalStorageNode(StorageAreaNode):

    def as_local_storage_node(self) -> Optional[LocalStorageNode]:
        return self
