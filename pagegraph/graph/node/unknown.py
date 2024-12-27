from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node
from pagegraph.serialize import Reportable, BasicReport


class UnknownNode(Node, Reportable):

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

    def as_unknown_node(self) -> Optional[UnknownNode]:
        return self

    def to_report(self) -> BasicReport:
        return BasicReport("Unknown")
