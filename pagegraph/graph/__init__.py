from functools import lru_cache
from itertools import chain
from typing import Any, cast

import networkx as NWX  # type: ignore

from pagegraph.graph.edge import Edge, NodeInsertEdge, JSCallEdge
from pagegraph.graph.edge import RequestStartEdge
from pagegraph.graph.edge import for_type as edge_for_type
from pagegraph.graph.node import for_type as node_for_type
from pagegraph.graph.node import DOMRootNode, Node, HTMLNode, ScriptNode
from pagegraph.graph.node import ParserNode, FrameOwnerNode, ResourceNode
from pagegraph.graph.node import TextNode, JSStructureNode
from pagegraph.graph.requests import RequestChain, request_chain_for_edge
from pagegraph.types import BlinkId, NodeIterator, PageGraphId, DOMNode
from pagegraph.types import ChildNode, ParentNode, EdgeIterator, FrameId
from pagegraph.types import RequestId
from pagegraph.util import check_pagegraph_version


class PageGraph:

    # Instance properties
    debug: bool = True
    graph: NWX.MultiDiGraph
    r_graph: NWX.MultiDiGraph

    __blink_id_map: dict[BlinkId, DOMNode] = {}
    __request_chain_map: dict[RequestId, RequestChain] = {}

    __nodes_by_type: dict[Node.Types, list[Node]] = {}
    __edges_by_type: dict[Edge.Types, list[Edge]] = {}
    __edge_cache: list[Edge] = []
    __edge_id_cache: dict[PageGraphId, tuple[Any, Any]] = {}

    __inserted_below_map: dict[ParentNode, list[ChildNode]] = {}
    # Mapping from a frame id to the most recent DOM node seen for the frame
    __frame_id_map: dict[FrameId, DOMRootNode] = {}

    def __init__(self, graph: NWX.MultiDiGraph, debug: bool = False):
        self.graph = graph
        self.debug = debug
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

        for node in self.dom_nodes():
            if node.is_domroot():
                domroot_node = cast(DOMRootNode, node)
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

    def unattributed_requests(self) -> list[RequestChain]:
        prefetched_requests = []
        for request_start_edge in self.request_start_edges():
            request_id = request_start_edge.request_id()
            request_chain = self.request_chain_for_id(request_id)
            prefetched_requests.append(request_chain)
        return prefetched_requests

    def request_chain_for_id(self, request_id: RequestId) -> RequestChain:
        if self.debug:
            if request_id not in self.__request_chain_map:
                raise Exception(f"Unrecognized request id: {request_id}")
        return self.__request_chain_map[request_id]

    def nodes(self) -> list[Node]:
        return [self.node(node_id) for node_id in self.graph.nodes()]

    def edges(self) -> EdgeIterator:
        if len(self.__edge_cache) > 0:
            return self.__edge_cache
        edges = []
        for u, v, edge_id in self.graph.edges:
            self.__edge_id_cache[edge_id] = (u, v)
            edges.append(self.edge(edge_id))
        self.__edge_cache = edges
        return edges

    def insert_edges(self) -> list[NodeInsertEdge]:
        edges = self.edges_of_type(Edge.Types.NODE_INSERT)
        return cast(list[NodeInsertEdge], edges)

    def request_start_edges(self) -> list[RequestStartEdge]:
        edges = self.edges_of_type(Edge.Types.REQUEST_START)
        return cast(list[RequestStartEdge], edges)

    def node_for_blink_id(self, blink_id: BlinkId) -> Node:
        if self.debug:
            if blink_id not in self.__blink_id_map:
                raise Exception(f"blink_id not in blink_id cache: {blink_id}")

        node = self.__blink_id_map[blink_id]
        if node.is_domroot():
            return cast(DOMRootNode, node)

        if not node.is_dom_node_type():
            node.throw("Unexpected blink id in mapping table")
        return cast(HTMLNode, node)

    def dom_nodes(self) -> list[DOMNode]:
        node_types = [
            Node.Types.DOM_ROOT,
            Node.Types.HTML_NODE,
            Node.Types.TEXT_NODE,
            Node.Types.FRAME_OWNER,
        ]
        nodes = []
        for node_type in node_types:
            nodes += self.nodes_of_type(node_type)
        return cast(list[DOMNode], nodes)

    def nodes_of_type(self, node_type: Node.Types) -> list[Node]:
        return self.__nodes_by_type[node_type]

    def edges_of_type(self, edge_type: Edge.Types) -> list[Edge]:
        return self.__edges_by_type[edge_type]

    def domroot_for_frame_id(self, frame_id: FrameId) -> DOMRootNode:
        if self.debug:
            if frame_id not in self.__frame_id_map:
                raise Exception(f"frame_id not in __frame_id_map:{frame_id}")
        return self.__frame_id_map[frame_id]

    def resource_nodes(self) -> list[ResourceNode]:
        node_iterator = self.nodes_of_type(Node.Types.RESOURCE)
        return cast(list[ResourceNode], node_iterator)

    def script_nodes(self) -> list[ScriptNode]:
        node_iterator = self.nodes_of_type(Node.Types.SCRIPT)
        return cast(list[ScriptNode], node_iterator)

    def html_nodes(self) -> list[HTMLNode]:
        node_iterator = self.nodes_of_type(Node.Types.HTML_NODE)
        return cast(list[HTMLNode], node_iterator)

    def parser_nodes(self) -> list[ParserNode]:
        node_iterator = self.nodes_of_type(Node.Types.PARSER)
        return cast(list[ParserNode], node_iterator)

    def frame_owner_nodes(self) -> list[FrameOwnerNode]:
        node_iterator = self.nodes_of_type(Node.Types.FRAME_OWNER)
        return cast(list[FrameOwnerNode], node_iterator)

    def domroots(self) -> list[DOMRootNode]:
        node_iterator = self.nodes_of_type(Node.Types.DOM_ROOT)
        return cast(list[DOMRootNode], node_iterator)

    def js_structure_nodes(self) -> list[JSStructureNode]:
        js_builtin_iterator = self.nodes_of_type(Node.Types.JS_BUILTIN)
        webapi_iterator = self.nodes_of_type(Node.Types.WEB_API)
        js_structures = chain(js_builtin_iterator, webapi_iterator)
        return cast(list[JSStructureNode], js_structures)

    def js_call_edges(self) -> list[JSCallEdge]:
        edge_iterator = self.edges_of_type(Edge.Types.JS_CALL)
        return cast(list[JSCallEdge], edge_iterator)

    def child_dom_nodes(self,
                        parent_node: ParentNode) -> list[ChildNode] | None:
        """Returns all nodes that were ever a child of the parent node,
        at any point during the page's lifetime."""
        if parent_node not in self.__inserted_below_map:
            return None
        return self.__inserted_below_map[parent_node]

    @lru_cache(maxsize=None)
    def node(self, node_id: PageGraphId) -> Node:
        """Loading any node object should come through this method, since
        this method is the one that knows what Node or Node subtype
        should be used."""
        node_type_str = self.graph.nodes[node_id][Node.RawAttrs.TYPE.value]
        node_type = Node.Types(node_type_str)
        node = node_for_type(node_type, self, node_id)
        if node.is_dom_node_type():
            dom_node = cast(DOMNode, node)
            self.__blink_id_map[dom_node.blink_id()] = dom_node
        return node

    @lru_cache(maxsize=None)
    def edge(self, edge_id: PageGraphId) -> Edge:
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

        if edge.is_insert_edge():
            insert_edge = cast(NodeInsertEdge, edge)
            inserted_node = insert_edge.inserted_node()
            parent_node = insert_edge.inserted_below_node()

            if parent_node not in self.__inserted_below_map:
                self.__inserted_below_map[parent_node] = []
            self.__inserted_below_map[parent_node].append(inserted_node)
        return edge

    def iframe_nodes(self) -> list[FrameOwnerNode]:
        nodes = []
        for node in self.frame_owner_nodes():
            if node.tag_name() == "IFRAME":
                nodes.append(node)
        return nodes

    def toplevel_domroot_nodes(self) -> list[DOMRootNode]:
        nodes = []
        for node in self.parser_nodes():
            if not node.is_toplevel_parser():
                continue
            for domroot_node in node.domroots():
                try:
                    if domroot_node.url() and domroot_node.frame_id():
                        nodes.append(domroot_node)
                except KeyError:
                    pass
        return nodes


def from_path(input_path: str, debug: bool = False) -> PageGraph:
    check_pagegraph_version(input_path)
    return PageGraph(NWX.read_graphml(input_path), debug)
