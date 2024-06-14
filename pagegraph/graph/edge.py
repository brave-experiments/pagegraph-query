from abc import ABC
from enum import StrEnum
from json import loads, JSONDecodeError
from typing import Any, cast, Dict, List, Optional, TypeVar, Type
from typing import TYPE_CHECKING, Union

from pagegraph.graph.element import PageGraphElement
from pagegraph.types import PageGraphNodeId, PageGraphEdgeId, Url
from pagegraph.types import BlinkId, PageGraphEdgeKey, RequesterNode
from pagegraph.types import ChildDOMNode, ParentDOMNode, FrameId, RequestId
from pagegraph.types import ResourceType, AttrDOMNode, ActorNode
from pagegraph.serialize import EdgeReport, BriefEdgeReport
from pagegraph.serialize import NodeReport, BriefNodeReport
from pagegraph.versions import Feature


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.node import Node, ScriptNode, DOMRootNode, HTMLNode
    from pagegraph.graph.node import JSStructureNode, ResourceNode, ParserNode
    from pagegraph.graph.node import FrameOwnerNode, StorageAreaNode


class Edge(PageGraphElement, ABC):

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
        DOCUMENT = "document"
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
        KEY = "key"
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
                incoming_node_report = f"(recursion {incoming_node.pg_id()})"
            elif depth > 0:
                incoming_node_report = incoming_node.to_node_report(depth - 1)
            else:
                incoming_node_report = incoming_node.to_brief_report()

        outgoing_node = self.outgoing_node()
        outgoing_node_report: None | NodeReport | BriefNodeReport | str = None
        if outgoing_node:
            if outgoing_node in seen:
                outgoing_node_report = f"(recursion {outgoing_node.pg_id()})"
            if depth > 0:
                outgoing_node_report = outgoing_node.to_node_report(depth - 1)
            else:
                outgoing_node_report = outgoing_node.to_brief_report()

        return EdgeReport(
            self.pg_id(), self.edge_type(), self.summary_fields(),
            incoming_node_report,
            outgoing_node_report)

    def to_brief_report(self) -> BriefEdgeReport:
        return BriefEdgeReport(self.pg_id(), self.edge_type(),
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

    def as_insert_edge(self) -> Optional["NodeInsertEdge"]:
        return None

    def as_structure_edge(self) -> Optional["StructureEdge"]:
        return None

    def as_create_edge(self) -> Optional["NodeCreateEdge"]:
        return None

    def as_execute_edge(self) -> Optional["ExecuteEdge"]:
        return None

    def as_cross_dom_edge(self) -> Optional["CrossDOMEdge"]:
        return None

    def as_request_start_edge(self) -> Optional["RequestStartEdge"]:
        return None

    def as_request_complete_edge(self) -> Optional["RequestCompleteEdge"]:
        return None

    def as_request_error_edge(self) -> Optional["RequestErrorEdge"]:
        return None

    def as_request_redirect_edge(self) -> Optional["RequestRedirectEdge"]:
        return None

    def as_attribute_set_edge(self) -> Optional["AttributeSetEdge"]:
        return None

    def as_attribute_delete_edge(self) -> Optional["AttributeDeleteEdge"]:
        return None

    def as_document_edge(self) -> Optional["DocumentEdge"]:
        return None

    def as_node_remove_edge(self) -> Optional["NodeRemoveEdge"]:
        return None

    def as_event_listener_edge(self) -> Optional["EventListenerEdge"]:
        return None

    def as_event_listener_add_edge(self) -> Optional["EventListenerAddEdge"]:
        return None

    def as_event_listener_remove_edge(self) -> Optional[
            "EventListenerRemoveEdge"]:
        return None

    def as_storage_bucket_edge(self) -> Optional["StorageBucketEdge"]:
        return None

    def as_storage_read_call_edge(self) -> Optional["StorageReadCallEdge"]:
        return None

    def as_storage_read_result_edge(self) -> Optional["StorageReadResultEdge"]:
        return None

    def as_storage_set_edge(self) -> Optional["StorageSetEdge"]:
        return None

    def as_storage_clear_edge(self) -> Optional["StorageClearEdge"]:
        return None

    def as_storage_delete_edge(self) -> Optional["StorageDeleteEdge"]:
        return None

    def as_js_call_edge(self) -> Optional["JSCallEdge"]:
        return None

    def as_js_result_edge(self) -> Optional["JSResultEdge"]:
        return None

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.edges[self.edge_key()])

    def edge_key(self) -> PageGraphEdgeKey:
        return self.incoming_node_id, self.outgoing_node_id, self._id

    def describe(self) -> str:
        in_node = self.incoming_node()
        out_node = self.outgoing_node()

        output = f"edge eid={self.pg_id()}\n"
        output += (
            f"- incoming: {in_node.node_type()}, {in_node.pg_id()}\n"
            f"- outgoing: {out_node.node_type()}, {out_node.pg_id()}\n"
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


class FrameIdAttributedEdge(Edge, ABC):

    def domroot_for_frame_id(self) -> "DOMRootNode":
        frame_id = self.frame_id()
        return self.pg.domroot_for_frame_id(frame_id)

    def frame_id(self) -> FrameId:
        if self.pg.debug:
            if self.RawAttrs.FRAME_ID.value not in self.data():
                self.throw("No frame id recorded")
        return int(self.data()[self.RawAttrs.FRAME_ID.value])


class AttributeEdge(FrameIdAttributedEdge, ABC):

    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT
        "parser",  # TEMP
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
    ]

    def key(self) -> str:
        return self.data()[self.RawAttrs.KEY]

    def incoming_node(self) -> ActorNode:
        incoming_node = super().incoming_node()
        actor_node = incoming_node.as_actor_node()
        assert actor_node
        return actor_node

    def outgoing_node(self) -> AttrDOMNode:
        outgoing_node = super().outgoing_node()
        node = outgoing_node.as_attributable_dom_node()
        assert node
        return node


class AttributeDeleteEdge(AttributeEdge):

    def as_attribute_delete_edge(self) -> Optional["AttributeDeleteEdge"]:
        return self


class AttributeSetEdge(AttributeEdge):

    def as_attribute_set_edge(self) -> Optional["AttributeSetEdge"]:
        return self

    def value(self) -> str:
        return self.data()[self.RawAttrs.VALUE]


class CrossDOMEdge(Edge):

    incoming_node_type_names = [
        "frame owner",  # Node.Types.FRAME_OWNER
    ]

    # Note that the correct values for edges differs depending on
    # graph version.
    outgoing_node_type_names = None

    def validate(self) -> bool:
        if self.__class__.outgoing_node_type_names is not None:
            return super().validate()

        if self.pg.feature_check(
                Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS):
            self.__class__.outgoing_node_type_names = ["DOM root"]
        else:
            self.__class__.outgoing_node_type_names = ["parser"]
        return super().validate()

    def as_cross_dom_edge(self) -> Optional["CrossDOMEdge"]:
        return self

    def incoming_node(self) -> "FrameOwnerNode":
        incoming_node = super().incoming_node().as_frame_owner_node()
        assert incoming_node
        return incoming_node

    def outgoing_node(self) -> Union["DOMRootNode", "ParserNode"]:
        # Note that even though we can be sure which of these the outgoing
        # node will be, it'll differ across graph versions, so we
        # have to be ambagious for now.
        outgoing_node = super().outgoing_node()
        return_node = (
            outgoing_node.as_domroot_node() or
            outgoing_node.as_parser_node()
        )
        assert return_node
        return return_node


class DocumentEdge(Edge):

    def as_document_edge(self) -> Optional["DocumentEdge"]:
        return self

    def incoming_node(self) -> ParentDOMNode:
        incoming_node = super().incoming_node()
        parent_dom_node = incoming_node.as_parent_dom_node()
        assert parent_dom_node
        return parent_dom_node

    def outgoing_node(self) -> ChildDOMNode:
        outgoing_node = super().outgoing_node()
        child_dom_node = outgoing_node.as_child_dom_node()
        assert child_dom_node
        return child_dom_node


class ExecuteEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
        "DOM root",  # Node.Types.HTML_NODE
        "frame owner",  # Node.Types.FRAME_OWNER
        # Encodes JS URLs
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]

    def as_execute_edge(self) -> Optional["ExecuteEdge"]:
        return self

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        script_node = outgoing_node.as_script_node()
        assert script_node
        return script_node


class ExecuteFromAttributeEdge(ExecuteEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]


class StructureEdge(Edge):

    # Note that the correct values for edges differs depending on
    # graph version.
    incoming_node_type_names = None

    def validate(self) -> bool:
        if self.__class__.incoming_node_type_names:
            return super().validate()

        if self.pg.feature_check(Feature.DOCUMENT_EDGES):
            self.__class__.incoming_node_type_names = ["parser"]
            self.__class__.outgoing_node_type_names = [
                "extensions",  # Node.Types.EXTENSIONS
                "DOM root",  # Node.Types.DOM_ROOT
            ]
        else:
            self.__class__.incoming_node_type_names = [
                "DOM root",  # Node.Types.DOM_ROOT
                "frame owner",  # Node.Types.FRAME_OWNER
                "HTML element",  # Node.Types.HTML_NODE
                "parser",  # Node.Types.PARSER
            ]
        return super().validate()

    def as_structure_edge(self) -> Optional["StructureEdge"]:
        return self


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

    def as_request_start_edge(self) -> Optional["RequestStartEdge"]:
        return self

    def incoming_node(self) -> RequesterNode:
        node = super().incoming_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

    def outgoing_node(self) -> "ResourceNode":
        node = super().outgoing_node()
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

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
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

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

    def as_request_complete_edge(self) -> Optional["RequestCompleteEdge"]:
        return self

    def outgoing_node(self) -> RequesterNode:
        node = super().outgoing_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

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

    def as_request_error_edge(self) -> Optional["RequestErrorEdge"]:
        return self

    def outgoing_node(self) -> RequesterNode:
        node = super().outgoing_node()
        requester_node = node.as_requester_node()
        assert requester_node
        return requester_node

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
        resource_node = node.as_resource_node()
        assert resource_node
        return resource_node

    def as_request_redirect_edge(self) -> Optional["RequestRedirectEdge"]:
        return self

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

    def incoming_node(self) -> ActorNode:
        incoming_node = super().incoming_node()
        actor_node = incoming_node.as_actor_node()
        assert actor_node
        return actor_node

    def as_create_edge(self) -> Optional["NodeCreateEdge"]:
        return self

    def validate(self) -> bool:
        # The only times we should see a 0-reported frame id are for
        # frames that are created automatically by blink (e.g.,
        # when a frame is being set up for the to level frame, or
        # when an iframe is being created by a script, before its
        # been populated or loaded).
        frame_id = self.frame_id()
        outgoing_node = self.outgoing_node()
        if frame_id == 0 and outgoing_node.as_domroot_node() is None:
            return False
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

    def as_insert_edge(self) -> Optional["NodeInsertEdge"]:
        return self

    def inserted_before_blink_id(self) -> Optional[BlinkId]:
        value = self.data()[Edge.RawAttrs.BEFORE_BLINK_ID]
        if value:
            return int(value)
        else:
            return None

    def inserted_before_node(self) -> Optional["Node"]:
        blink_id = self.inserted_before_blink_id()
        if not blink_id:
            return None
        node = self.pg.node_for_blink_id(blink_id)
        return node

    def inserted_below_blink_id(self) -> BlinkId:
        return int(self.data()[Edge.RawAttrs.PARENT_BLINK_ID])

    def inserted_below_node(self) -> ParentDOMNode:
        blink_id = self.inserted_below_blink_id()
        node = self.pg.node_for_blink_id(blink_id)
        parent_node = node.as_parent_dom_node()
        assert parent_node
        return parent_node

    def inserted_node(self) -> ChildDOMNode:
        node = self.outgoing_node()
        child_dom_node = node.as_child_dom_node()
        assert child_dom_node
        return child_dom_node


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

    def as_node_remove_edge(self) -> Optional["NodeRemoveEdge"]:
        return self


class EventListenerEdge(Edge):
    def as_event_listener_edge(self) -> Optional["EventListenerEdge"]:
        return self


class EventListenerAddEdge(FrameIdAttributedEdge):
    def as_event_listener_add_edge(self) -> Optional["EventListenerAddEdge"]:
        return self


class EventListenerRemoveEdge(FrameIdAttributedEdge):
    def as_event_listener_remove_edge(self) -> Optional[
            "EventListenerRemoveEdge"]:
        return self


class StorageBucketEdge(Edge):
    def as_storage_bucket_edge(self) -> Optional["StorageBucketEdge"]:
        return self


class StorageCallEdge(FrameIdAttributedEdge, ABC):

    incoming_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "local storage",  # Node.Types.LOCAL_STORAGE
        "session storage",  # Node.Types.SESSION_STORAGE
        "cookie jar",  # Node.Types.COOKIE_JAR
    ]

    def incoming_node(self) -> "ScriptNode":
        script_node = super().incoming_node().as_script_node()
        assert script_node
        return script_node

    def outgoing_node(self) -> "StorageAreaNode":
        outgoing_node = super().outgoing_node().as_storage_area_node()
        assert outgoing_node
        return outgoing_node


class StorageReadCallEdge(StorageCallEdge):
    def as_storage_read_call_edge(self) -> Optional["StorageReadCallEdge"]:
        return self

    def key(self) -> str:
        return self.data()[Edge.RawAttrs.KEY.value]


class StorageReadResultEdge(FrameIdAttributedEdge):
    def as_storage_read_result_edge(self) -> Optional["StorageReadResultEdge"]:
        return self

    def value(self) -> str:
        return self.data()[Edge.RawAttrs.VALUE.value]


class StorageSetEdge(StorageCallEdge):
    def as_storage_set_dge(self) -> Optional["StorageSetEdge"]:
        return self

    def key(self) -> str:
        return self.data()[Edge.RawAttrs.KEY.value]

    def value(self) -> str:
        return self.data()[Edge.RawAttrs.VALUE.value]


class StorageClearEdge(StorageCallEdge):
    def as_storage_clear_edge(self) -> Optional["StorageClearEdge"]:
        return self


class StorageDeleteEdge(StorageCallEdge):
    def as_storage_delete_edge(self) -> Optional["StorageDeleteEdge"]:
        return self

    def key(self) -> str:
        return self.data()[Edge.RawAttrs.KEY.value]


class JSCallEdge(FrameIdAttributedEdge):

    def args(self) -> Any:
        args_raw = self.data()[Edge.RawAttrs.ARGS.value]
        return_result = None
        try:
            return_result = loads(args_raw)
        except JSONDecodeError:
            return_result = args_raw
        return return_result

    def as_js_call_edge(self) -> Optional["JSCallEdge"]:
        return self

    def incoming_node(self) -> "ScriptNode":
        incoming_node = super().incoming_node()
        script_node = incoming_node.as_script_node()
        assert script_node
        return script_node

    def outgoing_node(self) -> "JSStructureNode":
        outgoing_node = super().outgoing_node()
        js_structure_node = outgoing_node.as_js_structure_node()
        assert js_structure_node
        return js_structure_node


class JSResultEdge(FrameIdAttributedEdge):

    def value(self) -> Any:
        value_raw = self.data()[Edge.RawAttrs.VALUE.value]
        try:
            return loads(value_raw)
        except JSONDecodeError:
            return value_raw

    def as_js_result_edge(self) -> Optional["JSResultEdge"]:
        return self

    def outgoing_node(self) -> "ScriptNode":
        outgoing_node = super().outgoing_node()
        script_node = outgoing_node.as_script_node()
        assert script_node
        return script_node

    def incoming_node(self) -> "JSStructureNode":
        incoming_node = super().incoming_node()
        js_structure_node = incoming_node.as_js_structure_node()
        assert js_structure_node
        return js_structure_node


class DeprecatedEdge(Edge):
    pass


TYPE_MAPPING: Dict[Edge.Types, Type[Edge]] = dict([
    (Edge.Types.ATTRIBUTE_DELETE, AttributeDeleteEdge),
    (Edge.Types.ATTRIBUTE_SET, AttributeSetEdge),
    (Edge.Types.CROSS_DOM, CrossDOMEdge),
    (Edge.Types.DOCUMENT, DocumentEdge),
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
