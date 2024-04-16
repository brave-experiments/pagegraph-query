from functools import lru_cache
from typing import Any, cast, Dict, Iterable, List

import networkx as NWX # type: ignore

from pagegraph.graph.edge import Edge, NodeInsertEdge
from pagegraph.graph.edge import for_type as edge_for_type
from pagegraph.graph.node import for_type as node_for_type
from pagegraph.graph.node import DOMRootNode, Node, HTMLNode, ScriptNode
from pagegraph.graph.node import ParserNode, FrameOwnerNode, ResourceNode
from pagegraph.graph.node import TextNode
from pagegraph.graph.types import BlinkId, NodeIterator, PageGraphId, DOMNode
from pagegraph.graph.types import ChildNode, ParentNode, EdgeIterator, FrameId


class PageGraph:

    graph: NWX.MultiDiGraph
    r_graph: NWX.MultiDiGraph
    blink_id_mapping: Dict[BlinkId, DOMNode] = {}

    nodes_by_type: Dict[Node.Types, List[Node]] = {}
    edges_by_type: Dict[Edge.Types, List[Edge]] = {}

    inserted_below_mapping: Dict[ParentNode, List[ChildNode]] = {}
    # Mapping from a frame id to the most recent DOM node seen for the frame
    frame_id_mapping: Dict[FrameId, DOMRootNode] = {}

    def __init__(self, graph: NWX.MultiDiGraph):
        print("start")
        self.graph = graph
        self.r_graph = NWX.reverse_view(graph)
        # do the below to populate the blink_id mapping dicts
        # and the frame_id to frame node mapping (we keep the most
        # recent version of each frame).
        for node in self.nodes():
            try:
                self.nodes_by_type[node.node_type()].append(node)
            except KeyError:
                self.nodes_by_type[node.node_type()] = [node]

        print('start edge cache')
        for edge in self.edges():
            try:
                self.edges_by_type[edge.edge_type()].append(edge)
            except KeyError:
                self.edges_by_type[edge.edge_type()] = [edge]

        print('here')
        for node in self.dom_nodes():
            if node.is_domroot():
                domroot_node = cast(DOMRootNode, node)
                frame_id = domroot_node.frame_id()
                if frame_id not in self.frame_id_mapping:
                    self.frame_id_mapping[frame_id] = domroot_node
                else:
                    current_node = self.frame_id_mapping[frame_id]
                    if current_node.timestamp() < domroot_node.timestamp():
                        self.frame_id_mapping[frame_id] = domroot_node
        print('there')
        # Finally, populate the mapping of what nodes were ever inserted
        # below another node, during the document's lifetime
        for insert_edge in self.insert_edges():
            pass
        print("end")

    def nodes(self) -> NodeIterator:
        for node_id in self.graph.nodes():
            yield self.node(node_id)

    def edges(self) -> EdgeIterator:
        for _, _, edge_id in self.graph.edges:
            yield self.edge(edge_id)

    def insert_edges(self) -> Iterable[NodeInsertEdge]:
        for edge in self.edges_of_type(Edge.Types.NODE_INSERT):
            return cast(NodeInsertEdge, node)

    def node_for_blink_id(self, blink_id: BlinkId) -> Node:
        assert blink_id in self.blink_id_mapping
        node = self.blink_id_mapping[blink_id]
        if node.is_domroot():
            return cast(DOMRootNode, node)

        if not node.is_dom_node_type():
            node.throw("Unexpected blink id in mapping table")
        return cast(HTMLNode, node)

    def dom_nodes(self) -> Iterable[DOMNode]:
        type_mapping = (
            (Node.Types.DOM_ROOT, DOMRootNode),
            (Node.Types.HTML_NODE, HTMLNode),
            (Node.Types.TEXT_NODE, TextNode),
            (Node.Types.FRAME_OWNER, FrameOwnerNode),
        )
        for node_type, node_class in type_mapping:
            for node in self.nodes_by_type[node_type]:
                yield cast(node_class, node)

    def nodes_of_type(self, node_type: Node.Types) -> NodeIterator:
        for node in self.nodes_by_type[node_type]:
            yield node

    def edges_of_type(self, edge_type: Edge.Types) -> EdgeIterator:
        for edge in self.edges_by_type[edge_type]:
            yield edge

    def domroot_for_frame_id(self, frame_id: FrameId) -> DOMRootNode:
        assert frame_id in self.frame_id_mapping
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

    def child_dom_nodes(self, parent_node: ParentNode) -> Iterable[ChildNode] | None:
        """Returns all nodes that were ever a child of the parent node,
        at any point during the page's lifetime."""
        if parent_node not in self.inserted_below_mapping:
            return None
        for child_node in self.inserted_below_mapping[parent_node]:
            yield child_node

    @lru_cache(maxsize=None)
    def node(self, node_id: PageGraphId) -> Node:
        """Loading any node object should come through this method, since
        this method is the one that knows what Node or Node subtype
        should be used."""
        assert node_id in self.graph.nodes
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
        for parent_id, child_id, eid in self.graph.edges:
            if edge_id != eid:
                continue
            init_args = [self, eid, parent_id, child_id]
            edge_key = (parent_id, child_id, eid)
            edge_data = self.graph.edges[edge_key]
            edge_type_str = edge_data[Edge.RawAttrs.TYPE.value]
            edge_type = Edge.Types(edge_type_str)
            edge = edge_for_type(edge_type, *init_args)

            if edge.is_insert_edge():
                insert_edge = cast(NodeInsertEdge, edge)
                inserted_node = insert_edge.inserted_node()
                parent_node = insert_edge.inserted_below_node()

                if parent_node not in self.inserted_below_mapping:
                    self.inserted_below_mapping[parent_node] = []
                self.inserted_below_mapping[parent_node].append(inserted_node)
            return edge

        raise ValueError(f'No edge with id {edge_id} found')

    def iframe_nodes(self) -> Iterable[FrameOwnerNode]:
        for node in self.frame_owner_nodes():
            if node.tag_name() == "IFRAME":
                yield node

    def toplevel_domroot_nodes(self) -> Iterable[DOMRootNode]:
        for node in self.parser_nodes():
            if not node.is_toplevel_parser():
                continue
            for domroot_node in node.domroots():
                try:
                    if domroot_node.url() and domroot_node.frame_id():
                        yield domroot_node
                except KeyError:
                    pass


def from_path(input_path: str) -> PageGraph:
    return PageGraph(NWX.read_graphml(input_path))