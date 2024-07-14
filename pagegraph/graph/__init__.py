from functools import lru_cache
from itertools import chain
from typing import Any, cast, Union, Optional, TYPE_CHECKING

import networkx as NWX  # type: ignore
from packaging.version import Version

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node
from pagegraph.graph.requests import request_chain_for_edge
from pagegraph.graph.type_map import edge_for_type, node_for_type
from pagegraph.versions import Feature, check_pagegraph_version
from pagegraph.versions import min_version_for_feature

if TYPE_CHECKING:
    from pagegraph.graph.edge.js_call import JSCallEdge
    from pagegraph.graph.edge.node_insert import NodeInsertEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.graph.edge.storage_clear import StorageClearEdge
    from pagegraph.graph.edge.storage_delete import StorageDeleteEdge
    from pagegraph.graph.edge.storage_set import StorageSetEdge
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.html import HTMLNode
    from pagegraph.graph.node.js_structure import JSStructureNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.graph.node.resource import ResourceNode
    from pagegraph.graph.node.script_local import ScriptLocalNode
    from pagegraph.graph.requests import RequestChain
    from pagegraph.types import BlinkId, PageGraphId, DOMNode, ChildDomNode
    from pagegraph.types import ParentDomNode, FrameId, RequestId

class PageGraph:

    # Instance properties
    debug: bool
    # Tracks the version of the graph (distinct from the version of this
    # library).
    graph_version: Union[Version, None]
    graph: NWX.MultiDiGraph
    r_graph: NWX.MultiDiGraph

    __blink_id_map: dict["BlinkId", "DOMNode"] = {}
    __request_chain_map: dict["RequestId", "RequestChain"] = {}

    __nodes_by_type: dict[Node.Types, list[Node]] = {}
    __edges_by_type: dict[Edge.Types, list[Edge]] = {}
    __edge_cache: list[Edge] = []
    __edge_id_cache: dict["PageGraphId", tuple[Any, Any]] = {}

    __inserted_below_map: dict["ParentDomNode", list["ChildDomNode"]] = {}
    # Mapping from a frame id to the most recent DOM node seen for the frame
    __frame_id_map: dict["FrameId", "DOMRootNode"] = {}

    def __init__(self, graph: NWX.MultiDiGraph,
                 version: Union[Version, None] = None, debug: bool = False):
        self.graph = graph
        self.debug = debug
        self.graph_version = version
        self.r_graph = NWX.reverse_view(graph)

        # do the below to populate the blink_id mapping dicts
        # and the frame_id to frame node mapping (we keep the most
        # recent version of each frame).
        for node_type in Node.Types:
            self.__nodes_by_type[node_type] = []
        for edge_type in Edge.Types:
            self.__edges_by_type[edge_type] = []

        for node in self.nodes():
            self.__nodes_by_type[node.node_type()].append(node)
        for edge in self.edges():
            self.__edges_by_type[edge.edge_type()].append(edge)

        # Now that we've mapped the NetworkX representation of the
        # graph into the representation defined by this library,
        # we iterate over each node and edge again, to allow
        # each element to take steps and operations only
        # safe to do once we know the entire graph is hooked up.
        for node in self.nodes():
            if self.debug:
                node.validate()
            node.build_caches()
        for edge in self.edges():
            if self.debug:
                edge.validate()
            edge.build_caches()

        self.build_caches()

    def build_caches(self) -> None:
        for node in self.dom_nodes():
            if domroot_node := node.as_domroot_node():
                blink_id = domroot_node.blink_id()
                if blink_id not in self.__frame_id_map:
                    self.__frame_id_map[blink_id] = domroot_node
                else:
                    current_node = self.__frame_id_map[blink_id]
                    if current_node.timestamp() < domroot_node.timestamp():
                        self.__frame_id_map[blink_id] = domroot_node

        for request_start_edge in self.request_start_edges():
            request_id = request_start_edge.request_id()
            self.__request_chain_map[request_id] = request_chain_for_edge(
                request_start_edge)

    def feature_check(self, feature: Feature) -> bool:
        if self.graph_version is None:
            return False
        min_graph_version = min_version_for_feature(feature)
        return self.graph_version >= min_graph_version

    def unattributed_requests(self) -> list["RequestChain"]:
        prefetched_requests = []
        for request_start_edge in self.request_start_edges():
            request_id = request_start_edge.request_id()
            request_chain = self.request_chain_for_id(request_id)
            prefetched_requests.append(request_chain)
        return prefetched_requests

    def request_chain_for_id(self, request_id: "RequestId") -> "RequestChain":
        if self.debug:
            if request_id not in self.__request_chain_map:
                raise ValueError(f"Unrecognized request id: {request_id}")
        return self.__request_chain_map[request_id]

    def nodes(self) -> list[Node]:
        return [self.node(node_id) for node_id in self.graph.nodes()]

    def edges(self) -> list[Edge]:
        if len(self.__edge_cache) > 0:
            return self.__edge_cache
        edges = []
        for u, v, edge_id in self.graph.edges:
            self.__edge_id_cache[edge_id] = (u, v)
            edges.append(self.edge(edge_id))
        self.__edge_cache = edges
        return edges

    def insert_edges(self) -> list["NodeInsertEdge"]:
        edges = self.edges_of_type(Edge.Types.NODE_INSERT)
        return cast(list["NodeInsertEdge"], edges)

    def request_start_edges(self) -> list["RequestStartEdge"]:
        edges = self.edges_of_type(Edge.Types.REQUEST_START)
        return cast(list["RequestStartEdge"], edges)

    def storage_set_edges(self) -> list["StorageSetEdge"]:
        edges = self.edges_of_type(Edge.Types.STORAGE_SET)
        return cast(list["StorageSetEdge"], edges)

    def storage_delete_edges(self) -> list["StorageDeleteEdge"]:
        edges = self.edges_of_type(Edge.Types.STORAGE_DELETE)
        return cast(list["StorageDeleteEdge"], edges)

    def storage_clear_edges(self) -> list["StorageClearEdge"]:
        edges = self.edges_of_type(Edge.Types.STORAGE_CLEAR)
        return cast(list["StorageClearEdge"], edges)

    def node_for_blink_id(self, blink_id: "BlinkId") -> "DOMNode":
        if self.debug:
            if blink_id not in self.__blink_id_map:
                raise ValueError(f"blink_id not in blink_id cache: {blink_id}")

        node = self.__blink_id_map[blink_id]
        dom_node = node.as_dom_node()
        assert dom_node is not None
        return dom_node

    def dom_nodes(self) -> list["DOMNode"]:
        node_types = [
            Node.Types.DOM_ROOT,
            Node.Types.HTML,
            Node.Types.TEXT,
            Node.Types.FRAME_OWNER,
        ]
        nodes = []
        for node_type in node_types:
            nodes += self.nodes_of_type(node_type)
        return cast(list["DOMNode"], nodes)

    def nodes_of_type(self, node_type: Node.Types) -> list["Node"]:
        return self.__nodes_by_type[node_type]

    def edges_of_type(self, edge_type: Edge.Types) -> list["Edge"]:
        return self.__edges_by_type[edge_type]

    def domroot_for_frame_id(self, frame_id: "FrameId") -> "DOMRootNode":
        if self.debug:
            if frame_id not in self.__frame_id_map:
                raise ValueError(f"frame_id not in __frame_id_map:{frame_id}")
        return self.__frame_id_map[frame_id]

    def resource_nodes(self) -> list["ResourceNode"]:
        node_iterator = self.nodes_of_type(Node.Types.RESOURCE)
        return cast(list["ResourceNode"], node_iterator)

    def script_local_nodes(self) -> list["ScriptLocalNode"]:
        node_iterator = self.nodes_of_type(Node.Types.SCRIPT_LOCAL)
        return cast(list["ScriptLocalNode"], node_iterator)

    def html_nodes(self) -> list["HTMLNode"]:
        node_iterator = self.nodes_of_type(Node.Types.HTML)
        return cast(list["HTMLNode"], node_iterator)

    def parser_nodes(self) -> list["ParserNode"]:
        node_iterator = self.nodes_of_type(Node.Types.PARSER)
        return cast(list["ParserNode"], node_iterator)

    def frame_owner_nodes(self) -> list["FrameOwnerNode"]:
        node_iterator = self.nodes_of_type(Node.Types.FRAME_OWNER)
        return cast(list["FrameOwnerNode"], node_iterator)

    def domroot_nodes(self) -> list["DOMRootNode"]:
        node_iterator = self.nodes_of_type(Node.Types.DOM_ROOT)
        return cast(list["DOMRootNode"], node_iterator)

    def js_structure_nodes(self) -> list["JSStructureNode"]:
        js_builtin_iterator = self.nodes_of_type(Node.Types.JS_BUILTIN)
        webapi_iterator = self.nodes_of_type(Node.Types.WEB_API)
        js_structures = chain(js_builtin_iterator, webapi_iterator)
        return cast(list["JSStructureNode"], js_structures)

    def js_call_edges(self) -> list["JSCallEdge"]:
        edge_iterator = self.edges_of_type(Edge.Types.JS_CALL)
        return cast(list["JSCallEdge"], edge_iterator)

    def child_dom_nodes(
            self, parent_node: "ParentDomNode") -> Optional[list["ChildDomNode"]]:
        """Returns all nodes that were ever a child of the parent node,
        at any point during the page's lifetime."""
        if parent_node not in self.__inserted_below_map:
            return None
        return self.__inserted_below_map[parent_node]

    @lru_cache(maxsize=None)
    def node(self, node_id: "PageGraphId") -> Node:
        """Loading any node object should come through this method, since
        this method is the one that knows what Node or Node subtype
        should be used."""
        node_type_str = self.graph.nodes[node_id][Node.RawAttrs.TYPE.value]
        node_type = Node.Types(node_type_str)
        node = node_for_type(node_type, self, node_id)
        if dom_node := node.as_dom_node():
            self.__blink_id_map[dom_node.blink_id()] = dom_node
        return node

    @lru_cache(maxsize=None)
    def edge(self, edge_id: "PageGraphId") -> Edge:
        """Loading any edge object should come through this method, since
        this method is the one that knows what Edge or Edge subtype
        should be used."""
        parent_id, child_id = self.__edge_id_cache[edge_id]
        edge_key = (parent_id, child_id, edge_id)
        edge_data = self.graph.edges[edge_key]
        edge_type_str = edge_data[Edge.RawAttrs.TYPE.value]
        edge_type = Edge.Types(edge_type_str)
        init_args = [self, edge_id, parent_id, child_id]
        edge = edge_for_type(edge_type, *init_args)

        if insert_edge := edge.as_insert_edge():
            inserted_node = insert_edge.inserted_node()
            parent_node = insert_edge.inserted_below_node()

            if parent_node not in self.__inserted_below_map:
                self.__inserted_below_map[parent_node] = []
            self.__inserted_below_map[parent_node].append(inserted_node)
        return edge

    def iframe_nodes(self) -> list["FrameOwnerNode"]:
        nodes = []
        for node in self.frame_owner_nodes():
            if node.tag_name() == "IFRAME":
                nodes.append(node)
        return nodes

    def toplevel_domroot_nodes(self) -> list["DOMRootNode"]:
        domroot_nodes = []
        for domroot_node in self.domroot_nodes():
            if domroot_node.is_top_level_domroot():
                domroot_nodes.append(domroot_node)
        return domroot_nodes


def from_path(input_path: str, debug: bool = False) -> PageGraph:
    graph_version = check_pagegraph_version(input_path)
    return PageGraph(NWX.read_graphml(input_path), graph_version, debug)
