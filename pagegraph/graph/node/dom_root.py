from __future__ import annotations

from enum import Enum
from typing import Callable, Optional, TYPE_CHECKING, TypeVar

from pagegraph.graph.node.abc.dom_element import DOMElementNode
from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
from pagegraph.serialize import Reportable, FrameReport
from pagegraph.urls import is_url_local, is_security_origin_inheriting_url
from pagegraph.urls import security_origin_from_url
from pagegraph.versions import Feature, exception_for_feature

if TYPE_CHECKING:
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.graph.node.script_local import ScriptLocalNode
    from pagegraph.types import Url, FrameId


class ChildNodeFilter(Enum):
    AT_CREATION = 1
    AT_INSERTION = 2
    AT_SERIALIZATION = 3
    ALL = 4


T = TypeVar('T', bound=DOMElementNode)
CNF = ChildNodeFilter
DOMNodeFilterFunc = Callable[[T], bool]
OptionalDOMNodeFilter = Optional[DOMNodeFilterFunc[T]]


class DOMRootNode(ParentDOMElementNode, Reportable):

    summary_methods = {
        "frame id": "frame_id",
        "security origin": "security_origin",
        "tag name": "tag_name",
        "url": "url",
    }

    def validate(self) -> None:
        """Add the additional validation step to make sure that the
        security origins we see explicitly included in graphs match
        what we expect them to be based on the graph structure (note
        this validation step will only be taken on graphs recent enough
        to include the security origin as an attribute)."""
        if self.pg.feature_check(Feature.EXPLICIT_SECURITY_ORIGINS):
            explicit_security_origin = self.__security_origin()
            calculated_security_origin = self.__calculate_security_origin()
            if explicit_security_origin != calculated_security_origin:
                self.throw(
                    f"Explicit security origin '{explicit_security_origin}' "
                    "did not match what we expect the security origin to be "
                    f"('{calculated_security_origin}')")
        return super().validate()

    def as_domroot_node(self) -> Optional[DOMRootNode]:
        return self

    def frame_owner_node(self) -> Optional[FrameOwnerNode]:
        if self.pg.feature_check(Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS):
            for edge in self.incoming_edges():
                if cross_dom_edge := edge.as_cross_dom_edge():
                    return cross_dom_edge.incoming_node()
        else:
            parent_frame_owner_nodes: list[FrameOwnerNode] = []
            for parent_node in self.parent_nodes():
                if frame_owner_node := parent_node.as_frame_owner_node():
                    parent_frame_owner_nodes.append(frame_owner_node)
            assert len(parent_frame_owner_nodes) == 1
            return parent_frame_owner_nodes[0]
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
        return FrameReport(self.pg_id(), self.is_top_level_domroot(),
                           self.url(), self.security_origin(), self.blink_id())

    def __calculate_security_origin(self) -> Optional[Url]:
        """Calculates the security origin of the frame based on graph structure.

        Older versions of PageGraph files did not explicitly include the
        Blink-determined security origin of the frame, and instead determined
        the security origin based on the frame's URL and the graph structure.
        This isn't necessary anymore, since the origin is explicitly recorded.
        This method ignores the explicit value, and determines it based on
        graph structure. This is only used currently as another step of graph
        validation."""
        this_url = self.url()
        if this_url and (sec_origin := security_origin_from_url(this_url)):
            return sec_origin
        if parent_domroot_node := self.parent_domroot_node():
            return parent_domroot_node.security_origin()
        return None

    def __security_origin(self) -> Optional[Url]:
        """Returns the security origin of the frame.

        This method returns the value for the "security origin" attribute from
        the XML. This method only works for graph files version 0.7.4 or more
        recent. Otherwise, raises an exception."""
        if self.pg.feature_check(Feature.EXPLICIT_SECURITY_ORIGINS):
            origin: Optional[str] = str(self.data()[self.RawAttrs.SECURITY_ORIGIN.value])
            if origin == "null":
                return None
            return origin
        raise exception_for_feature(Feature.EXPLICIT_SECURITY_ORIGINS)

    def security_origin(self) -> Optional[Url]:
        """Calculates the security origin for the frame.

        Usually this'll be determined by the URL of the frame, but in some
        cases (such as an about:blank frame) it'll be inherited from the
        parent frame."""

        # In more recent versions of PageGraph recordings, the security
        # origin of the frame is explicitly recorded in the graph, and so
        # doesn't require any calculation.
        if self.pg.feature_check(Feature.EXPLICIT_SECURITY_ORIGINS):
            return self.__security_origin()
        return self.__calculate_security_origin()

    def is_top_level_domroot(self) -> bool:
        for edge in self.incoming_edges():
            if edge.as_cross_dom_edge() is not None:
                return False
        return True

    def is_security_origin_inheriting(self) -> bool:
        """Returns true if the frame inherits its security origin.

        This happens if the frame has either an about:blank or about:srcdoc
        Url, in which case the frame inherits its security origin from
        its parent frame."""
        this_frame_url = self.url()
        if not this_frame_url:
            return False
        return is_security_origin_inheriting_url(this_frame_url)

    def is_local_domroot(self) -> bool:
        """Returns true if frame has the same origin as the parent frame."""
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

    def parent_domroot_node(self) -> Optional[DOMRootNode]:
        frame_owner_node = self.frame_owner_node()
        if not frame_owner_node:
            return None
        domroot_for_frame_owner_node = frame_owner_node.execution_context()
        return domroot_for_frame_owner_node

    def is_attached(self) -> bool:
        """Whether the document was attached to a frame at serialization."""
        return bool(self.data()[self.RawAttrs.IS_ATTACHED.value])

    def frame_id(self) -> FrameId:
        return int(self.data()[self.RawAttrs.BLINK_ID.value])

    def url(self) -> Optional[Url]:
        try:
            return self.data()[self.RawAttrs.URL.value]
        except KeyError:
            # This will happen for temporary frame owner nodes that
            # are created before the document is setup
            return None

    def parser(self) -> ParserNode:
        parser_node = None
        for node in self.parent_nodes():
            if parser_node := node.as_parser_node():
                break
        assert parser_node
        return parser_node

    def __matches(self, node: T, node_filter: CNF = CNF.ALL) -> bool:
        current_frame_id = self.frame_id()

        if node_filter in (CNF.AT_INSERTION, CNF.ALL):
            for edge in node.insertion_edges():
                if edge.frame_id() == current_frame_id:
                    return True

        if node_filter in (CNF.AT_CREATION, CNF.ALL):
            creation_edge = node.creation_edge()
            if creation_edge.frame_id() == current_frame_id:
                return True

        if node_filter in (CNF.AT_SERIALIZATION, CNF.ALL):
            serialization_domroot = node.domroot_for_serialization()
            if not serialization_domroot:
                return False
            if serialization_domroot.frame_id() == current_frame_id:
                return True
        return False

    def __filter_children(self, nodes: list[T], node_filter: CNF = CNF.ALL,
                          func: OptionalDOMNodeFilter[T] = None) -> list[T]:
        matching_nodes = set()
        for node in nodes:
            if self.__matches(node, node_filter):
                matching_nodes.add(node)
        return list(filter(func, matching_nodes))

    def frame_owner_nodes(self, node_filter: CNF = CNF.ALL,
                          func: OptionalDOMNodeFilter[
                                FrameOwnerNode
                            ] = None) -> list[FrameOwnerNode]:
        all_frame_owner_nodes = self.pg.frame_owner_nodes()
        return self.__filter_children(all_frame_owner_nodes, node_filter, func)

    def domroot_nodes(self, node_filter: CNF = CNF.ALL,
                      func: OptionalDOMNodeFilter[DOMRootNode] = None) -> list[DOMRootNode]:
        child_domroot_nodes = []
        child_frame_owner_nodes = self.frame_owner_nodes(node_filter)
        for node in child_frame_owner_nodes:
            child_domroot_nodes += node.child_domroot_nodes()
        return list(filter(func, child_domroot_nodes))

    def scripts_executed_in(self) -> list[ScriptLocalNode]:
        script_local_nodes = self.pg.script_local_nodes()
        current_frame_id = self.frame_id()

        scripts = set()
        for node in script_local_nodes:
            if node.execute_edge().frame_id() == current_frame_id:
                scripts.add(node)
        return list(scripts)

    def scripts_executed_from(self, node_filter: CNF = CNF.ALL) -> list[ScriptLocalNode]:
        current_frame_id = self.frame_id()
        script_local_nodes = self.pg.script_local_nodes()
        scripts = set()

        for script_node in script_local_nodes:
            execute_edge = script_node.execute_edge()
            ex_node = execute_edge.incoming_node()
            if dom_node := ex_node.as_parent_dom_element_node():
                if self.__matches(dom_node, node_filter):
                    scripts.add(script_node)
            elif ex_node.as_parser_node() is not None:
                if execute_edge.frame_id() == current_frame_id:
                    scripts.add(script_node)
            elif parent_script_node := ex_node.as_script_local_node():
                if parent_script_node.execution_context_from() == self:
                    scripts.add(script_node)
            else:
                pass
        return list(scripts)
