from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.script import ScriptNode
    from pagegraph.types import RequestId, Url


class ExecuteEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        "DOM root",  # Node.Types.HTML_NODE
        "frame owner",  # Node.Types.FRAME_OWNER
        # Encodes JS URLs
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]

    def as_execute_edge(self) -> Optional["ExecuteEdge"]:
        return self

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        script_node = outgoing_node.as_script_node()
        assert script_node
        return script_node
