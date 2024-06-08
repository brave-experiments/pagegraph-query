from abc import ABC, abstractmethod
from enum import StrEnum
from json import loads, JSONDecodeError
from typing import Any, cast, Dict, List, TypeVar, Type, TYPE_CHECKING, Union

from pagegraph.graph.element import PageGraphElement
from pagegraph.graph.requests import ResourceType
from pagegraph.types import PageGraphNodeId, PageGraphEdgeId, Url
from pagegraph.types import BlinkId, PageGraphEdgeKey, RequesterNode
from pagegraph.types import ChildNode, ParentNode, FrameId, RequestId
from pagegraph.serialize import EdgeReport, BriefEdgeReport
from pagegraph.serialize import NodeReport, BriefNodeReport


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.node import Node, ScriptNode, DOMRootNode, HTMLNode
    from pagegraph.graph.node import JSStructureNode, ResourceNode


class Edge(PageGraphElement):

    # Used as class properties
    #
    # Note that these are defined as lists of type str, but what they
    # really are is the str values for the Node.Types StrEnum. THis
    # is necessary to prevent the dependency loop.
    # That these are valid node type enum strs is checked at runtime
    # if in debug mode.
    incoming_node_type_names: Union[List[str], None] = None  # Node.Types
    outgoing_node_type_names: Union[List[str], None] = None  # Node.Types

    # The below are automatically generated from the above,
    # but at runtime to again prevent the dependency loop.
    incoming_node_types: Union[List["Node.Types"], None] = None
    outgoing_node_types: Union[List["Node.Types"], None] = None

    @classmethod
    def __make_incoming_node_types(cls) -> Union[List["Node.Types"], None]:
        if cls.incoming_node_type_names is None:
            return None

        if cls.incoming_node_types:
            return cls.incoming_node_types

        from pagegraph.graph.node import Node
        cls.incoming_node_types = []
        for node_type_name in cls.incoming_node_type_names:
            cls.incoming_node_types.append(Node.Types(node_type_name))
        return cls.incoming_node_types

    @classmethod
    def __make_outgoing_node_types(cls) -> Union[List["Node.Types"], None]:
        if cls.outgoing_node_type_names is None:
            return None

        if cls.outgoing_node_types:
            return cls.outgoing_node_types

        from pagegraph.graph.node import Node
        cls.outgoing_node_types = []
        for node_type_name in cls.outgoing_node_type_names:
            cls.outgoing_node_types.append(Node.Types(node_type_name))
        return cls.outgoing_node_types

    # Used as instance properties
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
        REQUEST_ID = "request id"
        RESOURCE_TYPE = "resource type"
        SIZE = "size"
        TIMESTAMP = "timestamp"
        TYPE = "edge type"
        VALUE = "value"

    def __init__(self, graph: "PageGraph", id: PageGraphEdgeId,
                 parent_id: PageGraphNodeId, child_id: PageGraphNodeId):
        self.incoming_node_id = parent_id
        self.outgoing_node_id = child_id
        super().__init__(graph, id)

    def to_edge_report(
            self, depth: int = 0,
            seen: None | set[Union["Node", "Edge"]] = None) -> EdgeReport:
        if seen is None:
            seen = set([self])

        incoming_node = self.incoming_node()
        incoming_node_report: None | NodeReport | BriefNodeReport | str = None
        if incoming_node:
            if incoming_node in seen:
                incoming_node_report = f"(recursion {incoming_node.id()})"
            elif depth > 0:
                incoming_node_report = incoming_node.to_node_report(depth - 1)
            else:
                incoming_node_report = incoming_node.to_brief_report()

        outgoing_node = self.outgoing_node()
        outgoing_node_report: None | NodeReport | BriefNodeReport | str = None
        if outgoing_node:
            if outgoing_node in seen:
                outgoing_node_report = f"(recursion {outgoing_node.id()})"
            if depth > 0:
                outgoing_node_report = outgoing_node.to_node_report(depth - 1)
            else:
                outgoing_node_report = outgoing_node.to_brief_report()

        return EdgeReport(
            self.id(), self.edge_type(), self.summary_fields(),
            incoming_node_report,
            outgoing_node_report)

    def to_brief_report(self) -> BriefEdgeReport:
        return BriefEdgeReport(self.id(), self.edge_type(),
                               self.summary_fields())

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
        incoming_node = self.incoming_node()
        outgoing_node = self.outgoing_node()

        output = f"edge eid={self.id()}\n"
        output += (
            f"- incoming: {incoming_node.node_type()}, {incoming_node.id()}\n"
            f"- outgoing: {outgoing_node.node_type()}, {outgoing_node.id()}\n"
        )
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"
        return output

    def validate(self) -> bool:
        valid_incoming_node_types = self.__class__.__make_incoming_node_types()
        if valid_incoming_node_types is not None:
            node_type = self.incoming_node().node_type()
            if node_type not in valid_incoming_node_types:
                self.throw(f"Unexpected incoming node type: {node_type}")
                return False

        valid_outgoing_node_types = self.__class__.__make_outgoing_node_types()
        if valid_outgoing_node_types is not None:
            node_type = self.outgoing_node().node_type()
            if node_type not in valid_outgoing_node_types:
                self.throw(f"Unexpected outgoing node type: {node_type}")
                return False
        return True


class FrameIdAttributedEdge(Edge):

    def domroot_for_frame_id(self) -> "DOMRootNode":
        frame_id = self.frame_id()
        return self.pg.domroot_for_frame_id(frame_id)

    def frame_id(self) -> FrameId:
        if self.pg.debug:
            if self.RawAttrs.FRAME_ID.value not in self.data():
                self.throw("No frame id recorded")
        return self.data()[self.RawAttrs.FRAME_ID.value]


class AttributeDeleteEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT
        "parser",  # TEMP
    ]

    outgoing_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
    ]


class AttributeSetEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
    ]


class CrossDOMEdge(Edge):

    incoming_node_type_names = [
        "frame owner",  # Node.Types.FRAME_OWNER
    ]

    outgoing_node_type_names = [
        "parser",  # Node.Types.PARSER
    ]

    def is_cross_dom_edge(self) -> bool:
        return True


class ExecuteEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        # Encodes JS URLs
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]

    def is_execute_edge(self) -> bool:
        return True

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        assert outgoing_node.is_script()
        return cast("ScriptNode", outgoing_node)


class ExecuteFromAttributeEdge(ExecuteEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]


class StructureEdge(Edge):

    incoming_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
        "parser",  # Node.Types.PARSER
    ]

    def is_structure_edge(self) -> bool:
        return True

    def incoming_node(self) -> ParentNode:
        incoming_node = super().incoming_node()
        return cast(ParentNode, incoming_node)

    def outgoing_node(self) -> ChildNode:
        outgoing_node = super().outgoing_node()
        return cast(ChildNode, outgoing_node)


class RequestStartEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "HTML element",  # Node.Types.HTML_NODE
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    summary_methods = {
        "url": "url",
        "resource type": "resource_type",
    }

    def request_id(self) -> RequestId:
        return int(self.data()[Edge.RawAttrs.REQUEST_ID.value])

    def is_request_start_edge(self) -> bool:
        return True

    def incoming_node(self) -> RequesterNode:
        node = super().incoming_node()
        assert node.is_requester_node_type()
        return cast(RequesterNode, node)

    def outgoing_node(self) -> "ResourceNode":
        node = super().outgoing_node()
        if self.pg.debug:
            if not node.is_resource_node():
                self.throw("Unexpected outgoing node type")
        return cast("ResourceNode", node)

    def resource_type(self) -> "ResourceType":
        resource_type_raw = self.data()[Edge.RawAttrs.RESOURCE_TYPE.value]
        try:
            return ResourceType(resource_type_raw)
        except ValueError:
            return ResourceType.OTHER

    def url(self) -> Url:
        return self.outgoing_node().url()


class RequestResponseEdge(FrameIdAttributedEdge):

    def request_id(self) -> RequestId:
        return int(self.data()[Edge.RawAttrs.REQUEST_ID.value])

    def incoming_node(self) -> "ResourceNode":
        node = super().incoming_node()
        if self.pg.debug:
            if not node.is_resource_node():
                self.throw("Unexpected incoming node type")
        return cast("ResourceNode", node)

    def request_start_edge(self) -> "RequestStartEdge":
        request_id = self.request_id()
        request_chain = self.pg.request_chain_for_id(request_id)
        return request_chain.request


class RequestCompleteEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    summary_methods = {
        "size": "size",
        "hash": "hash",
    }

    def is_request_complete_edge(self) -> bool:
        return True

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


class RequestErrorEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    def is_request_error_edge(self) -> bool:
        return True

    def outgoing_node(self) -> RequesterNode:
        node = super().outgoing_node()
        if self.pg.debug:
            if not node.is_requester_node_type():
                self.throw("Unexpected outgoing node type")
        return cast(RequesterNode, node)

    def headers(self) -> str | None:
        try:
            return self.data()[self.RawAttrs.HEADERS.value]
        except KeyError:
            return None


class RequestRedirectEdge(RequestResponseEdge):

    incoming_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    outgoing_node_type_names = [
        "resource",  # Node.Types.RESOURCE
    ]

    def outgoing_node(self) -> "ResourceNode":
        node = super().outgoing_node()
        if self.pg.debug:
            if not node.is_resource_node():
                self.throw("Unexpected outgoing node type")
        return cast("ResourceNode", node)

    def is_request_redirect_edge(self) -> bool:
        return True

    def url(self) -> Url:
        return self.outgoing_node().url()


class NodeCreateEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
        "text node",  # Node.Types.TEXT_NODE
    ]

    def is_create_edge(self) -> bool:
        return True


class NodeInsertEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
        "text node",  # Node.Types.TEXT_NODE
    ]

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
    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT
        "parser",  # TEMP
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
        "text node",  # Node.Types.TEXT_NODE
    ]


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
