from typing import Optional

from pagegraph.graph.node.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport


class TextNode(DOMElementNode, Reportable):

    def as_text_node(self) -> Optional["TextNode"]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name())

    def tag_name(self) -> str:
        return "[text]"
