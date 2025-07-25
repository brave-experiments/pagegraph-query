from __future__ import annotations

from base64 import b64encode
from enum import Enum
import hashlib
from typing import Union, Optional, TYPE_CHECKING

from pagegraph.graph.node import Node
from pagegraph.graph.node.abc.script import ScriptNode
from pagegraph.graph.node.text import TextNode
from pagegraph.serialize import Reportable, ScriptReport
from pagegraph.types import ResourceType

if TYPE_CHECKING:
    from pagegraph.graph.edge.execute import ExecuteEdge
    from pagegraph.graph.js import JSCallResult
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.requests import RequestChain
    from pagegraph.types import Url, ActorNode
    from pagegraph.types import ScriptExecutorNode
    from pagegraph.serialize import DOMElementReport


class ScriptLocalNode(ScriptNode, Reportable):

    # As defined by the Blink `ScriptSourceLocationType` enum
    # third_party/blink/renderer/bindings/core/v8/script_source_location_type.h
    class ScriptType(Enum):
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

    summary_methods = {
        "hash": "hash",
        "script_type": "script_type",
        "url": "url_if_external"
    }

    script_types_potentially_with_urls = {ScriptType.EXTERNAL, ScriptType.MODULE}

    def as_script_local_node(self) -> Optional[ScriptLocalNode]:
        return self

    def created_nodes(self) -> list[Node]:
        created_nodes = []
        for edge in self.outgoing_edges():
            if create_edge := edge.as_create_edge():
                created_nodes.append(create_edge.outgoing_node())
        return created_nodes

    def calls(self, method_name: Optional[str] = None) -> list[JSCallResult]:
        js_call_results = []
        for edge in self.outgoing_edges():
            if js_call_edge := edge.as_js_call_edge():
                if method_name is not None:
                    if js_call_edge.outgoing_node().name() != method_name:
                        continue
                call_result = js_call_edge.call_result()
                js_call_results.append(call_result)
        return js_call_results

    def script_type(self) -> ScriptLocalNode.ScriptType:
        script_type_raw = self.data()[self.RawAttrs.SCRIPT_TYPE.value]
        try:
            return self.__class__.ScriptType(script_type_raw)
        except ValueError:
            return self.__class__.ScriptType.UNKNOWN

    def executor_node(self) -> ScriptExecutorNode:
        return self.execute_edge().incoming_node()

    def creator_node(self) -> Union[ActorNode, ParentDOMElementNode]:
        node = self.execute_edge().incoming_node()
        if parent_script_local_node := node.as_script_local_node():
            return parent_script_local_node.creator_node()
        creator_node = (
            node.as_actor_node() or
            node.as_parent_dom_element_node()
        )
        assert creator_node
        return creator_node

    def to_report(self, include_source: bool = False) -> ScriptReport:
        executor_report: Union[ScriptReport, DOMElementReport, None] = None
        executor_node = self.creator_node()
        if executor_node.as_parser_node() is not None:
            executor_report = None

        elif script_node := executor_node.as_script_local_node():
            executor_report = script_node.to_report(include_source)
        elif html_elm_node := executor_node.as_html_node():
            executor_report = html_elm_node.to_report()
        elif frame_owner_node := executor_node.as_frame_owner_node():
            executor_report = frame_owner_node.to_report()

        url = self.url_if_available()

        report = ScriptReport(self.pg_id(), self.script_type().value,
                              self.hash())
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

    def url_if_external(self) -> Optional[Url]:
        if self.script_type() != self.__class__.ScriptType.EXTERNAL:
            return None
        return self.url()

    def url_if_available(self) -> Optional[Url]:
        if self.script_type() not in ScriptLocalNode.script_types_potentially_with_urls:
            return None
        # Inline scripts can also have the module type, but have no URL.
        if self.script_type() == ScriptLocalNode.ScriptType.MODULE and self.matching_text_node():
            return None
        return self.url()

    def url(self) -> Url:
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
        if self.pg.debug and script_type not in ScriptLocalNode.script_types_potentially_with_urls:
            self.throw("Cannot ask for URL of non-external script")

        creator_node = self.creator_node()
        # Test for requirement 2 above
        if self.pg.debug and creator_node.as_html_node() is None:
            creator_node.throw("Unexpected execute edge")

        executing_node = creator_node.as_html_node()
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
            # Test for requirements 6
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

    def matching_request_chain(self) -> Optional[RequestChain]:
        script_hash = self.hash()
        creator_node = self.creator_node()
        executing_node = creator_node.as_html_node()
        assert executing_node
        for request_chain in executing_node.requests():
            if request_chain.hash() == script_hash:
                return request_chain
        return None

    def matching_unattributed_request(self) -> Optional[RequestChain]:
        script_hash = self.hash()
        unattributed_requests = self.pg.unattributed_requests()
        for request_chain in unattributed_requests:
            if request_chain.hash() == script_hash:
                return request_chain
        return None

    def matching_text_node(self) -> Optional[TextNode]:
        script_hash = self.hash()
        creator_node = self.creator_node()
        for edge in creator_node.outgoing_edges():
            if create_edge := edge.as_document_edge():
                node = create_edge.outgoing_node()
                if text_node := node.as_text_node():
                    if text_node.hash() == script_hash:
                        return text_node
        return None

    def execution_context_in(self) -> DOMRootNode:
        exc_edge = self.execute_edge()
        return self.pg.domroot_for_frame_id(exc_edge.frame_id())

    def execution_context_from(self) -> DOMRootNode:
        exc_edge = self.execute_edge()
        exc_node = self.executor_node()
        frame_id = None

        if parent_dom_node := exc_node.as_parent_dom_element_node():
            return parent_dom_node.execution_context()

        if script_local_node := exc_node.as_script_local_node():
            return script_local_node.execution_context_from()

        if exc_node.as_parser_node() is not None:
            frame_id = exc_edge.frame_id()
        elif exc_node.as_script_remote_node() is not None:
            frame_id = exc_edge.frame_id()
        else:
            self.throw("Could not determine execution frame for local script")
        assert frame_id
        return self.pg.domroot_for_frame_id(exc_edge.frame_id())
