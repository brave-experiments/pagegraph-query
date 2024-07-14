from enum import Enum
from typing import Callable, Optional, TYPE_CHECKING, TypeVar

from pagegraph.graph.node.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, FrameReport
from pagegraph.util import is_url_local

if TYPE_CHECKING:
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.graph.node.script_local import ScriptLocalNode
    from pagegraph.types import Url, FrameId


T = TypeVar('T', bound=DOMElementNode)

class ChildNodeFilter(Enum):
    AT_CREATION = 1
    AT_INSERTION = 2
    AT_SERIALIZATION = 3
    ALL = 4


CNF = ChildNodeFilter
DOMNodeFilterFunc = Callable[[T], bool]
OptionalDOMNodeFilter = Optional[DOMNodeFilterFunc[T]]


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

    def frame_id(self) -> "FrameId":
        return int(self.data()[self.RawAttrs.BLINK_ID.value])

    def url(self) -> Optional["Url"]:
        try:
            return self.data()[self.RawAttrs.URL.value]
        except KeyError:
            # This will happen for temporary frame owner nodes that
            # are created before the document is setup
            return None

    def tag_name(self) -> str:
        return self.data()[self.RawAttrs.TAG.value]

    def parser(self) -> "ParserNode":
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
                                "FrameOwnerNode"
                            ] = None) -> list["FrameOwnerNode"]:
        all_frame_owner_nodes = self.pg.frame_owner_nodes()
        return self.__filter_children(all_frame_owner_nodes, node_filter, func)

    def domroot_nodes(self, node_filter: CNF = CNF.ALL,
                      func: OptionalDOMNodeFilter["DOMRootNode"] = None) -> list["DOMRootNode"]:
        child_domroot_nodes = []
        child_frame_owner_nodes = self.frame_owner_nodes(node_filter)
        for node in child_frame_owner_nodes:
            child_domroot_nodes += node.domroot_nodes()
        return list(filter(func, child_domroot_nodes))

    def scripts_executed_in(self) -> list["ScriptLocalNode"]:
        script_local_nodes = self.pg.script_local_nodes()
        current_frame_id = self.frame_id()

        scripts = set()
        for node in script_local_nodes:
            if node.execute_edge().frame_id() == current_frame_id:
                scripts.add(node)
        return list(scripts)

    def scripts_executed_from(self, node_filter: CNF = CNF.ALL) -> list["ScriptLocalNode"]:
        current_frame_id = self.frame_id()
        script_local_nodes = self.pg.script_local_nodes()
        scripts = set()

        for script_node in script_local_nodes:
            execute_edge = script_node.execute_edge()
            ex_node = execute_edge.incoming_node()
            # Union["ParentDomNode", "ParserNode", "ScriptNode"]
            if dom_node := ex_node.as_parent_dom_node():
                if self.__matches(dom_node, node_filter):
                    scripts.add(script_node)
            elif ex_node.as_parser_node() is not None:
                if execute_edge.frame_id() == current_frame_id:
                    scripts.add(script_node)
            elif parent_script_node := ex_node.as_script_local_node():
                if parent_script_node.domroot_executed_from() == self:
                    scripts.add(script_node)
            else:
                pass
        return list(scripts)
