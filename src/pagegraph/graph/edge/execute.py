from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.abc.script import ScriptNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.types import JSCallingNode, ScriptExecutorNode


class ExecuteEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML
        "DOM root",  # Node.Types.DOCUMENT
        "frame owner",  # Node.Types.FRAME_OWNER
        # Encodes JS URLs
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT_LOCAL
        "remote script",  # Node.Types.SCRIPT_REMOTE
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT_LOCAL
        "unknown actor",  # Node.Types.UNKNOWN
    ]

    def as_execute_edge(self) -> Optional[ExecuteEdge]:
        return self

    def incoming_node(self) -> ScriptExecutorNode:
        node = super().incoming_node()
        in_node: Optional[ScriptExecutorNode] = None
        if parent_dom_node := node.as_parent_dom_element_node():
            in_node = parent_dom_node
        elif script_node := node.as_script_node():
            in_node = script_node
        elif parser_node := node.as_parser_node():
            in_node = parser_node
        assert in_node
        return in_node

    def outgoing_node(self) -> JSCallingNode:
        outgoing_node = super().outgoing_node()
        executor_node = outgoing_node.as_executor_node()
        assert executor_node
        return executor_node
