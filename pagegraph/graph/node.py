from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from itertools import chain
import sys
from typing import cast, Dict, Iterable, List, Self, Set, Tuple, TypeVar, Type
from typing import TYPE_CHECKING

from pagegraph.graph.element import PageGraphElement
from pagegraph.graph.edge import Edge
from pagegraph.graph.js import JSCallResult
from pagegraph.graph.types import BlinkId, EdgeIterator, ChildNode
from pagegraph.graph.types import PageGraphId, PageGraphNodeId, PageGraphEdgeId
from pagegraph.graph.types import PageGraphEdgeKey, NodeIterator, Url
from pagegraph.graph.types import FrameSummary, ParentNode, FrameId
from pagegraph.graph.types import RequesterNode, RequestResponseTypesEdge
from pagegraph.graph.serialize import Reportable, FrameReport, DOMElementReport
from pagegraph.graph.serialize import JSStructureReport
from pagegraph.util import is_url_local


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import NodeCreateEdge, NodeInsertEdge
    from pagegraph.graph.edge import ExecuteEdge, StructureEdge
    from pagegraph.graph.edge import RequestStartEdge, RequestErrorEdge
    from pagegraph.graph.edge import RequestCompleteEdge, RequestRedirectEdge
    from pagegraph.graph.edge import JSCallEdge, JSResultEdge


class Node(PageGraphElement):

    parent_node_types: List["Node.Types"] = []
    child_node_types: List["Node.Types"] = []
    incoming_edge_types: List["Edge.Types"] = []
    outgoing_edge_types: List["Edge.Types"] = []

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
        METHOD = "method"
        SCRIPT_TYPE = "script type"
        TIMESTAMP = "timestamp"
        TYPE = "node type"
        TAG = "tag name"
        URL = "url"

    def type_name(self) -> str:
        return self.data()[self.RawAttrs.TYPE.value]

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

    def is_js_structure(self) -> bool:
        return False

    def is_resource_node(self) -> bool:
        return False

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

    def creator_node(self) -> "ScriptNode" | "HTMLNode" | "ParserNode" | None:
        for edge in self.incoming_edges():
            if edge.is_create_edge():
                creator_edge = cast("NodeCreateEdge", edge)
                node = creator_edge.incoming_node()
                if self.pg.debug:
                    if not node.is_script() and not node.is_parser():
                        self.throw("Unexpected parent creator node")
                if node.is_script():
                    return cast("ScriptNode", node)
                else:
                    return cast("ParserNode", node)
        self.throw("Could not find a creator for this node")
        return None

    def created_nodes(self) -> Iterable[Node]:
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
                if self.pg.debug:
                    if not c_node.is_parser() and not c_node.is_script():
                        self.throw("Unexpected parent creation edge")
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

        # The list now contains DOMRoots, from last created to earliest
        # created.
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
        if self.pg.debug:
            is_executing_script = (
                self.is_text_elm() or
                self.is_html_elm() or
                self.is_script() or
                self.is_frame_owner() or
                self.is_domroot()
            )
            if not is_executing_script:
                self.throw("Unexpected node executing a script")
        for edge in self.outgoing_edges():
            if not edge.is_execute_edge():
                continue
            execute_edge = cast(ExecuteEdge, edge)
            yield execute_edge.outgoing_node()

    def describe(self) -> str:
        output = f"node nid={self.id()}\n"
        for attr_name, attr_value in self.data().items():
            output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"

        output += "incoming edges:\n"
        for edge in self.incoming_edges():
            output += f"- {edge.id()} - {edge.edge_type().value}\n"

        output += "outgoing edges:\n"
        for edge in self.outgoing_edges():
            output += f"- {edge.id()} - {edge.edge_type().value}\n"

        return output

    def validate(self) -> bool:
        if len(self.__class__.parent_node_types) > 0:
            valid_parent_node_types = self.__class__.parent_node_types
            for parent_node in self.parent_nodes():
                node_type = parent_node.node_type()
                if node_type not in valid_parent_node_types:
                    self.throw(f"Unexpected parent node type: {node_type}")
                    return False

        if len(self.__class__.child_node_types) > 0:
            valid_child_node_types = self.__class__.child_node_types
            for child_node in self.child_nodes():
                node_type = child_node.node_type()
                if node_type not in valid_child_node_types:
                    self.throw(f"Unexpected child node type: {node_type}")
                    return False

        if len(self.__class__.incoming_edge_types) > 0:
            valid_incoming_edge_types = self.__class__.incoming_edge_types
            for edge in self.incoming_edges():
                edge_type = edge.edge_type()
                if edge_type not in valid_incoming_edge_types:
                    self.throw(f"Unexpected incoming edge type: {edge_type}")
                    return False

        if len(self.__class__.outgoing_edge_types) > 0:
            valid_outgoing_edge_types = self.__class__.outgoing_edge_types
            for edge in self.outgoing_edges():
                edge_type = edge.edge_type()
                if edge_type not in valid_outgoing_edge_types:
                    self.throw(f"Unexpected outgoing edge type: {edge_type}")
                    return False
        return True

    def creator_edge(self) -> NodeCreateEdge | None:
        for edge in self.incoming_edges():
            if edge.is_create_edge():
                return cast("NodeCreateEdge", edge)
        self.throw("Could not find a creation edge for this node")
        return None


class ScriptNode(Node):

    incoming_edge_types = [
        Edge.Types.EVENT_LISTENER,
        Edge.Types.EXECUTE,
        Edge.Types.EXECUTE_FROM_ATTRIBUTE,
        Edge.Types.JS_RESULT,
        Edge.Types.REQUEST_COMPLETE,
        Edge.Types.REQUEST_ERROR,
        Edge.Types.REQUEST_REDIRECT,
        Edge.Types.REQUEST_RESPONSE,
        Edge.Types.STORAGE_READ_RESULT,
    ]

    outgoing_edge_types = [
        Edge.Types.ATTRIBUTE_DELETE,
        Edge.Types.ATTRIBUTE_SET,
        Edge.Types.EXECUTE,
        Edge.Types.JS_CALL,
        Edge.Types.NODE_CREATE,
        Edge.Types.NODE_INSERT,
        Edge.Types.NODE_REMOVE,
        Edge.Types.REQUEST_START,
        Edge.Types.STORAGE_CLEAR,
        Edge.Types.STORAGE_DELETE,
        Edge.Types.STORAGE_READ_CALL,
        Edge.Types.STORAGE_SET,
        Edge.Types.EVENT_LISTENER_ADD,
        Edge.Types.EVENT_LISTENER_REMOVE,
    ]

    class ScriptTypes(StrEnum):
        INLINE = "inline"
        INLINE_ELM = "inline inside generated element"
        UNKNOWN = "unknown"

    def created_nodes(self) -> Iterable[Node]:
        for edge in self.outgoing_edges():
            if edge.is_create_edge():
                create_edge = cast("NodeCreateEdge", edge)
                yield create_edge.outgoing_node()

    def creator_node(self) -> "ScriptNode" | "HTMLNode" | "ParserNode" | None:
        creator_node = None
        for edge in self.incoming_edges():
            if edge.is_execute_edge():
                creator_node = edge.incoming_node().creator_node()
                break
        if self.pg.debug:
            if not creator_node:
                self.throw("Could not find creator for script node")
        return creator_node


class DOMElementNode(Node):

    def blink_id(self) -> BlinkId:
        return self.data()[Node.RawAttrs.BLINK_ID.value]

    def tag_name(self) -> str:
        raise NotImplementedError()

    def insert_edge(self) -> "NodeInsertEdge" | None:
        insert_edge: None | "NodeInsertEdge" = None
        for edge in self.incoming_edges():
            insert_edge = cast("NodeInsertEdge", edge)
            break
        return insert_edge


class HTMLNode(DOMElementNode, Reportable):

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.id(), self.tag_name())

    def tag_name(self) -> str:
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


class FrameOwnerNode(DOMElementNode, Reportable):

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.id(), self.tag_name())

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


class TextNode(DOMElementNode, Reportable):

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.id(), self.tag_name())

    def tag_name(self) -> str:
        return "<text>"


class DOMRootNode(DOMElementNode, Reportable):

    def to_report(self) -> FrameReport:
        return FrameReport(self.id(), self.url(), self.blink_id())

    def is_top_level_frame(self) -> bool:
        parser = self.parser()
        assert parser
        return parser.is_toplevel_parser()

    def is_local_frame(self) -> bool:
        parent_frame = self.parent_frame()
        if not parent_frame:
            self.throw("Nonsensical to ask if a top level frame is local")
            return False

        this_frame_url = self.url()
        if not this_frame_url:
            self.throw("Frame is intermediate frame, cannot be local")
            return False

        parent_frame_url = parent_frame.url()
        assert parent_frame_url
        return is_url_local(this_frame_url, parent_frame_url)

    def parent_frame(self) -> None | "DOMRootNode":
        assert not self.is_top_level_frame()
        parser = self.parser()
        assert parser
        owning_frame = parser.frame_owner_node()
        if not owning_frame:
            self.throw("Could not find parent frame")
            return None
        return owning_frame.domroot()

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
        return self.summarize_frame().script_nodes

    def _summarize_frame(
            self, node: Node, frame_summary: FrameSummary,
            ignore_nodes: Set[Node]) -> FrameSummary:
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
                        c_text_node = cast(TextNode, a_child_node)
                        frame_summary.attached_nodes.add(c_text_node)
                    elif a_child_node.is_frame_owner():
                        c_frame_node = cast(FrameOwnerNode, a_child_node)
                        frame_summary.attached_nodes.add(c_frame_node)
                    elif a_child_node.is_html_elm():
                        c_html_node = cast(HTMLNode, a_child_node)
                        frame_summary.attached_nodes.add(c_html_node)
                        self._summarize_frame(
                            c_html_node, frame_summary, ignore_nodes)

        if node.is_script() or node.is_parser():
            creating_node: ScriptNode | ParserNode
            if node.is_script():
                creating_node = cast(ScriptNode, node)
            else:
                creating_node = cast(ParserNode, node)

            for a_created_node in creating_node.created_nodes():
                if frame_summary.includes_created(a_created_node):
                    continue
                frame_summary.created_nodes.add(a_created_node)
                self._summarize_frame(
                    a_created_node, frame_summary, ignore_nodes)

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
        assert parser
        return self._summarize_frame(parser, FrameSummary(), set())


class ParserNode(Node):

    parent_node_types = [
        Node.Types.FRAME_OWNER,
        # The RESOURCE case is uncommon, but occurs when something is
        # fetched that doesn't have a representation in the graph,
        # most commonly a pre* <meta> instruction.
        Node.Types.RESOURCE
    ]

    def domroot(self) -> DOMRootNode | None:
        self.throw("Tried to ask for DOMRoot of a parser")
        return super().domroot()  # deadcode, to please mypy

    def frame_owner_node(self) -> FrameOwnerNode | None:
        parent_nodes_list = list(self.parent_nodes())
        frame_owner_nodes: List["FrameOwnerNode"] = []
        for parent_node in parent_nodes_list:
            if parent_node.is_frame_owner():
                frame_owner_nodes.append(cast(FrameOwnerNode, parent_node))
        if self.pg.debug:
            if len(frame_owner_nodes) != 1:
                self.throw("Did not find exactly 1 parent frame owner node")
        return frame_owner_nodes[0]

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

    outgoing_edge_types = [
        Edge.Types.REQUEST_COMPLETE,
        Edge.Types.REQUEST_ERROR,
        Edge.Types.REQUEST_REDIRECT
    ]

    incoming_edge_types = [
        Edge.Types.REQUEST_REDIRECT,
        Edge.Types.REQUEST_START
    ]

    def is_resource_node(self) -> bool:
        return True

    def url(self) -> Url:
        return self.data()[Node.RawAttrs.URL.value]

    def incoming_edges(self) -> Iterable["RequestStartEdge"]:
        return [cast("RequestStartEdge", e) for e in super().incoming_edges()]

    def outgoing_edges(self) -> Iterable[RequestResponseTypesEdge]:
        for edge in super().outgoing_edges():
            if edge.is_request_complete_edge():
                yield cast("RequestCompleteEdge", edge)
            elif edge.is_request_redirect_edge():
                yield cast("RequestRedirectEdge", edge)
            else:
                yield cast("RequestErrorEdge", edge)

    def requesters(self) -> Iterable["RequesterNode"]:
        for edge in self.incoming_edges():
            incoming_node = edge.incoming_node()
            yield incoming_node


class JSStructureNode(Node, Reportable):
    def to_report(self) -> JSStructureReport:
        return JSStructureReport(self.name(), self.type_name())

    def is_js_structure(self) -> bool:
        return True

    def name(self) -> str:
        return self.data()[self.RawAttrs.METHOD.value]

    def call_results(self) -> list["JSCallResult"]:
        js_calls = self.incoming_edges()
        js_results = self.outgoing_edges()
        calls_and_results_unsorted = list(chain(js_calls, js_results))
        calls_and_results = sorted(
            calls_and_results_unsorted, key=lambda x: x.int_id())

        if self.pg.debug:
            num_calls = len(list(js_calls))
            num_results = len(list(js_results))
            if num_results > num_calls:
                self.throw("Found more results than calls to this builtin, "
                           f"calls={num_calls}, results={num_results}")

            last_edge = calls_and_results[0]
            for edge in calls_and_results[1:]:
                if edge.is_js_result_edge():
                    if last_edge.is_js_result_edge():
                        self.throw("Found two adjacent result edges: "
                                   f"{last_edge.id()} and {edge.id()}")
                last_edge = edge

        call_results: list[JSCallResult] = []
        for edge in calls_and_results:
            if edge.is_js_result_edge():
                js_result_edge = cast("JSResultEdge", edge)
                last_call_result = call_results[-1]
                last_call_result.result_edge = js_result_edge
            else:
                js_call_edge = cast("JSCallEdge", edge)
                a_call_result = JSCallResult(js_call_edge, None)
                call_results.append(a_call_result)
        return call_results

    def incoming_edges(self) -> Iterable["JSCallEdge"]:
        for edge in super().incoming_edges():
            yield cast("JSCallEdge", edge)

    def outgoing_edges(self) -> Iterable["JSResultEdge"]:
        for edge in super().outgoing_edges():
            yield cast("JSResultEdge", edge)


class JSBuiltInNode(JSStructureNode):
    pass


class WebAPINode(JSStructureNode):
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
