from functools import lru_cache
from typing import cast, Iterable

import networkx as NWX # type: ignore

from pagegraph.graph.edge import Edge, InsertNodeEdge
from pagegraph.graph.edge import for_type as edge_for_type
from pagegraph.graph.node import for_type as node_for_type
from pagegraph.graph.node import DOMRootNode, Node, HTMLNode, ScriptNode
from pagegraph.graph.node import  ParserNode, FrameOwnerNode
from pagegraph.graph.types import BlinkId, NodeIterator, PageGraphId
from pagegraph.graph.types import ParentNode, ChildNode, EdgeIterator


class PageGraph:

    graph: NWX.MultiDiGraph
    r_graph: NWX.MultiDiGraph
    blink_id_mapping: dict[BlinkId, Node] = {}
    inserted_below_mapping: dict[Node, list[ChildNode]] = {}

    def __init__(self, graph: NWX.MultiDiGraph):
        self.graph = graph
        self.r_graph = NWX.reverse_view(graph)
        # do the below to populate the blink_id mapping dicts
        for html_node in self.html_nodes():
            pass
        for domroot_node in self.domroots():
            pass
        # Finally, populate the mapping of what nodes were ever inserted
        # below another node, during the document's lifetime
        for insert_edge in self.insert_edges():
            parent_node = insert_edge.inserted_below_node()
            inserted_node = insert_edge.child_node()
            self.record_node_was_child_of_node(inserted_node, parent_node)

    def nodes(self) -> NodeIterator:
        for node_id in self.graph.nodes():
            yield self.node(node_id)

    def edges(self) -> EdgeIterator:
        for _, _, edge_id in self.graph.edges:
            yield self.edge(edge_id)

    def insert_edges(self) -> Iterable[InsertNodeEdge]:
        for _, _, edge_id in self.graph.edges:
            edge = self.edge(edge_id)
            if edge.is_insert_edge():
                yield cast(InsertNodeEdge, edge)

    def node_for_blink_id(self, blink_id: BlinkId) -> Node:
        assert blink_id in self.blink_id_mapping
        node = self.blink_id_mapping[blink_id]
        if node.is_domroot():
            return cast(DOMRootNode, node)

        if not node.is_html_elm():
            node.throw("Unexpected blink id in mapping table")
        return cast(HTMLNode, node)

    def nodes_of_type(self, node_type: Node.Types) -> NodeIterator:
        for nid in self.graph.nodes():
            node = self.node(nid)
            if node.is_type(node_type):
                yield node

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

    def record_node_was_child_of_node(self, child_node: ChildNode,
                parent_node: ParentNode) -> None:
        if parent_node not in self.inserted_below_mapping:
            self.inserted_below_mapping[parent_node] = []
        self.inserted_below_mapping[parent_node].append(child_node)

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
        if node.is_type(Node.Types.HTML_NODE):
            html_node = cast(HTMLNode, node)
            self.blink_id_mapping[html_node.blink_id()] = html_node
        if node.is_type(Node.Types.DOM_ROOT):
            domroot_node = cast(DOMRootNode, node)
            self.blink_id_mapping[domroot_node.blink_id()] = domroot_node
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
            return edge_for_type(edge_type, *init_args)
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
                yield domroot_node

    def domroots(self) -> Iterable[DOMRootNode]:
        for node in self.nodes():
            if node.is_domroot():
                yield cast(DOMRootNode, node)


def from_path(input_path: str) -> PageGraph:
    return PageGraph(NWX.read_graphml(input_path))