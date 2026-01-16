from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node

if TYPE_CHECKING:
    from typing import Optional

    from pagegraph.graph.edge.execute import ExecuteEdge
    from pagegraph.types import ScriptId


class ScriptNode(Node, ABC):

    incoming_edge_types = [
        Edge.Types.EVENT_LISTENER_FIRED,
        Edge.Types.EXECUTE,
        Edge.Types.EXECUTE_FROM_ATTRIBUTE,
        Edge.Types.JS_RESULT,
        Edge.Types.REQUEST_COMPLETE,
        Edge.Types.REQUEST_ERROR,
        Edge.Types.REQUEST_REDIRECT,
        Edge.Types.STORAGE_READ_RESULT,
    ]

    outgoing_edge_types = [
        Edge.Types.ATTRIBUTE_DELETE,
        Edge.Types.ATTRIBUTE_SET,
        Edge.Types.EXECUTE,
        Edge.Types.JS_CALL,
        Edge.Types.NODE_CREATE,
        Edge.Types.NODE_INSERT,
        Edge.Types.NODE_REMOVE,
        Edge.Types.REQUEST_START,
        Edge.Types.STORAGE_CLEAR,
        Edge.Types.STORAGE_DELETE,
        Edge.Types.STORAGE_READ_CALL,
        Edge.Types.STORAGE_SET,
        Edge.Types.EVENT_LISTENER_ADD,
        Edge.Types.EVENT_LISTENER_REMOVE,
    ]

    def as_script_node(self) -> Optional[ScriptNode]:
        return self

    def script_id(self) -> ScriptId:
        return int(self.data()[self.RawAttrs.SCRIPT_ID.value])

    def execute_edge(self) -> ExecuteEdge:
        execute_edge = None
        for edge in self.incoming_edges():
            if execute_edge := edge.as_execute_edge():
                break
        if self.pg.debug:
            if not execute_edge:
                self.throw("Could not find execution edge for script")
        assert execute_edge
        return execute_edge
