from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
import sys
from typing import cast, Dict, Iterable, Self, Set, TypeVar, Type, TYPE_CHECKING

from pagegraph.graph.types import BlinkId, EdgeIterator, ChildNode
from pagegraph.graph.types import PageGraphId, PageGraphNodeId, PageGraphEdgeId
from pagegraph.graph.types import PageGraphEdgeKey, NodeIterator, Url
from pagegraph.graph.types import FrameSummary, ParentNode, FrameId
from pagegraph.graph.types import RequesterNode
from pagegraph.graph.element import PageGraphElement

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import Edge, NodeCreateEdge, NodeInsertEdge
    from pagegraph.graph.edge import ExecuteEdge, StructureEdge
    from pagegraph.graph.edge import RequestStartEdge, RequestErrorEdge
    from pagegraph.graph.edge import RequestCompleteEdge


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

    class RawAttrs(StrEnum):
        BLINK_ID = "node id"
        FRAME_ID = "frame id"
        SCRIPT_TYPE = "script type"
        TIMESTAMP = "timestamp"
        TYPE = "node type"
        TAG = "tag name"
        URL = "url"

    def node_type(self) -> "Node.Types":
        type_name = self.data()[self.RawAttrs.TYPE.value]
        return self.Types(type_name)

    def child_nodes(self) -> NodeIterator:
        for nid, _ in self.pg.graph.adj[self._id].items():
            yield self.pg.node(nid)

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

    def is_dom_node_type(self) -> bool:
        return (
            self.is_html_elm() or
            self.is_text_elm() or
            self.is_domroot() or
            self.is_frame_owner()
        )

    def is_child_dom_node_type(self) -> bool:
        """Returns true if this node is valid to ever be a child node for
        any other DOM node type."""
        is_child_dom_node = (
            self.is_frame_owner() or
            self.is_text_elm() or
            self.is_html_elm()
        )
        return is_child_dom_node

    def is_requester_node_type(self) -> bool:
        is_requester_node = (
            self.is_parser() or
            self.is_html_elm() or
            self.is_script() or
            self.is_domroot()
        )
        return is_requester_node

    def is_leaf_dom_node_type(self) -> bool:
        """Returns true if this is a node type that can appear in the DOM,
        and cannot have any child nodes within this frame."""
        return self.is_text_elm() or self.is_frame_owner()

    def is_parent_dom_node_type(self) -> bool:
        """Returns true if this node is valid to ever be the parent of
        another DOM node in w/in a frame (i.e., iframes/frame owners
        cannot be parents of other DOM nodes w/in the same frame)."""
        is_parent_dom_node_type = (
            self.is_html_elm() or
            self.is_domroot() or
            # below is surprising, but frameowner (i.e., iframe) nodes
            # can contain text elements, because if a page includes
            # an iframe like this <iframe>SOME TEXT</iframe>, blink will
            # initialize the "SOME TEXT" node as a child of the iframe,
            # even though those nodes will then be immediately replaced
            # with the child document.
            self.is_frame_owner()
        )
        return is_parent_dom_node_type

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

    def frame_owner_nodes(self) -> Iterable[FrameOwnerNode]:
        for node in self.pg.nodes():
            if node.is_frame_owner():
                yield cast(FrameOwnerNode, node)

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.nodes[self._id])

    def timestamp(self) -> int:
        return int(self.data()[self.RawAttrs.TIMESTAMP])

    def creator_node(self) -> "ScriptNode" | "ParserNode" | None:
        for edge in self.incoming_edges():
            if edge.is_create_edge():
                creator_edge = cast("NodeCreateEdge", edge)
                node = creator_edge.incoming_node()
                assert node.is_script() or node.is_parser()
                if node.is_script():
                    return cast("ScriptNode", node)
                else:
                    return cast("ParserNode", node)
        self.throw("Could not find a creator for this node")
        return None

    def created_node(self) -> Iterable[Node]:
        for edge in self.outgoing_edges():
            if edge.is_create_edge():
                yield edge.outgoing_node()

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
            c_node = creator_node.creator_node()
            if c_node is not None:
                assert c_node.is_parser() or c_node.is_script()
                if c_node.is_parser():
                    creator_node = cast(ParserNode, c_node)
                else:
                    creator_node = cast(ScriptNode, c_node)

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
        assert (
            self.is_text_elm() or
            self.is_html_elm() or
            self.is_script() or
            self.is_frame_owner() or
            self.is_domroot()
        )
        for edge in self.outgoing_edges():
            if not edge.is_execute_edge():
                continue
            execute_edge = cast(ExecuteEdge, edge)
            yield execute_edge.outgoing_node()

    def describe(self) -> str:
        output = f"node nid={self.id()}\n"
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"
        return output

    def validate(self) -> bool:
        return True

    def creator_edge(self) -> NodeCreateEdge | None:
        for edge in self.incoming_edges():
            if edge.is_create_edge():
                return cast("NodeCreateEdge", edge)
        self.throw("Could not find a creation edge for this node")
        return None


class DOMElementNode(Node):

    def blink_id(self) -> BlinkId:
        return self.data()[Node.RawAttrs.BLINK_ID.value]

    def insert_edge(self) -> "NodeInsertEdge":
        node: None | "NodeInsertEdge" = None
        for edge in self.incoming_edges():
            if edge.is_insert_edge():
                node = cast("NodeInsertEdge", edge)
                break
        assert node
        return node

class ScriptNode(Node):

    class ScriptTypes(StrEnum):
        INLINE = "inline"
        INLINE_ELM = "inline inside generated element"
        UNKNOWN = "unknown"

    def __init__(self, graph: "PageGraph", pg_id: PageGraphId):
        super().__init__(graph, pg_id)
        assert self.is_type(Node.Types.SCRIPT)

    def created_nodes(self) -> Iterable[Node]:
        for edge in self.outgoing_edges():
            if edge.is_create_edge():
                create_edge = cast("NodeCreateEdge", edge)
                yield create_edge.outgoing_node()


class HTMLNode(DOMElementNode):

    def html_tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def parent_html_nodes(self) -> Iterable[ParentNode]:
        """Return every node this node was ever inserted under. This can be
        zero nodes (if the node was created but never inserted in the
        document), or more than one node (if the node was moved around the
        document during execution)."""
        for incoming_edge in self.incoming_edges():
            if incoming_edge.is_insert_edge():
                yield cast(NodeInsertEdge, incoming_edge).inserted_below_node()

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


class FrameOwnerNode(DOMElementNode):

    def child_parser_nodes(self) -> Iterable[ParserNode]:
        for child_node in self.child_nodes():
            if child_node.is_parser():
                yield cast(ParserNode, child_node)

    def domroots(self) -> Iterable[DOMRootNode]:
        for parser_node in self.child_parser_nodes():
            domroot_nodes = list(parser_node.domroots())
            domroots_sorted = sorted(domroot_nodes, key=lambda x: x.int_id())
            for domroot_node in domroots_sorted:
                yield domroot_node

    def tag_name(self) -> str:
        return self.data()[self.RawAttrs.TAG.value]


class TextNode(DOMElementNode):
    pass


class DOMRootNode(DOMElementNode):

    def frame_owner_nodes(self) -> Iterable[FrameOwnerNode]:
        seen_set = set()
        frame_id = self.frame_id()
        for frame_owner_node in self.pg.frame_owner_nodes():
            if frame_owner_node in seen_set:
                continue
            creator_edge = frame_owner_node.creator_edge()
            if creator_edge and creator_edge.frame_id() == frame_id:
                seen_set.add(frame_owner_node)
                yield frame_owner_node
                continue
            insert_edge = frame_owner_node.insert_edge()
            if insert_edge and insert_edge.frame_id() == frame_id:
                seen_set.add(frame_owner_node)
                yield frame_owner_node
                continue

    def frame_id(self) -> FrameId:
        return self.data()[self.RawAttrs.FRAME_ID.value]

    def url(self) -> Url | None:
        try:
            return self.data()[self.RawAttrs.URL.value]
        except KeyError:
            # This will happen for temporary frame owner nodes that
            # are created before the document is setup
            return None

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

    def script_nodes(self) -> Iterable[ScriptNode]:
        for script_node in self.summarize_frame().script_nodes:
            yield script_node

    def _summarize_frame(self, node: Node,
            frame_summary: FrameSummary, ignore_nodes: Set[Node]) -> FrameSummary:
        if node in ignore_nodes:
            return frame_summary

        if node.is_parser():
            ignore_nodes.add(node)

        if node.is_parent_dom_node_type():
            parent_node = cast(ParentNode, node)
            child_dom_nodes = self.pg.child_dom_nodes(parent_node)
            if child_dom_nodes is not None:
                for a_child_node in child_dom_nodes:
                    if frame_summary.includes_attached(a_child_node):
                        continue

                    if a_child_node.is_text_elm():
                        child_text_node = cast(TextNode, a_child_node)
                        frame_summary.attached_nodes.add(child_text_node)
                    elif a_child_node.is_frame_owner():
                        child_frame_owner_node = cast(FrameOwnerNode, a_child_node)
                        frame_summary.attached_nodes.add(child_frame_owner_node)
                    elif a_child_node.is_html_elm():
                        child_html_node = cast(HTMLNode, a_child_node)
                        frame_summary.attached_nodes.add(child_html_node)
                        self._summarize_frame(child_html_node, frame_summary, ignore_nodes)

        if node.is_script() or node.is_parser():
            creating_node: ScriptNode | ParserNode = (
                cast(ScriptNode, node) if node.is_script() else cast(ParserNode, node)
            )

            for a_created_node in creating_node.created_nodes():
                if frame_summary.includes_created(a_created_node):
                    continue
                frame_summary.created_nodes.add(a_created_node)
                self._summarize_frame(a_created_node, frame_summary, ignore_nodes)

        for executed_node in node.executed_scripts():
            assert executed_node.is_script()

            if frame_summary.includes_executed(executed_node):
                continue

            frame_summary.script_nodes.add(executed_node)
            self._summarize_frame(executed_node, frame_summary, ignore_nodes)

        return frame_summary

    @lru_cache(maxsize=None)
    def summarize_frame(self) -> FrameSummary:
        parser = self.parser()
        assert parser is not None
        return self._summarize_frame(parser, FrameSummary(), set())


class ParserNode(Node):

    def domroot(self) -> DOMRootNode | None:
        msg = "Tried to ask for DOMRoot of a parser"
        self.throw(msg)
        return super().domroot() # deadcode, to please mypy

    def frame_owner_node(self) -> FrameOwnerNode | None:
        parent_nodes_list = list(self.parent_nodes())
        num_parent_nodes = len(parent_nodes_list)
        has_parent_nodes = num_parent_nodes == 0
        if not has_parent_nodes:
            return None
        assert num_parent_nodes == 1
        parent_node = parent_nodes_list[0]
        assert parent_node.is_type(Node.Types.FRAME_OWNER)
        return cast(FrameOwnerNode, parent_node)

    def created_nodes(self) -> Iterable[Node]:
        for edge in self.outgoing_edges():
            if edge.is_create_edge():
                create_edge = cast(NodeCreateEdge, edge)
                yield create_edge.outgoing_node()

    def domroots(self) -> Iterable[DOMRootNode]:
        already_returned = set()
        for outgoing_edge in self.outgoing_edges():
            if (not outgoing_edge.is_create_edge() and
                    not outgoing_edge.is_structure_edge()):
                continue
            child_node = outgoing_edge.outgoing_node()
            if child_node in already_returned:
                continue
            if not child_node.is_type(Node.Types.DOM_ROOT):
                continue
            already_returned.add(child_node)
            yield cast(DOMRootNode, child_node)


class ResourceNode(Node):

    def url(self) -> Url:
        return self.data()[Node.RawAttrs.URL.value]

    def incoming_edges(self) -> Iterable["RequestStartEdge"]:
        for edge in super().incoming_edges():
            if not edge.is_request_start_edge():
                edge.throw("")
            assert edge.is_request_start_edge()
            yield cast("RequestStartEdge", edge)

    def outgoing_edges(self) -> Iterable[
            "RequestCompleteEdge" | "RequestErrorEdge"]:
        for edge in super().outgoing_edges():
            assert edge.is_request_complete_edge() or edge.is_request_error_edge()
            if edge.is_request_complete_edge():
                yield cast("RequestCompleteEdge", edge)
            else:
                yield cast("RequestErrorEdge", edge)

    def requesters(self) -> Iterable["RequesterNode"]:
        for edge in self.incoming_edges():
            incoming_node = edge.incoming_node()
            yield incoming_node


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

class DeprecatedNode(Node):
    pass


TYPE_MAPPING: Dict[Node.Types, Type[Node]] = dict([
    (Node.Types.FRAME_OWNER, FrameOwnerNode),
    (Node.Types.SCRIPT, ScriptNode),
    (Node.Types.PARSER, ParserNode),
    (Node.Types.HTML_NODE, HTMLNode),
    (Node.Types.TEXT_NODE, TextNode),
    (Node.Types.DOM_ROOT, DOMRootNode),
    (Node.Types.STORAGE, StorageNode),
    (Node.Types.COOKIE_JAR, CookieJarNode),
    (Node.Types.LOCAL_STORAGE, LocalStorageNode),
    (Node.Types.SESSION_STORAGE, SessionStorageNode),
    (Node.Types.EXTENSIONS, DeprecatedNode),
    (Node.Types.RESOURCE, ResourceNode),
    (Node.Types.JS_BUILTIN, JSBuiltInNode),
    (Node.Types.WEB_API, WebAPINode),

    (Node.Types.SHIELDS, DeprecatedNode),
    (Node.Types.ADS_SHIELDS, DeprecatedNode),
    (Node.Types.TRACKERS_SHIELDS, DeprecatedNode),
    (Node.Types.JS_SHIELDS, DeprecatedNode),
    (Node.Types.FP_SHIELDS, DeprecatedNode),
])

def for_type(node_type: Node.Types, graph: "PageGraph",
        node_id: PageGraphNodeId) -> Node:
    try:
        return TYPE_MAPPING[node_type](graph, node_id)
    except KeyError:
        raise ValueError(f"Unexpected node type={node_type.value}")
