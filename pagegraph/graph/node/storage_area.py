from __future__ import annotations

from abc import ABC
from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node


class StorageAreaNode(Node, ABC):
    incoming_edge_types = [
        Edge.Types.STORAGE_BUCKET,
        Edge.Types.STORAGE_CLEAR,
        Edge.Types.STORAGE_DELETE,
        Edge.Types.STORAGE_READ_CALL,
        Edge.Types.STORAGE_SET,
    ]

    outgoing_edge_types = [
        Edge.Types.STORAGE_READ_RESULT
    ]

    def as_storage_area_node(self) -> Optional[StorageAreaNode]:
        return (
            self.as_cookie_jar_node() or
            self.as_local_storage_node() or
            self.as_session_storage_node()
        )
