from typing import Optional

from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge


class NodeRemoveEdge(FrameIdAttributedEdge):
    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT
        "parser",  # TEMP
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
        "text node",  # Node.Types.TEXT_NODE
    ]

    def as_node_remove_edge(self) -> Optional["NodeRemoveEdge"]:
        return self
