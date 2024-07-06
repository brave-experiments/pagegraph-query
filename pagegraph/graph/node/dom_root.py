from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, FrameReport
from pagegraph.types import Url, FrameId
from pagegraph.util import is_url_local

if TYPE_CHECKING:
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.parser import ParserNode


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
        return self.data()[self.RawAttrs.TAG.value]

    def parser(self) -> "ParserNode":
        parser_node = None
        for node in self.parent_nodes():
            if parser_node := node.as_parser_node():
                break
        assert parser_node
        return parser_node
