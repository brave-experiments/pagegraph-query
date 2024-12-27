from __future__ import annotations

from typing import Type, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.edge.attribute_delete import AttributeDeleteEdge
from pagegraph.graph.edge.attribute_set import AttributeSetEdge
from pagegraph.graph.edge.cross_dom import CrossDOMEdge
from pagegraph.graph.edge.deprecated import DeprecatedEdge
from pagegraph.graph.edge.document import DocumentEdge
from pagegraph.graph.edge.event_listener_fired import EventListenerFiredEdge
from pagegraph.graph.edge.event_listener_add import EventListenerAddEdge
from pagegraph.graph.edge.event_listener_remove import EventListenerRemoveEdge
from pagegraph.graph.edge.execute import ExecuteEdge
from pagegraph.graph.edge.execute_from_attribute import ExecuteFromAttributeEdge
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
from pagegraph.graph.node.cookie_jar import CookieJarNode
from pagegraph.graph.node.deprecated import DeprecatedNode
from pagegraph.graph.node.dom_root import DOMRootNode
from pagegraph.graph.node.frame_owner import FrameOwnerNode
from pagegraph.graph.node.html import HTMLNode
from pagegraph.graph.node.js_built_in import JSBuiltInNode
from pagegraph.graph.node.local_storage import LocalStorageNode
from pagegraph.graph.node.parser import ParserNode
from pagegraph.graph.node.resource import ResourceNode
from pagegraph.graph.node.script_local import ScriptLocalNode
from pagegraph.graph.node.script_remote import ScriptRemoteNode
from pagegraph.graph.node.session_storage import SessionStorageNode
from pagegraph.graph.node.storage import StorageNode
from pagegraph.graph.node.text import TextNode
from pagegraph.graph.node.unknown import UnknownNode
from pagegraph.graph.node.web_api import WebAPINode

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.types import PageGraphEdgeId, PageGraphNodeId


NODE_TYPE_MAPPING: dict[Node.Types, Type[Node]] = dict([
    (Node.Types.COOKIE_JAR, CookieJarNode),
    (Node.Types.DOM_ROOT, DOMRootNode),
    (Node.Types.EXTENSIONS, DeprecatedNode),
    (Node.Types.FRAME_OWNER, FrameOwnerNode),
    (Node.Types.HTML, HTMLNode),
    (Node.Types.JS_BUILTIN, JSBuiltInNode),
    (Node.Types.LOCAL_STORAGE, LocalStorageNode),
    (Node.Types.PARSER, ParserNode),
    (Node.Types.RESOURCE, ResourceNode),
    (Node.Types.SCRIPT_LOCAL, ScriptLocalNode),
    (Node.Types.SCRIPT_REMOTE, ScriptRemoteNode),
    (Node.Types.SESSION_STORAGE, SessionStorageNode),
    (Node.Types.STORAGE, StorageNode),
    (Node.Types.TEXT, TextNode),
    (Node.Types.UNKNOWN, UnknownNode),
    (Node.Types.WEB_API, WebAPINode),

    (Node.Types.SHIELDS, DeprecatedNode),
    (Node.Types.ADS_SHIELDS, DeprecatedNode),
    (Node.Types.TRACKERS_SHIELDS, DeprecatedNode),
    (Node.Types.JS_SHIELDS, DeprecatedNode),
    (Node.Types.FP_SHIELDS, DeprecatedNode),
])

def node_for_type(node_type: Node.Types, graph: PageGraph,
                  node_id: PageGraphNodeId) -> Node:
    try:
        return NODE_TYPE_MAPPING[node_type](graph, node_id)
    except KeyError as exc:
        raise ValueError(f"Unexpected node type={node_type.value}") from exc


EDGE_TYPE_MAPPING: dict[Edge.Types, Type[Edge]] = dict([
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
    (Edge.Types.EVENT_LISTENER_FIRED, EventListenerFiredEdge),
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


def edge_for_type(edge_type: Edge.Types, graph: PageGraph,
                  edge_id: PageGraphEdgeId, parent_id: PageGraphNodeId,
                  child_id: PageGraphNodeId) -> Edge:
    try:
        return EDGE_TYPE_MAPPING[edge_type](graph, edge_id, parent_id,
                                            child_id)
    except KeyError as exc:
        raise ValueError(f"Unexpected edge type='{edge_type.value}'") from exc
