from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.node.js_structure import JSStructureNode


class JSBuiltInNode(JSStructureNode):

    incoming_edge_types = [
        Edge.Types.JS_CALL
    ]

    outgoing_edge_types = [
        Edge.Types.JS_RESULT
    ]

    def as_js_builtin_node(self) -> Optional[JSBuiltInNode]:
        return self
