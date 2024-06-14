from __future__ import annotations

from abc import ABC
from base64 import b64encode
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
import hashlib
from itertools import chain
import sys
from typing import Any, cast, Optional, Type, TYPE_CHECKING, Union

from pagegraph.graph.element import PageGraphElement, sort_elements
from pagegraph.graph.edge import Edge
from pagegraph.graph.js import JSCallResult
from pagegraph.graph.requests import RequestResponse, RequestChain
from pagegraph.types import BlinkId, EdgeIterator, ChildDOMNode, AttrDOMNode
from pagegraph.types import PageGraphId, PageGraphNodeId, PageGraphEdgeId
from pagegraph.types import PageGraphEdgeKey, NodeIterator, Url, ActorNode
from pagegraph.types import FrameSummary, ParentDOMNode, FrameId, LeafDOMNode
from pagegraph.types import RequesterNode, RequestId, ResourceType, DOMNode
from pagegraph.serialize import Reportable, FrameReport, DOMElementReport
from pagegraph.serialize import JSStructureReport, ScriptReport
from pagegraph.serialize import EdgeReport, BriefEdgeReport
from pagegraph.serialize import NodeReport, BriefNodeReport
from pagegraph.util import is_url_local, brief_version
from pagegraph.versions import Feature


if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import NodeCreateEdge, NodeInsertEdge
    from pagegraph.graph.edge import ExecuteEdge, StructureEdge
    from pagegraph.graph.edge import RequestStartEdge, RequestErrorEdge
    from pagegraph.graph.edge import RequestCompleteEdge, RequestRedirectEdge
    from pagegraph.graph.edge import JSCallEdge, JSResultEdge
    from pagegraph.graph.edge import RequestResponseEdge


class Node(PageGraphElement, ABC):

    # Used as class properties
    incoming_node_types: Union[list["Node.Types"], None] = None
    outgoing_node_types: Union[list["Node.Types"], None] = None
    incoming_edge_types: Union[list["Edge.Types"], None] = None
    outgoing_edge_types: Union[list["Edge.Types"], None] = None

    class Types(StrEnum):
        ADS_SHIELDS = "shieldsAds shield"
        COOKIE_JAR = "cookie jar"
        DOM_ROOT = "DOM root"
        EXTENSIONS = "extensions"
        FP_SHIELDS = "fingerprintingV2 shield"
        FRAME_OWNER = "frame owner"
        HTML_NODE = "HTML element"
        JS_BUILTIN = "JS builtin"
        JS_SHIELDS = "javascript shield"
        LOCAL_STORAGE = "local storage"
        PARSER = "parser"
        RESOURCE = "resource"
        SCRIPT = "script"
        SESSION_STORAGE = "session storage"
        SHIELDS = "Brave Shields"
        STORAGE = "storage"
        TEXT_NODE = "text node"
        TRACKERS_SHIELDS = "trackers shield"
        WEB_API = "web API"

    class RawAttrs(StrEnum):
        BLINK_ID = "node id"
        FRAME_ID = "frame id"
        METHOD = "method"
        SCRIPT_TYPE = "script type"
        SOURCE = "source"
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

    def to_node_report(
            self, depth: int = 0,
            seen: None | set[Union["Node", "Edge"]] = None) -> NodeReport:
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
            self.pg_id(), self.node_type(), self.summary_fields(),
            incoming_edges, outgoing_edges)

    def to_brief_report(self) -> BriefNodeReport:
        return BriefNodeReport(self.pg_id(), self.node_type(),
                               self.summary_fields())

    def is_type(self, node_type: Types) -> bool:
        return self.data()[self.RawAttrs.TYPE.value] == node_type.value

    def as_dom_node(self) -> Optional[DOMNode]:
        return (
            self.as_html_node() or
            self.as_text_node() or
            self.as_domroot_node() or
            self.as_frame_owner_node()
        )

    def as_child_dom_node(self) -> Optional[ChildDOMNode]:
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
            self.as_script_node() or
            self.as_domroot_node()
        )

    def as_leaf_dom_node(self) -> Optional[LeafDOMNode]:
        """Returns true if this is a node type that can appear in the DOM,
        and cannot have any child nodes within this frame."""
        return (
            self.as_text_node() or
            self.as_frame_owner_node()
        )

    def as_parent_dom_node(self) -> Optional[ParentDOMNode]:
        """Returns true if this node is valid to ever be the parent of
        another DOM node in w/in a frame (i.e., iframes/frame owners
        cannot be parents of other DOM nodes w/in the same frame)."""
        return (
            self.as_html_node() or
            self.as_domroot_node() or
            # below is surprising, but frameowner (i.e., iframe) nodes
            # can contain text elements, because if a page includes
            # an iframe like this <iframe>SOME TEXT</iframe>, blink will
            # initialize the "SOME TEXT" node as a child of the iframe,
            # even though those nodes will then be immediately replaced
            # with the child document.
            self.as_frame_owner_node()
        )

    def as_attributable_dom_node(self) -> Optional[AttrDOMNode]:
        return (
            self.as_html_node() or
            self.as_domroot_node() or
            self.as_frame_owner_node()
        )

    def as_actor_node(self) -> Optional[ActorNode]:
        return (
            self.as_script_node() or
            self.as_parser_node()
        )

    def as_storage_area_node(self) -> Optional["StorageAreaNode"]:
        return None

    def as_text_node(self) -> Optional["TextNode"]:
        return None

    def as_frame_owner_node(self) -> Optional["FrameOwnerNode"]:
        return None

    def as_script_node(self) -> Optional["ScriptNode"]:
        return None

    def as_domroot_node(self) -> Optional["DOMRootNode"]:
        return None

    def as_parser_node(self) -> Optional["ParserNode"]:
        return None

    def as_html_node(self) -> Optional["HTMLNode"]:
        return None

    def as_js_structure_node(self) -> Optional["JSStructureNode"]:
        return None

    def as_resource_node(self) -> Optional["ResourceNode"]:
        return None

    def as_cookie_jar_node(self) -> Optional["CookieJarNode"]:
        return None

    def as_local_storage_node(self) -> Optional["LocalStorageNode"]:
        return None

    def as_session_storage_node(self) -> Optional["SessionStorageNode"]:
        return None

    def is_toplevel_parser(self) -> bool:
        for incoming_edge in self.incoming_edges():
            if incoming_edge.as_cross_dom_edge() is not None:
                return False
        return True

    def frame_owner_nodes(self) -> list["FrameOwnerNode"]:
        frame_owner_nodes = []
        for node in self.pg.nodes():
            if frame_owner_node := node.as_frame_owner_node():
                frame_owner_nodes.append(frame_owner_node)
        return frame_owner_nodes

    def data(self) -> dict[str, str]:
        return cast(dict[str, str], self.pg.graph.nodes[self._id])

    def creation_edge(self) -> Optional["NodeCreateEdge"]:
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

    def executed_scripts(self) -> list[ScriptNode]:
        if self.pg.debug:
            is_executing_script = (
                self.as_text_node() or
                self.as_html_node() or
                self.as_script_node() or
                self.as_frame_owner_node() or
                self.as_domroot_node()
            )
            if not is_executing_script:
                self.throw("Unexpected node executing a script")
        executed_scripts = []
        for edge in self.outgoing_edges():
            if execute_edge := edge.as_execute_edge():
                executed_scripts.append(execute_edge.outgoing_node())
        return executed_scripts

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

    def creator_edge(self) -> Optional["NodeCreateEdge"]:
        for edge in self.incoming_edges():
            if create_edge := edge.as_create_edge():
                return create_edge
        self.throw("Could not find a creation edge for this node")
        return None


class ScriptNode(Node, Reportable):

    incoming_edge_types = [
        Edge.Types.EVENT_LISTENER,
        Edge.Types.EXECUTE,
        Edge.Types.EXECUTE_FROM_ATTRIBUTE,
        Edge.Types.JS_RESULT,
        Edge.Types.REQUEST_COMPLETE,
        Edge.Types.REQUEST_ERROR,
        Edge.Types.REQUEST_REDIRECT,
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

    summary_methods = {
        "hash": "hash",
        "script_type": "script_type",
    }

    # As defined by the Blink `ScriptSourceLocationType` enum
    # third_party/blink/renderer/bindings/core/v8/script_source_location_type.h
    class ScriptType(StrEnum):
        EVAL = "eval"
        EVAL_SCHEDULED = "eval for scheduled action"
        EXTERNAL = "external file"
        INLINE = "inline"
        INLINE_DOC_WRITE = "inline inside document write"
        INLINE_ELM = "inline inside generated element"
        INSPECTOR = "inspector"
        INTERNAL = "internal"
        JS_URL = "javascript url"
        MODULE = "module"
        UNKNOWN = "unknown"

    def as_script_node(self) -> Optional["ScriptNode"]:
        return self

    def created_nodes(self) -> list[Node]:
        created_nodes = []
        for edge in self.outgoing_edges():
            if create_edge := edge.as_create_edge():
                created_nodes.append(create_edge.outgoing_node())
        return created_nodes

    def script_type(self) -> "ScriptNode.ScriptType":
        script_type_raw = self.data()[Node.RawAttrs.SCRIPT_TYPE.value]
        try:
            return ScriptNode.ScriptType(script_type_raw)
        except ValueError:
            return ScriptNode.ScriptType.UNKNOWN

    def execute_edge(self) -> "ExecuteEdge":
        execute_edge = None
        for edge in self.incoming_edges():
            if execute_edge := edge.as_execute_edge():
                break
        if self.pg.debug:
            if not execute_edge:
                self.throw("Could not find execution edge for script")
        assert execute_edge
        return execute_edge

    def creator_node(self) -> Union["ActorNode", "ParentDOMNode"]:
        node = self.execute_edge().incoming_node()
        creator_node = (
            node.as_actor_node() or
            node.as_parent_dom_node()
        )
        assert creator_node
        return creator_node

    def to_report(self, include_source: bool = False) -> ScriptReport:
        executor_report: Union[ScriptReport, DOMElementReport, None] = None
        executor_node = self.creator_node()
        if executor_node.as_parser_node() is not None:
            executor_report = None

        elif script_node := executor_node.as_script_node():
            executor_report = script_node.to_report(include_source)
        elif html_elm_node := executor_node.as_html_node():
            executor_report = html_elm_node.to_report(include_source)
        elif frame_owner_node := executor_node.as_frame_owner_node():
            executor_report = frame_owner_node.to_report(include_source)

        url = None
        if self.script_type() == ScriptNode.ScriptType.EXTERNAL:
            url = self.url()

        report = ScriptReport(self.pg_id(), self.script_type(), self.hash())
        report.url = url
        report.executor = executor_report
        if include_source:
            report.source = self.source()
        return report

    def source(self) -> str:
        try:
            return self.data()[Node.RawAttrs.SOURCE.value]
        except KeyError:
            return ""

    def hash(self) -> str:
        hasher = hashlib.new("sha256")
        hasher.update(self.source().encode("utf8"))
        return b64encode(hasher.digest()).decode("utf8")

    def url(self) -> Url:
        # If all of the following are correct, then we can be certain
        # about associating this script with a particular URL.
        # 1. this script is script type EXTERNAL
        # 2. the executing node is an HTML node
        # 3. the executing node has only one
        #    outgoing execution edge (to the `self` node here)
        # 4. the executing node has only outgoing request edge
        # 5. the outgoing request successfully completed
        # 6. that resulting request is for script
        can_use_direct_url_method = True
        if self.pg.debug:
            # Test for requirement 1 above
            if self.script_type() != ScriptNode.ScriptType.EXTERNAL:
                self.throw("Cannot ask for URL of non-external script")

        incoming_node = self.execute_edge().incoming_node()
        if self.pg.debug:
            # Test for requirement 2 above
            if incoming_node.as_html_node() is None:
                incoming_node.throw("Unexpected execute edge")

        executing_node = cast("HTMLNode", incoming_node)
        # Test for requirement 3 above
        execution_edges = []
        for outgoing_edge in executing_node.outgoing_edges():
            if execution_edge := outgoing_edge.as_execute_edge():
                execution_edges.append(execution_edge)

        # A little odd to use a `while` statement here, since we'll
        # never loop, but just done so we can easily jump out of the
        # series of checks with a `break`
        while len(execution_edges) == 1:
            # Test for requirement 4 above
            requests_from_node = executing_node.requests()
            if len(requests_from_node) != 1:
                break
            request_chain = requests_from_node[0]
            # Test for requirements 5
            successful_request = request_chain.success_request()
            if not successful_request:
                break
            if request_chain.resource_type() != ResourceType.SCRIPT:
                break
            # Otherwise, if we're here, we can confidently and correctly
            # get the URL the script came from, based off the requests
            # initiated by the executing node.
            return request_chain.final_url()

        # Otherwise we have to try and match this script with request
        # responses by hash, which has at least one rare bug that causes
        # the python generated hash to not match the PageGraph generated
        # graph in the XML. So we do this matching as a last resort.
        # For note, this bug can be reproduced by fetching the following
        # redirecting URL:
        #    https://sslwidget.criteo.com/event?a=21479&v=5.23.0
        #    &otl=1&p0=e%3Dce%26m%3D%255B%255D&p1=e%3Dsetcurrency%26c%3DUSD
        #    &p2=e%3Dexd%26site_type%3Dm&p3=e%3Dvh&p4=e%3Ddis&adce=1
        #    &bundle=nVg9El9uTERKdEUycGp2R2dhM2VaalJoaGhYZ1NkdHFSWTlpd0FSWlBZeSUyRm5LeGV2OWd6JTJCZUJncGZUbTZNVjJFWXlxSVZVR3luMjdDOWdKWWFsUXAwMyUyRmNUdyUyRmFvdmhLJTJGWVVoJTJGS1MlMkYxRmYwZURjT2N1cW9pZXY3bmslMkI1VENObU5vZUNlWUFXY0tRUVdHOUIyYTJrdTF3UXJBJTNEJTNE
        #    &tld=shein.com.mx&fu=https%253A%252F%252Fm.shein.com.mx%252F
        #    &ceid=7af27d1e-ff03-43dc-89ac-064fc890a79a&dtycbr=22540
        script_hash = self.hash()
        matching_request_chain = None
        for request_chain in executing_node.requests():
            if request_chain.hash() == script_hash:
                matching_request_chain = request_chain
                break

        # If we still haven't found the relevant request chain, we
        # last ditch check to see if the resource was cached, or otherwise
        # already fetched, and so a request wasn't attributed to the
        # HTML element.
        if not matching_request_chain:
            other_requests = self.pg.unattributed_requests()
            for request_chain in other_requests:
                if request_chain.hash() == script_hash:
                    matching_request_chain = request_chain
                    break

        if self.pg.debug:
            if not matching_request_chain:
                self.throw("Unable to find request for this script")
        assert matching_request_chain
        return matching_request_chain.request.url()


class DOMElementNode(Node, ABC):

    def blink_id(self) -> BlinkId:
        return int(self.data()[Node.RawAttrs.BLINK_ID.value])

    def tag_name(self) -> str:
        raise NotImplementedError()

    def insertion_edges(self) -> list["NodeInsertEdge"]:
        insertion_edges: list["NodeInsertEdge"] = []
        for edge in self.incoming_edges():
            if insert_edge := edge.as_insert_edge():
                insertion_edges.append(insert_edge)
        return sort_elements(insertion_edges)

    def insert_edge(self) -> Optional["NodeInsertEdge"]:
        """Return the most recent edge describing when this element
        was appended to a document."""
        insertion_edges = self.insertion_edges()
        try:
            return insertion_edges[-1]
        except IndexError:
            return None

    def parent_at_serialization(self) -> Optional[ParentDOMNode]:
        incoming_edges = self.incoming_edges()
        if self.pg.feature_check(Feature.DOCUMENT_EDGES):
            for edge in self.incoming_edges():
                if document_edge := edge.as_document_edge():
                    return document_edge.incoming_node()
        else:
            for edge in self.incoming_edges():
                structure_edge = edge.as_structure_edge()
                if not structure_edge:
                    continue
                incoming_node = structure_edge.incoming_node()
                parent_node = incoming_node.as_parent_dom_node()
                assert parent_node
                return parent_node
        return None

    def creation_edge(self) -> "NodeCreateEdge":
        creation_edge = None
        for edge in self.incoming_edges():
            if creation_edge := edge.as_create_edge():
                break
        assert creation_edge
        return creation_edge

    def creator_node(self) -> ActorNode:
        return self.creation_edge().incoming_node()

    def domroot_node(self) -> DOMRootNode:
        """Returns a best effort of what frame / DOMRootNode to associate
        this element with. Since an DOM element can be attached to
        multiple documents / multiple frames, this may not be what you're
        looking for."""
        return (
            self.domroot_for_serialization() or
            self.domroot_for_document() or
            self.domroot_for_creation()
        )

    def domroot_for_creation(self) -> DOMRootNode:
        """Returns the DOMRootNode that is the execution context
        that this element was created in. Node that this could differ
        from the DOMRootNode / frame that the element was inserted into."""
        creation_frame_id = self.creation_edge().frame_id()
        return self.pg.domroot_for_frame_id(creation_frame_id)

    def domroot_for_document(self) -> Optional["DOMRootNode"]:
        """Returns the DOMRootNode for the most last document the element
        was attached to. Note that this *does not* mean the this element
        was attached to the document at serialization (since the element
        could have been attached and then removed), *nor* does it mean
        that this was the only document this element was attached to
        (since the element could have been moved between documents)."""
        insert_edge = self.insert_edge()
        if not insert_edge:
            return None
        return insert_edge.domroot_for_frame_id()

    def domroot_for_serialization(self) -> Optional["DOMRootNode"]:
        """Get the DOMRootNode for the document this element is attached
        to at serialization time. Note that this could be `None` (if
        this element is not attached to a document at serialization),
        and could differ from the domroot of the context the element
        was created in (if this element was moved between documents
        during page execution)."""
        current_node = self.parent_at_serialization()
        while current_node:
            if domroot_node := current_node.as_domroot_node():
                return domroot_node
            current_node = current_node.parent_at_serialization()
        return None

        parent_node_from_structure = self._domroot_from_parent_node_path()
        if parent_node_from_structure:
            return parent_node_from_structure
        return super().domroot()


class HTMLNode(DOMElementNode, Reportable):

    summary_methods = {
        "tag name": "tag_name"
    }

    def as_html_node(self) -> Optional["HTMLNode"]:
        return self

    def to_report(self, *args: Any) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def parent_html_nodes(self) -> list[ParentDOMNode]:
        """Return every node this node was ever inserted under. This can be
        zero nodes (if the node was created but never inserted in the
        document), or more than one node (if the node was moved around the
        document during execution)."""
        parent_html_nodes = []
        for e in self.incoming_edges():
            if insert_edge := e.as_insert_edge():
                parent_html_nodes.append(insert_edge.inserted_below_node())
        return parent_html_nodes

    def _domroot_from_parent_node_path(self) -> DOMRootNode | None:
        """Tries to follow all chains of nodes that this node was inserted
        as a child of. Its possible that we cannot get to a docroot node
        in this path though (for example, nodes trees created in script
        but not inserted in a document), in which case, we return None."""
        for parent_node in self.parent_html_nodes():
            if domroot_node := parent_node.as_domroot_node():
                return domroot_node
            elif html_node := parent_node.as_html_node():
                return html_node._domroot_from_parent_node_path()
        return None

    def requests(self) -> list[RequestChain]:
        chains: list[RequestChain] = []
        for outgoing_edge in self.outgoing_edges():
            if request_start_edge := outgoing_edge.as_request_start_edge():
                request_id = request_start_edge.request_id()
                request_chain = self.pg.request_chain_for_id(request_id)
                chains.append(request_chain)
        return chains


class FrameOwnerNode(DOMElementNode, Reportable):

    def as_frame_owner_node(self) -> Optional["FrameOwnerNode"]:
        return self

    def to_report(self, *args: Any) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def child_parser_nodes(self) -> list[ParserNode]:
        child_parser_nodes = []
        for child_node in self.child_nodes():
            if parser_node := child_node.as_parser_node():
                child_parser_nodes.append(parser_node)
        return child_parser_nodes

    def domroot_nodes(self) -> list[DOMRootNode]:
        domroots = []
        if self.pg.feature_check(Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS):
            for edge in self.outgoing_edges():
                if cross_dom_edge := edge.as_cross_dom_edge():
                    node = cross_dom_edge.outgoing_node().as_domroot_node()
                    assert node
                    domroots.append(node)
        else:
            for parser_node in self.child_parser_nodes():
                nodes = list(parser_node.domroots())
                domroots_sorted = sorted(nodes, key=lambda x: x.id())
                for domroot_node in domroots_sorted:
                    domroots.append(domroot_node)
        return domroots

    def tag_name(self) -> str:
        return self.data()[self.RawAttrs.TAG.value]


class TextNode(DOMElementNode, Reportable):

    def as_text_node(self) -> Optional["TextNode"]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def tag_name(self) -> str:
        return "[text]"


class DOMRootNode(DOMElementNode, Reportable):

    def as_domroot_node(self) -> Optional["DOMRootNode"]:
        return self

    def frame_owner_node(self) -> Optional["FrameOwnerNode"]:
        for edge in self.incoming_edges():
            if cross_dom_edge := edge.as_cross_dom_edge():
                return cross_dom_edge.incoming_node()
        return None

    def is_init_domroot(self) -> bool:
        # Blink creates an initial "about:blank" frame for every
        # <iframe> tag
        if self.url() != "about:blank":
            return False
        for edge in self.incoming_edges():
            if edge.as_structure_edge() is not None:
                return True
        return False

    def to_report(self) -> FrameReport:
        return FrameReport(self.pg_id(), self.url(), self.blink_id())

    def is_top_level_domroot(self) -> bool:
        frame_url = self.url()
        if not frame_url or frame_url == "about:blank":
            return False
        for edge in self.incoming_edges():
            if edge.as_cross_dom_edge() is not None:
                return False
        return True

    def is_local_domroot(self) -> bool:
        parent_frame = self.parent_domroot_node()
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

    def parent_domroot_node(self) -> Optional["DOMRootNode"]:
        assert not self.is_top_level_domroot()
        frame_owner_node = self.frame_owner_node()
        assert frame_owner_node
        domroot_for_frame_owner_node = frame_owner_node.domroot_node()
        return domroot_for_frame_owner_node

    def frame_id(self) -> FrameId:
        return int(self.data()[self.RawAttrs.BLINK_ID.value])

    def url(self) -> Url | None:
        try:
            return self.data()[self.RawAttrs.URL.value]
        except KeyError:
            # This will happen for temporary frame owner nodes that
            # are created before the document is setup
            return None

    def tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def parser(self) -> Optional[ParserNode]:
        parser_node = None
        for node in self.parent_nodes():
            if parser_node := node.as_parser_node():
                break
        assert parser_node
        return parser_node


class ParserNode(Node):

    incoming_node_types = [
        Node.Types.FRAME_OWNER,
        # The RESOURCE case is uncommon, but occurs when something is
        # fetched that doesn't have a representation in the graph,
        # most commonly a pre* <meta> instruction.
        Node.Types.RESOURCE
    ]

    def as_parser_node(self) -> Optional["ParserNode"]:
        return self

    def frame_owner_node(self) -> Optional["FrameOwnerNode"]:
        parent_nodes_list = list(self.parent_nodes())
        frame_owner_nodes = []
        for parent_node in parent_nodes_list:
            if frame_owner_node := parent_node.as_frame_owner_node():
                frame_owner_nodes.append(frame_owner_node)
        if self.pg.debug:
            if len(frame_owner_nodes) != 1:
                self.throw("Did not find exactly 1 parent frame owner node")
        return frame_owner_nodes[0]

    def created_nodes(self) -> list[Node]:
        created_nodes = []
        for edge in self.outgoing_edges():
            if create_edge := edge.as_create_edge():
                created_nodes.append(create_edge.outgoing_node())
        return created_nodes

    def domroots(self) -> list[DOMRootNode]:
        domroots = []
        already_returned = set()
        for e in self.outgoing_edges():
            if (e.as_create_edge() is None and e.as_structure_edge() is None):
                continue
            child_node = e.outgoing_node()
            if child_node in already_returned:
                continue
            if domroot_node := child_node.as_domroot_node():
                already_returned.add(domroot_node)
                domroots.append(domroot_node)
        return domroots


class ResourceNode(Node):

    outgoing_edge_types = [
        Edge.Types.REQUEST_COMPLETE,
        Edge.Types.REQUEST_ERROR,
        Edge.Types.REQUEST_REDIRECT,
    ]

    incoming_edge_types = [
        # Incoming redirect edges denote a request that was redirected
        # to this resource, from another resource. In this case,
        # both the incoming and outgoing node for the redirect edge
        # will be `ResourceNode` nodes.
        Edge.Types.REQUEST_REDIRECT,
        Edge.Types.REQUEST_START,
    ]

    summary_methods = {
        "url": "url"
    }

    # Instance properties
    requests_map: dict[RequestId, RequestResponse]

    def __init__(self, graph: "PageGraph", pg_id: PageGraphId):
        self.requests_map = {}
        super().__init__(graph, pg_id)

    def as_resource_node(self) -> Optional["ResourceNode"]:
        return self

    def url(self) -> Url:
        return self.data()[Node.RawAttrs.URL.value]

    def incoming_edges(self) -> list["RequestStartEdge"]:
        return cast(list["RequestStartEdge"], super().incoming_edges())

    def outgoing_edges(self) -> list["RequestResponseEdge"]:
        outgoing_edges: list["RequestResponseEdge"] = []
        for edge in super().outgoing_edges():
            if request_complete_edge := edge.as_request_complete_edge():
                outgoing_edges.append(request_complete_edge)
            elif request_redirect_edge := edge.as_request_redirect_edge():
                outgoing_edges.append(request_redirect_edge)
            elif request_error_edge := edge.as_request_error_edge():
                outgoing_edges.append(request_error_edge)
        return outgoing_edges

    def requesters(self) -> list["RequesterNode"]:
        requesters = []
        for edge in self.incoming_edges():
            requesters.append(edge.incoming_node())
        return requesters

    def build_caches(self) -> None:
        for incoming_edge in self.incoming_edges():
            request_id = incoming_edge.request_id()
            if self.pg.debug:
                if request_id in self.requests_map:
                    self.throw("Found duplicate request id")
            request_response = RequestResponse(incoming_edge)
            self.requests_map[request_id] = request_response

        for outgoing_edge in self.outgoing_edges():
            request_id = outgoing_edge.request_id()
            if self.pg.debug:
                if request_id not in self.requests_map:
                    self.throw("Response without request for resource")
                if self.requests_map[request_id].response is not None:
                    self.throw("Second response for request for resource")
            self.requests_map[request_id].response = outgoing_edge

    def response_for_id(self,
                        request_id: RequestId) -> "RequestResponseEdge" | None:
        if self.pg.debug:
            if request_id not in self.requests_map:
                self.throw("Unexpected request id")
        return self.requests_map[request_id].response


class JSStructureNode(Node, Reportable):
    def to_report(self) -> JSStructureReport:
        return JSStructureReport(self.name(), self.type_name())

    def as_js_structure_node(self) -> Optional["JSStructureNode"]:
        return self

    def name(self) -> str:
        return self.data()[self.RawAttrs.METHOD.value]

    def call_results(self) -> list["JSCallResult"]:
        js_calls = self.incoming_edges()
        js_results = self.outgoing_edges()
        calls_and_results_unsorted = list(chain(js_calls, js_results))
        calls_and_results = sorted(
            calls_and_results_unsorted, key=lambda x: x.id())

        if self.pg.debug:
            num_calls = len(list(js_calls))
            num_results = len(list(js_results))
            if num_results > num_calls:
                self.throw("Found more results than calls to this builtin, "
                           f"calls={num_calls}, results={num_results}")

            last_edge = calls_and_results[0]
            for edge in calls_and_results[1:]:
                if edge.as_js_result_edge() is not None:
                    if last_edge.as_js_result_edge() is not None:
                        self.throw("Found two adjacent result edges: "
                                   f"{last_edge.pg_id()} and {edge.pg_id()}")
                last_edge = edge

        call_results: list[JSCallResult] = []
        for edge in calls_and_results:
            if js_result_edge := edge.as_js_result_edge():
                last_call_result = call_results[-1]
                last_call_result.result_edge = js_result_edge
            elif js_call_edge := edge.as_js_call_edge():
                a_call_result = JSCallResult(js_call_edge, None)
                call_results.append(a_call_result)
        return call_results

    def incoming_edges(self) -> list["JSCallEdge"]:
        return cast(list["JSCallEdge"], super().incoming_edges())

    def outgoing_edges(self) -> list["JSResultEdge"]:
        return cast(list["JSResultEdge"], super().outgoing_edges())


class JSBuiltInNode(JSStructureNode):
    incoming_edge_types = [
        Edge.Types.JS_CALL
    ]

    outgoing_edge_types = [
        Edge.Types.JS_RESULT
    ]

    def as_js_builtin_node(self) -> Optional["JSBuiltInNode"]:
        return self


class WebAPINode(JSStructureNode):
    incoming_edge_types = [
        Edge.Types.JS_CALL
    ]

    outgoing_edge_types = [
        Edge.Types.JS_RESULT
    ]

    def as_web_api_node(self) -> Optional["WebAPINode"]:
        return self


class StorageNode(Node):
    incoming_edge_types = []

    outgoing_edge_types = [
        Edge.Types.STORAGE_BUCKET
    ]

    def as_storage_node(self) -> Optional["StorageNode"]:
        return self


class StorageAreaNode(Node, ABC):
    incoming_edge_types = [
        Edge.Types.STORAGE_BUCKET,
        Edge.Types.STORAGE_CLEAR,
        Edge.Types.STORAGE_DELETE,
        Edge.Types.STORAGE_READ_CALL,
        Edge.Types.STORAGE_SET,
    ]

    outgoing_edge_types = [
        Edge.Types.STORAGE_READ_RESULT
    ]

    def as_storage_area_node(self) -> Optional["StorageAreaNode"]:
        return (
            self.as_cookie_jar_node() or
            self.as_local_storage_node() or
            self.as_session_storage_node()
        )


class CookieJarNode(StorageAreaNode):

    def as_cookie_jar_node(self) -> Optional["CookieJarNode"]:
        return self


class LocalStorageNode(StorageAreaNode):

    def as_local_storage_node(self) -> Optional["LocalStorageNode"]:
        return self


class SessionStorageNode(StorageAreaNode):

    def as_session_storage_node(self) -> Optional["SessionStorageNode"]:
        return self


class DeprecatedNode(Node):
    pass


TYPE_MAPPING: dict[Node.Types, Type[Node]] = dict([
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
