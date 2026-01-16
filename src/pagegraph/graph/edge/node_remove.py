from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge


class NodeRemoveEdge(FrameIdAttributedEdge):
    incoming_node_type_names = [
        "parser",  # TEMP
        "script",  # Node.Types.SCRIPT_LOCAL
        "unknown actor",  # Node.Types.UNKNOWN
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML
        "text node",  # Node.Types.TEXT_NODE
    ]

    def as_node_remove_edge(self) -> Optional[NodeRemoveEdge]:
        return self
