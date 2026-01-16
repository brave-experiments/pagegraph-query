from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.storage_area import StorageAreaNode
    from pagegraph.types import JSCallingNode


class StorageCallEdge(FrameIdAttributedEdge, ABC):

    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT_LOCAL
        "unknown actor",  # Node.Types.UNKNOWN
    ]

    outgoing_node_type_names = [
        "local storage",  # Node.Types.LOCAL_STORAGE
        "session storage",  # Node.Types.SESSION_STORAGE
        "cookie jar",  # Node.Types.COOKIE_JAR
    ]

    def incoming_node(self) -> JSCallingNode:
        node = super().incoming_node().as_executor_node()
        assert node
        return node

    def outgoing_node(self) -> StorageAreaNode:
        outgoing_node = super().outgoing_node().as_storage_area_node()
        assert outgoing_node
        return outgoing_node
