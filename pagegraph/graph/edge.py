from enum import StrEnum
from json import loads, JSONDecodeError
from typing import Any, cast, Dict, List, TypeVar, Type, TYPE_CHECKING, Union

from pagegraph.graph.element import PageGraphElement
from pagegraph.graph.types import PageGraphNodeId, PageGraphEdgeId
from pagegraph.graph.types import BlinkId, PageGraphEdgeKey, RequesterNode
from pagegraph.graph.types import ChildNode, ParentNode, FrameId
from pagegraph.graph.serialize import Reportable, RequestReport

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.node import Node, ScriptNode, DOMRootNode, HTMLNode
    from pagegraph.graph.node import JSStructureNode, ResourceNode


class Edge(PageGraphElement):

    incoming_node_id: PageGraphNodeId
    outgoing_node_id: PageGraphNodeId

    class Types(StrEnum):
        ATTRIBUTE_DELETE = "delete attribute"
        ATTRIBUTE_SET = "set attribute"
        CROSS_DOM = "cross DOM"
        EXECUTE = "execute"
        EXECUTE_FROM_ATTRIBUTE = "execute from attribute"
        NODE_CREATE = "create node"
        NODE_INSERT = "insert node"
        NODE_REMOVE = "remove node"
        STRUCTURE = "structure"
        REQUEST_START = "request start"
        REQUEST_COMPLETE = "request complete"
        REQUEST_ERROR = "request error"
        REQUEST_REDIRECT = "request redirect"
        REQUEST_RESPONSE = "request response"
        EVENT_LISTENER = "event listener"
        EVENT_LISTENER_ADD = "add event listener"
        EVENT_LISTENER_REMOVE = "remove event listener"
        SHIELD = "shield"
        STORAGE_BUCKET = "storage bucket"
        STORAGE_READ_CALL = "read storage call"
        STORAGE_READ_RESULT = "storage read result"
        STORAGE_CLEAR = "clear storage"
        STORAGE_SET = "storage set"
        STORAGE_DELETE = "delete storage"
        JS_CALL = "js call"
        JS_RESULT = "js result"

    class RawAttrs(StrEnum):
        ARGS = "args"
        BEFORE_BLINK_ID = "before"
        FRAME_ID = "frame id"
        HASH = "response hash"
        HEADERS = "headers"
        PARENT_BLINK_ID = "parent"
        SIZE = "size"
        TIMESTAMP = "timestamp"
        TYPE = "edge type"
        VALUE = "value"

    def __init__(self, graph: "PageGraph", id: PageGraphEdgeId,
                 parent_id: PageGraphNodeId, child_id: PageGraphNodeId):
        self.incoming_node_id = parent_id
        self.outgoing_node_id = child_id
        super().__init__(graph, id)

    def incoming_node(self) -> "Node":
        return self.pg.node(self.incoming_node_id)

    def outgoing_node(self) -> "Node":
        return self.pg.node(self.outgoing_node_id)

    def edge_type(self) -> "Edge.Types":
        type_name = self.data()[self.RawAttrs.TYPE.value]
        return self.Types(type_name)

    def is_type(self, edge_type: Types) -> bool:
        return self.data()[self.RawAttrs.TYPE.value] == edge_type.value

    def is_insert_edge(self) -> bool:
        return False

    def is_structure_edge(self) -> bool:
        return False

    def is_create_edge(self) -> bool:
        return False

    def is_execute_edge(self) -> bool:
        return False

    def is_cross_dom_edge(self) -> bool:
        return False

    def is_request_start_edge(self) -> bool:
        return False

    def is_request_complete_edge(self) -> bool:
        return False

    def is_request_error_edge(self) -> bool:
        return False

    def is_request_redirect_edge(self) -> bool:
        return False

    def is_js_call_edge(self) -> bool:
        return False

    def is_js_result_edge(self) -> bool:
        return False

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.edges[self.key()])

    def timestamp(self) -> int:
        return int(self.data()[self.RawAttrs.TIMESTAMP])

    def key(self) -> PageGraphEdgeKey:
        return self.incoming_node_id, self.outgoing_node_id, self._id

    def describe(self) -> str:
        output = f"edge eid={self.id()}\n"
        output += f"- parent node nid={self.incoming_node().id()}\n"
        output += f"- child node nid={self.outgoing_node().id()}\n"
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"
        return output

    def validate(self) -> bool:
        return True


class FrameIdAttributedEdge(Edge):

    def frame_id(self) -> FrameId:
        if self.RawAttrs.FRAME_ID.value not in self.data():
            self.throw("")
        return self.data()[self.RawAttrs.FRAME_ID.value]


class AttributeDeleteEdge(FrameIdAttributedEdge):
    pass


class AttributeSetEdge(FrameIdAttributedEdge):
    pass


class CrossDOMEdge(Edge):

    def is_cross_dom_edge(self) -> bool:
        return True


class ExecuteEdge(Edge):
    def is_execute_edge(self) -> bool:
        return True

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        assert outgoing_node.is_script()
        return cast("ScriptNode", outgoing_node)


class ExecuteFromAttributeEdge(ExecuteEdge):
    pass


class StructureEdge(Edge):

    def is_structure_edge(self) -> bool:
        return True

    def outgoing_node(self) -> ChildNode:
        outgoing_node = super().outgoing_node()
        return cast(ChildNode, outgoing_node)


class RequestStartEdge(FrameIdAttributedEdge):

    def is_request_start_edge(self) -> bool:
        return True

    def incoming_node(self) -> RequesterNode:
        node = super().incoming_node()
        assert node.is_requester_node_type()
        return cast(RequesterNode, node)


class RequestCompleteEdge(FrameIdAttributedEdge, Reportable):

    def to_report(self) -> RequestReport:
        resource_node = self.incoming_node()
        return RequestReport(
            resource_node.id(), resource_node.url(),
            "complete", self.hash(), self.size(), self.headers())

    def is_request_complete_edge(self) -> bool:
        return True

    def incoming_node(self) -> "ResourceNode":
        node = super().incoming_node()
        if self.pg.debug:
            if not node.is_resource_node():
                self.throw("Unexpected incoming node type")
        return cast("ResourceNode", node)

    def outgoing_node(self) -> RequesterNode:
        node = super().outgoing_node()
        if self.pg.debug:
            if not node.is_requester_node_type():
                self.throw("Unexpected outgoing node type")
        return cast(RequesterNode, node)

    def headers(self) -> str:
        return self.data()[self.RawAttrs.HEADERS.value]

    def size(self) -> int:
        return int(self.data()[self.RawAttrs.SIZE.value])

    def hash(self) -> str:
        return self.data()[self.RawAttrs.HASH.value]


class RequestErrorEdge(FrameIdAttributedEdge, Reportable):

    def to_report(self) -> RequestReport:
        resource_node = self.incoming_node()
        return RequestReport(
            resource_node.id(), resource_node.url(),
            "error", None, None, None)

    def is_request_error_edge(self) -> bool:
        return True

    def incoming_node(self) -> "ResourceNode":
        node = super().incoming_node()
        if self.pg.debug:
            if not node.is_resource_node():
                self.throw("Unexpected incoming node type")
        return cast("ResourceNode", node)

    def outgoing_node(self) -> RequesterNode:
        node = super().outgoing_node()
        if self.pg.debug:
            if not node.is_requester_node_type():
                self.throw("Unexpected outgoing node type")
        return cast(RequesterNode, node)


class RequestRedirectEdge(FrameIdAttributedEdge, Reportable):

    def incoming_node(self) -> "ResourceNode":
        node = super().incoming_node()
        if self.pg.debug:
            if not node.is_resource_node():
                self.throw("Unexpected incoming node type")
        return cast("ResourceNode", node)

    def to_report(self) -> RequestReport:
        resource_node = self.incoming_node()
        return RequestReport(
            resource_node.id(), resource_node.url(),
            "redirect", None, None, None)

    def is_request_redirect_edge(self) -> bool:
        return True


class RequestResponseEdge(FrameIdAttributedEdge):
    pass


class NodeCreateEdge(FrameIdAttributedEdge):

    def is_create_edge(self) -> bool:
        return True


class NodeInsertEdge(FrameIdAttributedEdge):

    def is_insert_edge(self) -> bool:
        return True

    def inserted_before_blink_id(self) -> BlinkId | None:
        return self.data()[Edge.RawAttrs.BEFORE_BLINK_ID]

    def inserted_before_node(self) -> Union[None, "Node"]:
        blink_id = self.inserted_before_blink_id()
        if not blink_id:
            return None
        node = self.pg.node_for_blink_id(blink_id)
        return node

    def inserted_below_blink_id(self) -> BlinkId:
        return self.data()[Edge.RawAttrs.PARENT_BLINK_ID]

    def inserted_below_node(self) -> ParentNode:
        blink_id = self.inserted_below_blink_id()
        node = self.pg.node_for_blink_id(blink_id)
        assert node.is_parent_dom_node_type()
        if node.is_html_elm():
            return cast("HTMLNode", node)
        else:
            return cast("DOMRootNode", node)

    def inserted_node(self) -> ChildNode:
        child_node = self.outgoing_node()
        if self.pg.debug:
            if not child_node.is_child_dom_node_type():
                self.throw("Unexpected child node type")
        return cast(ChildNode, child_node)


class NodeRemoveEdge(FrameIdAttributedEdge):
    pass


class EventListenerEdge(Edge):
    pass


class EventListenerAddEdge(FrameIdAttributedEdge):
    pass


class EventListenerRemoveEdge(FrameIdAttributedEdge):
    pass


class StorageBucketEdge(Edge):
    pass


class StorageReadCallEdge(FrameIdAttributedEdge):
    pass


class StorageReadResultEdge(FrameIdAttributedEdge):
    pass


class StorageSetEdge(FrameIdAttributedEdge):
    pass


class StorageClearEdge(FrameIdAttributedEdge):
    pass


class StorageDeleteEdge(FrameIdAttributedEdge):
    pass


class JSCallEdge(FrameIdAttributedEdge):

    def args(self) -> Any:
        args_raw = self.data()[Edge.RawAttrs.ARGS.value]
        return_result = None
        try:
            return_result = loads(args_raw)
        except JSONDecodeError:
            return_result = args_raw
        return return_result

    def is_js_call_edge(self) -> bool:
        return True

    def incoming_node(self) -> "ScriptNode":
        incoming_node = super().incoming_node()
        if self.pg.debug:
            if not incoming_node.is_script():
                self.throw("Unexpected incoming node type")
        return cast("ScriptNode", incoming_node)

    def outgoing_node(self) -> "JSStructureNode":
        outgoing_node = super().outgoing_node()
        if self.pg.debug:
            if not outgoing_node.is_js_structure():
                self.throw("Unexpected outgoing node type")
        return cast("JSStructureNode", outgoing_node)


class JSResultEdge(FrameIdAttributedEdge):

    def value(self) -> Any:
        value_raw = self.data()[Edge.RawAttrs.VALUE.value]
        try:
            return loads(value_raw)
        except JSONDecodeError:
            return value_raw

    def is_js_result_edge(self) -> bool:
        return True

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        if self.pg.debug:
            if not outgoing_node.is_script():
                self.throw("Unexpected outgoing node type")
        return cast("ScriptNode", outgoing_node)

    def incoming_node(self) -> "JSStructureNode":
        incoming_node = super().incoming_node()
        if self.pg.debug:
            if not incoming_node.is_js_structure():
                self.throw("Unexpected incoming node type")
        return cast("JSStructureNode", incoming_node)


class DeprecatedEdge(Edge):
    pass


TYPE_MAPPING: Dict[Edge.Types, Type[Edge]] = dict([
    (Edge.Types.ATTRIBUTE_DELETE, AttributeDeleteEdge),
    (Edge.Types.ATTRIBUTE_SET, AttributeSetEdge),
    (Edge.Types.CROSS_DOM, CrossDOMEdge),
    (Edge.Types.EXECUTE, ExecuteEdge),
    (Edge.Types.EXECUTE_FROM_ATTRIBUTE, ExecuteFromAttributeEdge),
    (Edge.Types.NODE_CREATE, NodeCreateEdge),
    (Edge.Types.NODE_INSERT, NodeInsertEdge),
    (Edge.Types.NODE_REMOVE, NodeRemoveEdge),
    (Edge.Types.STRUCTURE, StructureEdge),
    (Edge.Types.REQUEST_START, RequestStartEdge),
    (Edge.Types.REQUEST_COMPLETE, RequestCompleteEdge),
    (Edge.Types.REQUEST_REDIRECT, RequestRedirectEdge),
    (Edge.Types.REQUEST_RESPONSE, RequestResponseEdge),
    (Edge.Types.EVENT_LISTENER, EventListenerEdge),
    (Edge.Types.EVENT_LISTENER_ADD, EventListenerAddEdge),
    (Edge.Types.EVENT_LISTENER_REMOVE, EventListenerRemoveEdge),
    (Edge.Types.STORAGE_BUCKET, StorageBucketEdge),
    (Edge.Types.STORAGE_READ_CALL, StorageReadCallEdge),
    (Edge.Types.STORAGE_READ_RESULT, StorageReadResultEdge),
    (Edge.Types.STORAGE_SET, StorageSetEdge),
    (Edge.Types.STORAGE_CLEAR, StorageClearEdge),
    (Edge.Types.STORAGE_DELETE, StorageDeleteEdge),
    (Edge.Types.REQUEST_ERROR, RequestErrorEdge),
    (Edge.Types.JS_CALL, JSCallEdge),
    (Edge.Types.JS_RESULT, JSResultEdge),

    (Edge.Types.SHIELD, DeprecatedEdge),
])


def for_type(edge_type: Edge.Types, graph: "PageGraph",
             edge_id: PageGraphEdgeId, parent_id: PageGraphNodeId,
             child_id: PageGraphNodeId) -> Edge:
    try:
        return TYPE_MAPPING[edge_type](graph, edge_id, parent_id, child_id)
    except KeyError:
        raise ValueError(f"Unexpected edge type='{edge_type.value}'")
