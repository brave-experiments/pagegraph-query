from enum import StrEnum
from typing import cast, TypeVar, TYPE_CHECKING

from pagegraph.graph.node import Node, HTMLNode, DOMRootNode, FrameOwnerNode, TextNode
from pagegraph.graph.types import PageGraphNodeId, PageGraphEdgeId
from pagegraph.graph.types import BlinkId, PageGraphEdgeKey, ParentNode
from pagegraph.graph.types import ChildNode
from pagegraph.graph.element import PageGraphElement

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph


class Edge(PageGraphElement):

    parent_id: PageGraphNodeId
    child_id: PageGraphNodeId

    class Types(StrEnum):
        CROSS_DOM = "cross DOM"
        EXECUTE = "execute"
        INSERT_NODE = "insert node"
        CREATE_NODE = "create node"
        STRUCTURE = "structure"
        REQUEST_START = "request start"
        REQUEST_COMPLETE = "request complete"
        EVENT_LISTENER = "event listener"

    class RawAttrs(StrEnum):
        TYPE = "edge type"
        PARENT_BLINK_ID = "parent"
        BEFORE_BLINK_ID = "before"

    def __init__(self, graph: "PageGraph", id: PageGraphEdgeId,
            parent_id: PageGraphNodeId, child_id: PageGraphNodeId):
        assert id.startswith('e')
        self.parent_id = parent_id
        self.child_id = child_id
        super().__init__(graph, id)

    def parent_node(self) -> Node:
        return self.pg.node(self.parent_id)

    def child_node(self) -> Node:
        return self.pg.node(self.child_id)

    def edge_type(self) -> str:
        return self.data()[self.RawAttrs.TYPE.value]

    def is_type(self, edge_type: Types) -> bool:
        return self.data()[self.RawAttrs.TYPE.value] == edge_type.value

    def is_insert_edge(self) -> bool:
        return self.is_type(self.Types.INSERT_NODE)

    def is_structure_edge(self) -> bool:
        return self.is_type(self.Types.STRUCTURE)

    def is_create_edge(self) -> bool:
        return self.is_type(self.Types.CREATE_NODE)

    def is_execute_edge(self) -> bool:
        return self.is_type(self.Types.EXECUTE)

    def is_cross_dom_edge(self) -> bool:
        return self.is_type(self.Types.CROSS_DOM)

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.edges[self.key()])

    def key(self) -> PageGraphEdgeKey:
        return self.parent_id, self.child_id, self._id

    def describe(self) -> str:
        output = f"edge eid={self.id()}\n"
        output += f"- parent node nid={self.parent_node().id()}\n"
        output += f"- child node nid={self.child_node().id()}\n"
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"
        return output


class CrossDOMEdge(Edge):
    pass


class ExecuteEdge(Edge):

    def child_node(self) -> ScriptNode:
        return cast(ScriptNode, super().child_node())


class StructureEdge(Edge):
    pass


class RequestStartEdge(Edge):
    pass


class RequestCompleteEdge(Edge):
    pass


class InsertNodeEdge(Edge):

    def inserted_before_blink_id(self) -> BlinkId | None:
        return self.data()[Edge.RawAttrs.BEFORE_BLINK_ID]

    def inserted_before_node(self) -> None | Node:
        blink_id = self.inserted_before_blink_id()
        if not blink_id:
            return None
        node = self.pg.node_for_blink_id(blink_id)
        return node

    def inserted_below_blink_id(self) -> BlinkId:
        return self.data()[Edge.RawAttrs.PARENT_BLINK_ID]

    def inserted_below_node(self) -> Node:
        blink_id = self.inserted_below_blink_id()
        node = self.pg.node_for_blink_id(blink_id)
        return node


class CreateNodeEdge(Edge):
    pass


class EventListenerEdge(Edge):
    pass


def for_type(edge_type: Edge.Types, graph: "PageGraph",
        edge_id: PageGraphEdgeId, parent_id: PageGraphNodeId,
        child_id: PageGraphNodeId) -> Edge:
    if edge_type == Edge.Types.CROSS_DOM:
        return CrossDOMEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.EXECUTE:
        return ExecuteEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.INSERT_NODE:
        return InsertNodeEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.CREATE_NODE:
        return CreateNodeEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.STRUCTURE:
        return StructureEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.REQUEST_START:
        return RequestStartEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.EVENT_LISTENER:
        return EventListenerEdge(graph, edge_id, parent_id, child_id)
    elif edge_type == Edge.Types.REQUEST_COMPLETE:
        return RequestCompleteEdge(graph, edge_id, parent_id, child_id)
    else:
        raise ValueError(f"Unexpected edge type={edge_type.value}")
