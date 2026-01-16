from __future__ import annotations

from typing import TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.node.js_structure import JSStructureNode

if TYPE_CHECKING:
    from typing import Optional


class JSBuiltInNode(JSStructureNode):

    incoming_edge_types = [
        Edge.Types.JS_CALL
    ]

    outgoing_edge_types = [
        Edge.Types.JS_RESULT
    ]

    def as_js_builtin_node(self) -> Optional[JSBuiltInNode]:
        return self
