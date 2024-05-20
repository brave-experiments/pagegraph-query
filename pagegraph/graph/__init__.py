from functools import lru_cache
from itertools import chain
from typing import Any, cast, Dict, Iterable, List, Tuple

import networkx as NWX  # type: ignore

from pagegraph.graph.edge import Edge, NodeInsertEdge, JSCallEdge
from pagegraph.graph.edge import for_type as edge_for_type
from pagegraph.graph.node import for_type as node_for_type
from pagegraph.graph.node import DOMRootNode, Node, HTMLNode, ScriptNode
from pagegraph.graph.node import ParserNode, FrameOwnerNode, ResourceNode
from pagegraph.graph.node import TextNode, JSStructureNode
from pagegraph.graph.types import BlinkId, NodeIterator, PageGraphId, DOMNode
from pagegraph.graph.types import ChildNode, ParentNode, EdgeIterator, FrameId
from pagegraph.util import check_pagegraph_version


class PageGraph:

    debug: bool = True
    graph: NWX.MultiDiGraph
    r_graph: NWX.MultiDiGraph
    blink_id_mapping: Dict[BlinkId, DOMNode] = {}

    nodes_by_type: Dict[Node.Types, List[Node]] = {}
    edges_by_type: Dict[Edge.Types, List[Edge]] = {}
    edge_cache: List[Edge] = []
    edge_id_cache: Dict[PageGraphId, Tuple[Any, Any]] = {}

    inserted_below_mapping: Dict[ParentNode, List[ChildNode]] = {}
    # Mapping from a frame id to the most recent DOM node seen for the frame
    frame_id_mapping: Dict[FrameId, DOMRootNode] = {}

    def __init__(self, graph: NWX.MultiDiGraph, debug: bool = False):
        self.graph = graph
        self.debug = debug
        self.r_graph = NWX.reverse_view(graph)

        # do the below to populate the blink_id mapping dicts
        # and the frame_id to frame node mapping (we keep the most
        # recent version of each frame).
        for node_type in Node.Types:
            self.nodes_by_type[node_type] = []
        for edge_type in Edge.Types:
            self.edges_by_type[edge_type] = []

        for node in self.nodes():
            self.nodes_by_type[node.node_type()].append(node)
        for edge in self.edges():
            self.edges_by_type[edge.edge_type()].append(edge)

        # We iterate over nodes a second time if we're in debug mode
        # because some internal checks are dependent on caches
        # having already seen other nodes, and so this removes those cycles.
        if self.debug:
            for node in self.nodes():
                node.validate()

        for node in self.dom_nodes():
            if node.is_domroot():
                domroot_node = cast(DOMRootNode, node)
                blink_id = domroot_node.blink_id()
                if blink_id not in self.frame_id_mapping:
                    self.frame_id_mapping[blink_id] = domroot_node
                else:
                    current_node = self.frame_id_mapping[blink_id]
                    if current_node.timestamp() < domroot_node.timestamp():
                        self.frame_id_mapping[blink_id] = domroot_node

        # Finally, populate the mapping of what nodes were ever inserted
        # below another node, during the document's lifetime
        for edge in self.insert_edges():
            pass

    def nodes(self) -> list[Node]:
        return [self.node(node_id) for node_id in self.graph.nodes()]

    def edges(self) -> EdgeIterator:
        if len(self.edge_cache) > 0:
            return self.edge_cache
        edges = []
        for u, v, edge_id in self.graph.edges:
            self.edge_id_cache[edge_id] = (u, v)
            edges.append(self.edge(edge_id))
        self.edge_cache = edges
        return edges

    def insert_edges(self) -> Iterable[NodeInsertEdge]:
        return [cast(NodeInsertEdge, e) for e in
                self.edges_of_type(Edge.Types.NODE_INSERT)]

    def node_for_blink_id(self, blink_id: BlinkId) -> Node:
        if self.debug:
            if blink_id not in self.blink_id_mapping:
                raise Exception(f"blink_id not in blink_id cache: {blink_id}")

        node = self.blink_id_mapping[blink_id]
        if node.is_domroot():
            return cast(DOMRootNode, node)

        if not node.is_dom_node_type():
            node.throw("Unexpected blink id in mapping table")
        return cast(HTMLNode, node)

    def dom_nodes(self) -> List[DOMNode]:
        node_types = [
            Node.Types.DOM_ROOT,
            Node.Types.HTML_NODE,
            Node.Types.TEXT_NODE,
            Node.Types.FRAME_OWNER,
        ]
        nodes = []
        for node_type in node_types:
            nodes += self.nodes_of_type(node_type)
        return cast(List[DOMNode], nodes)

    def nodes_of_type(self, node_type: Node.Types) -> List[Node]:
        return self.nodes_by_type[node_type]

    def edges_of_type(self, edge_type: Edge.Types) -> List[Edge]:
        return self.edges_by_type[edge_type]

    def domroot_for_frame_id(self, frame_id: FrameId) -> DOMRootNode:
        if self.debug:
            if frame_id not in self.frame_id_mapping:
                raise Exception(f"frame_id not in frame_id_mapping:{frame_id}")
        return self.frame_id_mapping[frame_id]

    def resource_nodes(self) -> Iterable[ResourceNode]:
        node_iterator = self.nodes_of_type(Node.Types.RESOURCE)
        return cast(Iterable[ResourceNode], node_iterator)

    def script_nodes(self) -> Iterable[ScriptNode]:
        node_iterator = self.nodes_of_type(Node.Types.SCRIPT)
        return cast(Iterable[ScriptNode], node_iterator)

    def html_nodes(self) -> Iterable[HTMLNode]:
        node_iterator = self.nodes_of_type(Node.Types.HTML_NODE)
        return cast(Iterable[HTMLNode], node_iterator)

    def parser_nodes(self) -> Iterable[ParserNode]:
        node_iterator = self.nodes_of_type(Node.Types.PARSER)
        return cast(Iterable[ParserNode], node_iterator)

    def frame_owner_nodes(self) -> Iterable[FrameOwnerNode]:
        node_iterator = self.nodes_of_type(Node.Types.FRAME_OWNER)
        return cast(Iterable[FrameOwnerNode], node_iterator)

    def domroots(self) -> Iterable[DOMRootNode]:
        node_iterator = self.nodes_of_type(Node.Types.DOM_ROOT)
        return cast(Iterable[DOMRootNode], node_iterator)

    def js_structure_nodes(self) -> Iterable[JSStructureNode]:
        js_builtin_iterator = self.nodes_of_type(Node.Types.JS_BUILTIN)
        webapi_iterator = self.nodes_of_type(Node.Types.WEB_API)
        js_structures = chain(js_builtin_iterator, webapi_iterator)
        return cast(Iterable[JSStructureNode], js_structures)

    def js_call_edges(self) -> Iterable[JSCallEdge]:
        edge_iterator = self.edges_of_type(Edge.Types.JS_CALL)
        return cast(Iterable[JSCallEdge], edge_iterator)

    def child_dom_nodes(self,
                        parent_node: ParentNode) -> List[ChildNode] | None:
        """Returns all nodes that were ever a child of the parent node,
        at any point during the page's lifetime."""
        if parent_node not in self.inserted_below_mapping:
            return None
        return self.inserted_below_mapping[parent_node]

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
            self.blink_id_mapping[dom_node.blink_id()] = dom_node
        return node

    @lru_cache(maxsize=None)
    def edge(self, edge_id: PageGraphId) -> Edge:
        """Loading any edge object should come through this method, since
        this method is the one that knows what Edge or Edge subtype
        should be used."""
        parent_id, child_id = self.edge_id_cache[edge_id]
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

            if parent_node not in self.inserted_below_mapping:
                self.inserted_below_mapping[parent_node] = []
            self.inserted_below_mapping[parent_node].append(inserted_node)
        return edge

    def iframe_nodes(self) -> List[FrameOwnerNode]:
        nodes = []
        for node in self.frame_owner_nodes():
            if node.tag_name() == "IFRAME":
                nodes.append(node)
        return nodes

    def toplevel_domroot_nodes(self) -> List[DOMRootNode]:
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
