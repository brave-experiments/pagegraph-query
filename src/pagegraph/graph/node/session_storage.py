from __future__ import annotations

from typing import Optional

from pagegraph.graph.node.storage_area import StorageAreaNode


class SessionStorageNode(StorageAreaNode):

    def as_session_storage_node(self) -> Optional[SessionStorageNode]:
        return self
