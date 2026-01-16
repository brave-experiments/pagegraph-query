from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node


class StorageNode(Node):
    incoming_edge_types = []

    outgoing_edge_types = [
        Edge.Types.STORAGE_BUCKET
    ]

    def as_storage_node(self) -> Optional[StorageNode]:
        return self
