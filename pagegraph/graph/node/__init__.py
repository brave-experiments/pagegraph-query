from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import cast, TYPE_CHECKING

from pagegraph.misc_utils import brief_version
from pagegraph.graph.element import PageGraphElement
from pagegraph.graph.edge import Edge
from pagegraph.serialize import EdgeReport, BriefEdgeReport
from pagegraph.serialize import NodeReport, BriefNodeReport

if TYPE_CHECKING:
    from typing import Any, Optional, Union, Iterable

    from networkx import MultiDiGraph

    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge.abc.request_response import RequestResponseEdge
    from pagegraph.graph.node.abc.effector import EffectorNode
    from pagegraph.graph.edge.execute import ExecuteEdge
    from pagegraph.graph.edge.js_call import JSCallEdge
    from pagegraph.graph.edge.js_result import JSResultEdge
    from pagegraph.graph.edge.node_create import NodeCreateEdge
    from pagegraph.graph.edge.node_insert import NodeInsertEdge
    from pagegraph.graph.edge.request_complete import RequestCompleteEdge
    from pagegraph.graph.edge.request_error import RequestErrorEdge
    from pagegraph.graph.edge.request_redirect import RequestRedirectEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.graph.edge.structure import StructureEdge
    from pagegraph.graph.node.abc.dom_element import DOMElementNode
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.graph.node.abc.script import ScriptNode
    from pagegraph.graph.node.cookie_jar import CookieJarNode
    from pagegraph.graph.node.deprecated import DeprecatedNode
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.html import HTMLNode
    from pagegraph.graph.node.js_built_in import JSBuiltInNode
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.graph.node.local_storage import LocalStorageNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.graph.node.resource import ResourceNode
    from pagegraph.graph.node.script_local import ScriptLocalNode
    from pagegraph.graph.node.script_remote import ScriptRemoteNode
    from pagegraph.graph.node.session_storage import SessionStorageNode
    from pagegraph.graph.node.storage import StorageNode
    from pagegraph.graph.node.storage_area import StorageAreaNode
    from pagegraph.graph.node.text import TextNode
    from pagegraph.graph.node.unknown import UnknownNode
    from pagegraph.graph.node.web_api import WebAPINode
    from pagegraph.types import ChildDomNode, RequesterNode, LeafDomNode
    from pagegraph.types import ActorNode, JSCallingNode, Url, PageGraphId


class Node(PageGraphElement, ABC):

    # Used as class properties
    incoming_node_types: Union[list[Node.Types], None] = None
    outgoing_node_types: Union[list[Node.Types], None] = None
    incoming_edge_types: Union[list[Edge.Types], None] = None
    outgoing_edge_types: Union[list[Edge.Types], None] = None

    class Types(Enum):
        ADS_SHIELDS = "shieldsAds shield"
        COOKIE_JAR = "cookie jar"
        DOM_ROOT = "DOM root"
        EXTENSIONS = "extensions"
        FP_SHIELDS = "fingerprintingV2 shield"
        FRAME_OWNER = "frame owner"
        HTML = "HTML element"
        JS_BUILTIN = "JS builtin"
        JS_SHIELDS = "javascript shield"
        LOCAL_STORAGE = "local storage"
        PARSER = "parser"
        RESOURCE = "resource"
        SCRIPT_LOCAL = "script"
        SCRIPT_REMOTE = "remote script"
        SESSION_STORAGE = "session storage"
        SHIELDS = "Brave Shields"
        STORAGE = "storage"
        TEXT = "text node"
        TRACKERS_SHIELDS = "trackers shield"
        UNKNOWN = "unknown actor"
        WEB_API = "web API"

    class RawAttrs(Enum):
        BLINK_ID = "node id"
        FRAME_ID = "frame id"
        IS_ATTACHED = "is attached"
        METHOD = "method"
        SCRIPT_ID = "script id"
        SCRIPT_TYPE = "script type"
        SOURCE = "source"
        TIMESTAMP = "timestamp"
        TEXT = "text"
        TYPE = "node type"
        TAG = "tag name"
        URL = "url"

    def __str__(self) -> str:
        return f"node<{self.type_name()}>#{self.pg_id()}"

    def type_name(self) -> str:
        return self.data()[self.RawAttrs.TYPE.value]

    def node_type(self) -> Node.Types:
        return Node.Types(self.type_name())

    def child_nodes(self) -> list[Node]:
        return cast(list["Node"], list(self.pg.graph.adj[self._id].items()))

    def parent_nodes(self) -> list[Node]:
        return cast(list["Node"], list(self.pg.r_graph.adj[self._id].items()))

    def outgoing_edges(self) -> Iterable[Edge]:
        edges = []
        for _, edge_info in self.pg.graph.adj[self._id].items():
            for edge_id, _ in edge_info.items():
                edges.append(self.pg.edge(edge_id))
        return edges

    def incoming_edges(self) -> Iterable[Edge]:
        edges: list[Edge] = []
        for _, edge_info in self.pg.r_graph.adj[self._id].items():
            for edge_id, _ in edge_info.items():
                edges.append(self.pg.edge(edge_id))
        return edges

    def to_node_report(
            self, depth: int = 0,
            seen: None | set[Union[Node, Edge]] = None) -> NodeReport:
        if seen is None:
            seen = set([self])

        incoming_edges: None | list[EdgeReport | BriefEdgeReport | str] = None
        outgoing_edges: None | list[EdgeReport | BriefEdgeReport | str] = None
        if depth > 0:
            incoming_edges = []
            for edge in self.incoming_edges():
                if edge in seen:
                    incoming_edges.append(f"(recursion {edge.pg_id()})")
                else:
                    incoming_edges.append(edge.to_edge_report(depth - 1, seen))

            outgoing_edges = []
            for edge in self.outgoing_edges():
                if edge in seen:
                    outgoing_edges.append(f"(recursion {edge.pg_id()})")
                else:
                    outgoing_edges.append(edge.to_edge_report(depth - 1, seen))
        else:
            incoming_edges = [e.to_brief_report() for e
                              in self.incoming_edges()]
            outgoing_edges = [e.to_brief_report() for e
                              in self.outgoing_edges()]

        return NodeReport(
            self.pg_id(), self.node_type().value, self.summary_fields(),
            incoming_edges, outgoing_edges)

    def to_brief_report(self) -> BriefNodeReport:
        return BriefNodeReport(self.pg_id(), self.node_type().value,
                               self.summary_fields())

    def is_type(self, node_type: Types) -> bool:
        return self.data()[self.RawAttrs.TYPE.value] == node_type.value

    def as_child_dom_node(self) -> Optional[ChildDomNode]:
        """Returns true if this node is valid to ever be a child node for
        any other DOM node type."""
        return (
            self.as_frame_owner_node() or
            self.as_text_node() or
            self.as_html_node()
        )

    def as_requester_node(self) -> Optional[RequesterNode]:
        return (
            self.as_parser_node() or
            self.as_html_node() or
            self.as_script_local_node() or
            self.as_domroot_node()
        )

    def as_leaf_dom_node(self) -> Optional[LeafDomNode]:
        """Returns true if this is a node type that can appear in the DOM,
        and cannot have any child nodes within this frame."""
        return (
            self.as_text_node() or
            self.as_frame_owner_node()
        )

    def as_actor_node(self) -> Optional[ActorNode]:
        return (
            self.as_script_local_node() or
            self.as_parser_node()
        )

    def as_storage_area_node(self) -> Optional[StorageAreaNode]:
        return None

    def as_text_node(self) -> Optional[TextNode]:
        return None

    def as_frame_owner_node(self) -> Optional[FrameOwnerNode]:
        return None

    def as_script_node(self) -> Optional[ScriptNode]:
        return None

    def as_script_local_node(self) -> Optional[ScriptLocalNode]:
        return None

    def as_script_remote_node(self) -> Optional[ScriptRemoteNode]:
        return None

    def as_domroot_node(self) -> Optional[DOMRootNode]:
        return None

    def as_parser_node(self) -> Optional[ParserNode]:
        return None

    def as_html_node(self) -> Optional[HTMLNode]:
        return None

    def as_js_structure_node(self) -> Optional[JSStructureNode]:
        return None

    def as_resource_node(self) -> Optional[ResourceNode]:
        return None

    def as_cookie_jar_node(self) -> Optional[CookieJarNode]:
        return None

    def as_local_storage_node(self) -> Optional[LocalStorageNode]:
        return None

    def as_session_storage_node(self) -> Optional[SessionStorageNode]:
        return None

    def as_unknown_node(self) -> Optional[UnknownNode]:
        return None

    def as_executor_node(self) -> Optional[JSCallingNode]:
        return self.as_script_local_node() or self.as_unknown_node()

    def as_effector_node(self) -> Optional[EffectorNode]:
        return None

    def as_parent_dom_element_node(self) -> Optional[ParentDOMElementNode]:
        return None

    def as_dom_element_node(self) -> Optional[DOMElementNode]:
        return None

    def is_toplevel_parser(self) -> bool:
        for incoming_edge in self.incoming_edges():
            if incoming_edge.as_cross_dom_edge() is not None:
                return False
        return True

    def frame_owner_nodes(self) -> list[FrameOwnerNode]:
        frame_owner_nodes = []
        for node in self.pg.nodes():
            if frame_owner_node := node.as_frame_owner_node():
                frame_owner_nodes.append(frame_owner_node)
        return frame_owner_nodes

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.nodes[self._id])

    def creation_edge(self) -> Optional[NodeCreateEdge]:
        for edge in self.incoming_edges():
            if create_edge := edge.as_create_edge():
                return create_edge
        return None

    def created_nodes(self) -> list[Node]:
        created_nodes = []
        for edge in self.outgoing_edges():
            if edge.as_create_edge() is not None:
                created_nodes.append(edge.outgoing_node())
        return created_nodes

    def describe(self) -> str:
        output = f"node nid={self.pg_id()}\n"
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={brief_version(str(attr_value))}\n"

        output += "incoming edges:\n"
        for edge in self.incoming_edges():
            output += f"- {edge.pg_id()} - {edge.edge_type().value}\n"

        output += "outgoing edges:\n"
        for edge in self.outgoing_edges():
            output += f"- {edge.pg_id()} - {edge.edge_type().value}\n"

        return output

    def validate(self) -> bool:
        if self.__class__.incoming_node_types is not None:
            valid_incoming_node_types = self.__class__.incoming_node_types
            for edge in self.incoming_edges():
                parent_node = edge.incoming_node()
                node_type = parent_node.node_type()
                if node_type not in valid_incoming_node_types:
                    self.throw(
                        f"Unexpected incoming node: {node_type}\n"
                        f"{parent_node.node_type()}:{parent_node.pg_id()} -> "
                        f"{edge.edge_type()}:{edge.pg_id()} -> "
                        f"{self.node_type()}:{self.pg_id()}")
                    return False

        if self.__class__.outgoing_node_types is not None:
            valid_outgoing_node_types = self.__class__.outgoing_node_types
            for child_node in self.child_nodes():
                node_type = child_node.node_type()
                if node_type not in valid_outgoing_node_types:
                    self.throw(f"Unexpected outgoing node type: {node_type}")
                    return False

        if self.__class__.incoming_edge_types is not None:
            valid_incoming_edge_types = self.__class__.incoming_edge_types
            for edge in self.incoming_edges():
                edge_type = edge.edge_type()
                if edge_type not in valid_incoming_edge_types:
                    self.throw(f"Unexpected incoming edge type: {edge_type}")
                    return False

        if self.__class__.outgoing_edge_types is not None:
            valid_outgoing_edge_types = self.__class__.outgoing_edge_types
            for edge in self.outgoing_edges():
                edge_type = edge.edge_type()
                if edge_type not in valid_outgoing_edge_types:
                    self.throw(f"Unexpected outgoing edge type: {edge_type}")
                    return False
        return True

    def creator_edge(self) -> Optional[NodeCreateEdge]:
        for edge in self.incoming_edges():
            if create_edge := edge.as_create_edge():
                return create_edge
        self.throw("Could not find a creation edge for this node")
        return None

    def subgraph(self, depth: int = 1,
                 other_node: Optional[Node] = None) -> MultiDiGraph:
        node_ids: set[PageGraphId] = set()
        node_ids.add(self.pg_id())
        if other_node:
            node_ids.add(other_node.pg_id())

        for _ in range(depth):
            neighbors: set[PageGraphId] = set()
            for node_id in node_ids:
                neighbors.update(self.pg.graph.neighbors(node_id))
            node_ids.update(neighbors)

        return self.pg.graph.subgraph(node_ids)


def node_type_from_networkx_node_data(node_data: dict[str, Any]) -> Node.Types:
    type_name = node_data[Node.RawAttrs.TYPE.value]
    return Node.Types(type_name)


def url_from_network_node_data(node_data: dict[str, Any]) -> Optional[Url]:
    return node_data.get(Node.RawAttrs.URL.value)
