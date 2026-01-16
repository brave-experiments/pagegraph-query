from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.execute import ExecuteEdge

if TYPE_CHECKING:
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.graph.node.script_local import ScriptLocalNode


class ExecuteFromAttributeEdge(ExecuteEdge):

    incoming_node_type_names = [
        "DOM root",  # Node.Types.DOCUMENT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT_LOCAL
    ]

    def as_execute_from_attribute_edge(self) -> Optional[
            ExecuteFromAttributeEdge]:
        return self

    def incoming_node(self) -> ParentDOMElementNode:
        node = super().incoming_node()
        parent_dom_node = node.as_parent_dom_element_node()
        assert parent_dom_node
        return parent_dom_node

    def outgoing_node(self) -> ScriptLocalNode:
        outgoing_node = super().outgoing_node()
        executor_node = outgoing_node.as_script_local_node()
        assert executor_node
        return executor_node
