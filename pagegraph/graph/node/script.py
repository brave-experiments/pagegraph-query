from base64 import b64encode
from enum import StrEnum
import hashlib
from typing import Union, Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.graph.node import Node
from pagegraph.serialize import Reportable, ScriptReport
from pagegraph.types import ResourceType

if TYPE_CHECKING:
    from pagegraph.graph.edge.execute import ExecuteEdge
    from pagegraph.graph.requests import RequestChain
    from pagegraph.types import Url, ParentDomNode, ActorNode
    from pagegraph.serialize import DOMElementReport


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

    def created_nodes(self) -> list["Node"]:
        created_nodes = []
        for edge in self.outgoing_edges():
            if create_edge := edge.as_create_edge():
                created_nodes.append(create_edge.outgoing_node())
        return created_nodes

    def script_type(self) -> "ScriptNode.ScriptType":
        script_type_raw = self.data()[self.RawAttrs.SCRIPT_TYPE.value]
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

    def creator_node(self) -> Union["ActorNode", "ParentDomNode"]:
        node = self.execute_edge().incoming_node()
        creator_node = (
            node.as_actor_node() or
            node.as_parent_dom_node()
        )
        assert creator_node
        return creator_node

    def to_report(self, include_source: bool = False) -> ScriptReport:
        executor_report: Union[ScriptReport, "DOMElementReport", None] = None
        executor_node = self.creator_node()
        if executor_node.as_parser_node() is not None:
            executor_report = None

        elif script_node := executor_node.as_script_node():
            executor_report = script_node.to_report(include_source)
        elif html_elm_node := executor_node.as_html_node():
            executor_report = html_elm_node.to_report()
        elif frame_owner_node := executor_node.as_frame_owner_node():
            executor_report = frame_owner_node.to_report()

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

    def url(self) -> "Url":
        # pylint: disable=line-too-long
        # If all of the following are correct, then we can be certain
        # about associating this script with a particular URL.
        # 1. this script is script type EXTERNAL
        # 2. the executing node is an HTML node
        # 3. the executing node has only one
        #    outgoing execution edge (to the `self` node here)
        # 4. the executing node has only outgoing request edge
        # 5. the outgoing request successfully completed
        # 6. that resulting request is for script
        # Test for requirement 1 above
        script_type = self.script_type()
        if self.pg.debug and script_type != ScriptNode.ScriptType.EXTERNAL:
            self.throw("Cannot ask for URL of non-external script")

        incoming_node = self.execute_edge().incoming_node()
        # Test for requirement 2 above
        if self.pg.debug and incoming_node.as_html_node() is None:
            incoming_node.throw("Unexpected execute edge")

        executing_node = incoming_node.as_html_node()
        assert executing_node
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
        matching_request_chain = self.matching_request_chain()

        # If we still haven't found the relevant request chain, we
        # last ditch check to see if the resource was cached, or otherwise
        # already fetched, and so a request wasn't attributed to the
        # HTML element.
        if not matching_request_chain:
            matching_request_chain = self.matching_unattributed_request()

        if self.pg.debug and not matching_request_chain:
            self.throw("Unable to find request for this script")
        assert matching_request_chain
        return matching_request_chain.request.url()

    def matching_request_chain(self) -> Optional["RequestChain"]:
        script_hash = self.hash()
        incoming_node = self.execute_edge().incoming_node()
        executing_node = incoming_node.as_html_node()
        assert executing_node
        for request_chain in executing_node.requests():
            if request_chain.hash() == script_hash:
                return request_chain
        return None

    def matching_unattributed_request(self) -> Optional["RequestChain"]:
        script_hash = self.hash()
        unattributed_requests = self.pg.unattributed_requests()
        for request_chain in unattributed_requests:
            if request_chain.hash() == script_hash:
                return request_chain
        return None
