from __future__ import annotations

from enum import StrEnum
import sys
from typing import cast, Iterable, Self, Set, TypeVar, TYPE_CHECKING

from pagegraph.graph.types import BlinkId, EdgeIterator
from pagegraph.graph.types import PageGraphId, PageGraphNodeId, PageGraphEdgeId
from pagegraph.graph.types import PageGraphEdgeKey, NodeIterator, Url
from pagegraph.graph.element import PageGraphElement


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import Edge, CreateNodeEdge, InsertNodeEdge


def created_dom_nodes_recursive(node: ParentNode | ScriptNode,
        seen_nodes=Set[ChildNode] | None) -> Set[ChildNode]:
    """This function returns a set of all nodes created by the initial node,
    or any node created by one of those nodes, etc."""
    if seen_nodes is None:
        seen_nodes = set()

    for child_node in node.created_nodes_immediate():
        if child_node in seen_nodes:
            continue

        if child_node.is_text_elm():
            a_text_node = cast(TextNode, child_node)
            seen_nodes.add(a_text_node)
        elif child_node.is_html_elm():
            a_html_node = cast(HTMLNode, child_node)
            seen_nodes.add(a_html_node)
            seen_nodes |= created_dom_nodes_recursive(a_html_node, seen_nodes)
        elif child_node.is_frame_owner():
            a_frame_owner_node = cast(FrameOwnerNode, child_node)
            seen_nodes.add(a_frame_owner_node)

        for script in child_node.executed_scripts():
            seen_nodes |= created_dom_nodes_recursive(script, seen_nodes)

    return seen_nodes


def child_dom_nodes_recursive(node: ParentNode, seen_nodes=None | Set[ChildNode]) -> Set[ChildNode]:
    """Returns every node that was ever a child (or child of a child, etc)
    in the DOM tree, over the lifetime of the graph"""
    if seen_nodes is None:
        seen_nodes = set()

    for child_node in node.pg.child_dom_nodes(node):
        if child_node in seen_nodes:
            continue

        if child_node.is_text() or child_node.is_frame_owner():
            seen_nodes.add(child_node)
        elif child_node.is_html_elm():
            a_html_node = cast(HTMLNode, child_node)
            seen_nodes.add(a_html_node)
            seen_nodes |= child_dom_nodes_recursive(a_html_node, seen_nodes)
    return seen_nodes


def executed_scripts_recursive(node: ParentNode | ScriptNode,
        seen_nodes=None | Set[ScriptNode]) -> Set[ScriptNode]:
    pass


class Node(PageGraphElement):

    class Types(StrEnum):
        FRAME_OWNER = "frame owner"
        SCRIPT = "script"
        PARSER = "parser"
        HTML_NODE = "HTML element"
        TEXT_NODE = "text node"
        DOM_ROOT = "DOM root"
        SHIELDS = "Brave Shields"
        ADS_SHIELDS = "shieldsAds shield"
        TRACKERS_SHIELDS = "trackers shield"
        JS_SHIELDS = "javascript shield"
        FP_SHIELDS = "fingerprintingV2 shield"
        STORAGE = "storage"
        COOKIE_JAR = "cookie jar"
        LOCAL_STORAGE = "local storage"
        SESSION_STORAGE = "session storage"
        EXTENSIONS = "extensions"
        RESOURCE = "resource"
        JS_BUILTIN = "JS builtin"
        WEB_API = "web API"

    IGNORE_TYPES = [
            Types.SHIELDS, Types.ADS_SHIELDS, Types.TRACKERS_SHIELDS,
            Types.JS_SHIELDS, Types.FP_SHIELDS, Types.EXTENSIONS]

    class RawAttrs(StrEnum):
        TYPE = "node type"
        TAG = "tag name"
        SCRIPT_TYPE = "script type"
        BLINK_ID = "node id"
        URL = "url"

    def __init__(self, graph: "PageGraph", pg_id: PageGraphId):
        assert pg_id.startswith('n')
        super().__init__(graph, pg_id)

    def node_type(self) -> "Node.Types":
        type_name = self.data()[self.RawAttrs.TYPE.value]
        return self.Types(type_name)

    def child_nodes(self) -> NodeIterator:
        for nid, _ in self.pg.graph.adj[self._id].items():
            yield self.pg.node(nid)

    def child_dom_nodes_recursive(self) -> Set[ChildNode]:
        """Returns every node that was ever a child (or child of a child, etc)
        in the DOM tree, over the lifetime of the graph."""
        all_child_nodes = set()
        for node in self.pg.inserted_below_mapping(self):
            child_child_nodes = node.child_dom_nodes_tree()
            if child_child_nodes is None:
                continue
            all_child_nodes |= child_child_nodes
        return all_child_nodes

    def parent_nodes(self) -> NodeIterator:
        for nid, _ in self.pg.r_graph.adj[self._id].items():
            yield self.pg.node(nid)

    def outgoing_edges(self) -> EdgeIterator:
        for _, edge_info in self.pg.graph.adj[self._id].items():
            for edge_id, _ in edge_info.items():
                yield self.pg.edge(edge_id)

    def incoming_edges(self) -> EdgeIterator:
        for _, edge_info in self.pg.r_graph.adj[self._id].items():
            for edge_id, _ in edge_info.items():
                yield self.pg.edge(edge_id)

    def is_type(self, node_type: Types) -> bool:
        return self.data()[self.RawAttrs.TYPE.value] == node_type.value

    def is_text_elm(self) -> bool:
        return self.is_type(self.Types.TEXT_NODE)

    def is_frame_owner(self) -> bool:
        return self.is_type(self.Types.FRAME_OWNER)

    def is_script(self) -> bool:
        return self.is_type(self.Types.SCRIPT)

    def is_domroot(self) -> bool:
        return self.is_type(self.Types.DOM_ROOT)

    def is_parser(self) -> bool:
        return self.is_type(self.Types.PARSER)

    def is_html_elm(self) -> bool:
        return self.is_type(self.Types.HTML_NODE)

    def is_toplevel_parser(self) -> bool:
        for incoming_edge in self.incoming_edges():
            if incoming_edge.is_cross_dom_edge():
                return False
        return True

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.nodes[self._id])

    def creator_node(self) -> "Node" | None:
        creator_edge = None
        for incoming_edge in self.incoming_edges():
            if incoming_edge.is_create_edge():
                creator_edge = incoming_edge
                break

        if creator_edge is None:
            self.throw("Could not find a creator for this node")
        creator_edge = cast("CreateNodeEdge", creator_edge)
        return creator_edge.parent_node()

    def created_nodes_immediate(self) -> Iterable[Node]:
        for edge in self.outgoing_edges():
            if edge.is_create_edge():
                yield edge.child_node()

    def created_nodes_recursive(self) -> Set[Node]:
        all_created_nodes = set()
        for node in self.created_nodes():
            all_created_nodes.add(node)
            all_created_nodes |= node.created_nodes_recursive()
        return all_created_nodes

    def domroot(self) -> DOMRootNode | None:
        """In the simplest case, we try and find a DOMRoot by recursively
        looking to see what created our creator, until we get to a parser node,
        and then we just choose the correct DOMRoot from the list of possible
        candidates (see below for how we do that)."""
        domroots_for_parser = None

        creator_node = self.creator_node()
        while creator_node:
            if creator_node.is_parser():
                parser_node = cast(ParserNode, creator_node)
                domroots_for_parser = parser_node.domroots()
                break
            creator_node = creator_node.creator_node()

        if not domroots_for_parser:
            self.throw("Unable to find a DOMRoot")
        domroots_for_parser = cast(Iterable[DOMRootNode], domroots_for_parser)

        # We 'cheat' here by finding the docroot node that has an id
        # closest to, but not larger than, the this node (since any
        # document with a higher pg id had to be created after this node,
        # and so could not contain the given node).
        domroots_sorted = sorted(domroots_for_parser, key=lambda x: x.id())

        # The list now contains DOMRoots, from last created to earliest created.
        domroots_sorted.reverse()
        owning_domroot = None
        for a_domroot in domroots_sorted:
            if a_domroot.int_id() < self.int_id():
                owning_domroot = a_domroot
                break
            break

        if not owning_domroot:
            self.throw("All DOMRoots for parser are younger than this node")
        return cast(DOMRootNode, owning_domroot)

    def executed_scripts(self) -> Iterable[ScriptNode]:
        for edge in self.outgoing_edges():
            if not edge.is_execute_edge():
                continue
            execute_edge = cast(ExecuteEdge, edge)
            return execute_edge.child_node()

    def describe(self) -> str:
        output = f"node nid={self.id()}\n"
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"
        return output


class ScriptNode(Node):

    class ScriptTypes(StrEnum):
        INLINE = "inline"
        INLINE_ELM = "inline inside generated element"
        UNKNOWN = "unknown"

    def __init__(self, graph: "PageGraph", pg_id: PageGraphId):
        super().__init__(graph, pg_id)
        assert self.is_type(Node.Types.SCRIPT)

    def creator_node(self) -> Node:
        creator_node = None
        for edge in self.incoming_edges():
            if edge.is_execute_edge():
                creator_node = edge.parent_node()
                break
        if not creator_node:
            self.throw(f"Can't find execution edge")
        return cast(Node, creator_node)


class HTMLNode(Node):

    def html_tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def blink_id(self) -> BlinkId:
        return self.data()[Node.RawAttrs.BLINK_ID.value]

    def parent_html_nodes(self) -> Iterable[HTMLNode | DOMRootNode]:
        """Return every node this node was ever inserted under. This can be
        zero nodes (if the node was created but never inserted in the
        document), or more than one node (if the node was moved around the
        document during execution)."""
        for incoming_edge in self.incoming_edges():
            if incoming_edge.is_insert_edge():
                yield cast(InsertNodeEdge, incoming_edge).inserted_below_node()

    def script_nodes(self) -> Iterable[ScriptNode]:
        pass


    def _domroot_from_parent_node_path(self) -> DOMRootNode | None:
        """Tries to follow all chains of nodes that this node was inserted
        as a child of. Its possible that we cannot get to a docroot node
        in this path though (for example, nodes trees created in script
        but not inserted in a document), in which case, we return None."""
        for parent_node in self.parent_html_nodes():
            if parent_node.is_domroot():
                return cast(DOMRootNode, parent_node)
            else:
                return cast(HTMLNode, parent_node)._domroot_from_parent_node_path()
        return None

    def domroot(self) -> DOMRootNode:
        """First, see if we can figure out what DOMRoot this HTML Element
        existed in by looking at document structure. We do this to
        make correct attribute frames created cross dom, in local child frames
        (since, if we checked for frame-ownership by creator, we'd wind
        up with the cross-dom script's frame, and not the frame
        this element was in)"""
        parent_node_from_structure = self._domroot_from_parent_node_path()
        if parent_node_from_structure:
            return parent_node_from_structure
        return cast(DOMRootNode, super().domroot())


class FrameOwnerNode(Node):

    def child_parser_nodes(self) -> Iterable[ParserNode]:
        for child_node in self.child_nodes():
            if child_node.is_parser():
                yield cast(ParserNode, child_node)

    def child_domroots(self) -> Iterable[DOMRootNode]:
        for parser_node in self.child_parser_nodes():
            domroot_nodes = list(parser_node.domroots())
            domroots_sorted = sorted(domroot_nodes, key=lambda x: x.int_id())
            for domroot_node in domroots_sorted:
                yield domroot_node

    def tag_name(self) -> str:
        return self.data()[self.RawAttrs.TAG.value]


class TextNode(Node):
    pass


class DOMRootNode(Node):

    def url(self) -> Url:
        return self.data()[self.RawAttrs.URL.value]

    def blink_id(self) -> BlinkId:
        return self.data()[Node.RawAttrs.BLINK_ID.value]

    def tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def parser(self) -> ParserNode | None:
        for node in self.parent_nodes():
            if node.is_parser():
                return cast(ParserNode, node)
        self.throw("Could not find parser node from DomRoot")
        return None

    def domroot(self) -> DOMRootNode:
        return self

    def nodes(self) -> Set[Node]:
        """To figure out what nodes were in this domroot, we do the following:
            - get the parser that was responsible for this domroot (noting
              that the parser could be shared with other domroots)
            - starting at the docroot, we spider along
                - any node that this node created
                - any node that was ever inserted below this node
                - any requests this node made
                - any scripts this node executed"""
        found_nodes: Set[Node] = set()

        # First, recursively return any node that the dom root created
        # (or any node created by a node the domroot created, etc.)
        found_nodes |= self.created_nodes_recursive()

        # Next, recursively return any node that was ever inserted below
        # the DOMRoot (or was inserted below a node that was inserted below
        # the DOMRoot, etc).
        found_nodes |= self.child_dom_nodes_recursive()

        # Third,




    def tree_nodes(self) -> Iterable[Node]:
        """This differs from the above, in that it only includes nodes that
        were at some point attached to the document"""
        pass




class ParserNode(Node):

    def domroot(self) -> DOMRootNode | None:
        msg = "Tried to ask for DOMRoot of a parser"
        self.throw(msg)
        return super().domroot() # deadcode, to please mypy

    def creator_node(self) -> Node | None:
        parent_nodes_list = list(self.parent_nodes())
        num_parent_nodes = len(parent_nodes_list)
        has_parent_nodes = num_parent_nodes == 0
        if not has_parent_nodes:
            return None

        assert num_parent_nodes == 1
        parent_node = parent_nodes_list[0]
        assert parent_node.is_type(Node.Types.FRAME_OWNER)
        return cast(FrameOwnerNode, parent_node)

    def domroots(self) -> Iterable[DOMRootNode]:
        already_returned = set()
        for outgoing_edge in self.outgoing_edges():
            if (not outgoing_edge.is_create_edge() and
                    not outgoing_edge.is_structure_edge()):
                continue
            child_node = outgoing_edge.child_node()
            if child_node in already_returned:
                continue
            if not child_node.is_type(Node.Types.DOM_ROOT):
                continue
            already_returned.add(child_node)
            yield cast(DOMRootNode, child_node)

    def created_nodes_for_domroot(self, domroot: DOMRootNode) -> Iterable[Node]:
        all_domroots = self.domroots()
        domroots_sorted = sorted(all_domroots, key=lambda x: x.int_id())
        min_id = self.int_id()
        max_id = sys.maxsize
        for a_domroot in domroots_sorted:
            if a_domroot.int_id() > min_id:
                max_id = a_domroot.int_id()
                break


class ResourceNode(Node):
    pass

class JSBuiltInNode(Node):
    pass

class WebAPINode(Node):
    pass

class StorageNode(Node):
    pass

class CookieJarNode(Node):
    pass

class LocalStorageNode(Node):
    pass

class SessionStorageNode(Node):
    pass


def for_type(node_type: Node.Types, graph: "PageGraph", node_id: PageGraphNodeId) -> Node:
    if node_type == Node.Types.FRAME_OWNER:
        return FrameOwnerNode(graph, node_id)
    elif node_type == Node.Types.SCRIPT:
        return ScriptNode(graph, node_id)
    elif node_type == Node.Types.PARSER:
        return ParserNode(graph, node_id)
    elif node_type == Node.Types.HTML_NODE:
        return HTMLNode(graph, node_id)
    elif node_type == Node.Types.TEXT_NODE:
        return TextNode(graph, node_id)
    elif node_type == Node.Types.DOM_ROOT:
        return DOMRootNode(graph, node_id)
    elif node_type == Node.Types.STORAGE:
        return StorageNode(graph, node_id)
    elif node_type == Node.Types.COOKIE_JAR:
        return CookieJarNode(graph, node_id)
    elif node_type == Node.Types.LOCAL_STORAGE:
        return LocalStorageNode(graph, node_id)
    elif node_type == Node.Types.SESSION_STORAGE:
        return SessionStorageNode(graph, node_id)
    elif node_type == Node.Types.RESOURCE:
        return ResourceNode(graph, node_id)
    elif node_type == Node.Types.JS_BUILTIN:
        return JSBuiltInNode(graph, node_id)
    elif node_type == Node.Types.WEB_API:
        return WebAPINode(graph, node_id)
    elif node_type in Node.IGNORE_TYPES:
        return Node(graph, node_id)
    else:
        raise ValueError(f"Unexpected node type={node_type.value}")
