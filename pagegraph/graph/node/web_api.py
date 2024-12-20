from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.node.js_structure import JSStructureNode


class WebAPINode(JSStructureNode):
    incoming_edge_types = [
        Edge.Types.JS_CALL
    ]

    outgoing_edge_types = [
        Edge.Types.JS_RESULT
    ]

    def as_web_api_node(self) -> Optional[WebAPINode]:
        return self
