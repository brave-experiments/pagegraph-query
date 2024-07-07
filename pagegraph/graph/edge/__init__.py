from abc import ABC
from enum import Enum
from typing import cast, Optional
from typing import TYPE_CHECKING, Union

from pagegraph.graph.element import PageGraphElement
from pagegraph.serialize import EdgeReport, BriefEdgeReport
from pagegraph.serialize import NodeReport, BriefNodeReport

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge.attribute_delete import AttributeDeleteEdge
    from pagegraph.graph.edge.attribute_set import AttributeSetEdge
    from pagegraph.graph.edge.cross_dom import CrossDOMEdge
    from pagegraph.graph.edge.document import DocumentEdge
    from pagegraph.graph.edge.event_listener import EventListenerEdge
    from pagegraph.graph.edge.event_listener_add import EventListenerAddEdge
    from pagegraph.graph.edge.event_listener_remove import EventListenerRemoveEdge
    from pagegraph.graph.edge.execute import ExecuteEdge
    from pagegraph.graph.edge.js_call import JSCallEdge
    from pagegraph.graph.edge.js_result import JSResultEdge
    from pagegraph.graph.edge.node_create import NodeCreateEdge
    from pagegraph.graph.edge.node_insert import NodeInsertEdge
    from pagegraph.graph.edge.node_remove import NodeRemoveEdge
    from pagegraph.graph.edge.request_complete import RequestCompleteEdge
    from pagegraph.graph.edge.request_error import RequestErrorEdge
    from pagegraph.graph.edge.request_redirect import RequestRedirectEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.graph.edge.storage_bucket import StorageBucketEdge
    from pagegraph.graph.edge.storage_clear import StorageClearEdge
    from pagegraph.graph.edge.storage_delete import StorageDeleteEdge
    from pagegraph.graph.edge.storage_read_call import StorageReadCallEdge
    from pagegraph.graph.edge.storage_read_result import StorageReadResultEdge
    from pagegraph.graph.edge.storage_set import StorageSetEdge
    from pagegraph.graph.edge.structure import StructureEdge
    from pagegraph.graph.node import Node
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.html import HTMLNode
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.graph.node.resource import ResourceNode
    from pagegraph.graph.node.script import ScriptNode
    from pagegraph.graph.node.storage_area import StorageAreaNode
    from pagegraph.types import BlinkId, PageGraphEdgeKey, RequesterNode
    from pagegraph.types import ChildDomNode, ParentDomNode, FrameId, RequestId
    from pagegraph.types import PageGraphNodeId, PageGraphEdgeId, Url
    from pagegraph.types import ResourceType, AttrDomNode, ActorNode


class Edge(PageGraphElement, ABC):

    # Used as class properties
    #
    # Note that these are defined as lists of type str, but what they
    # really are is the str values for the Node.Types Enum. This
    # is necessary to prevent the dependency loop.
    # That these are valid node type enum strs is checked at runtime
    # if in debug mode.
    incoming_node_type_names: Union[list[str], None] = None  # Node.Types
    outgoing_node_type_names: Union[list[str], None] = None  # Node.Types

    # The below are automatically generated from the above,
    # but at runtime to again prevent the dependency loop.
    incoming_node_types: Union[list["Node.Types"], None] = None
    outgoing_node_types: Union[list["Node.Types"], None] = None

    @classmethod
    def make_incoming_node_types(cls) -> Union[list["Node.Types"], None]:
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
    def make_outgoing_node_types(cls) -> Union[list["Node.Types"], None]:
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
    incoming_node_id: "PageGraphNodeId"
    outgoing_node_id: "PageGraphNodeId"

    class Types(Enum):
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

    class RawAttrs(Enum):
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

    def __init__(self, graph: "PageGraph", pagegraph_id: "PageGraphEdgeId",
                 parent_id: "PageGraphNodeId", child_id: "PageGraphNodeId"):
        self.incoming_node_id = parent_id
        self.outgoing_node_id = child_id
        super().__init__(graph, pagegraph_id)

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
            self.pg_id(), self.edge_type().value, self.summary_fields(),
            incoming_node_report,
            outgoing_node_report)

    def to_brief_report(self) -> BriefEdgeReport:
        return BriefEdgeReport(self.pg_id(), self.edge_type().value,
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

    def edge_key(self) -> "PageGraphEdgeKey":
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
            one_line_attr_value = str(attr_value).replace("\n", "\\n")
            output += f"- {attr_name}={one_line_attr_value}\n"
        return output

    def validate(self) -> bool:
        valid_incoming_node_types = self.__class__.make_incoming_node_types()
        if valid_incoming_node_types is not None:
            node_type = self.incoming_node().node_type()
            if node_type not in valid_incoming_node_types:
                self.throw(f"Unexpected incoming node type: {node_type}")
                return False

        valid_outgoing_node_types = self.__class__.make_outgoing_node_types()
        if valid_outgoing_node_types is not None:
            node_type = self.outgoing_node().node_type()
            if node_type not in valid_outgoing_node_types:
                self.throw(f"Unexpected outgoing node type: {node_type}")
                return False
        return True
