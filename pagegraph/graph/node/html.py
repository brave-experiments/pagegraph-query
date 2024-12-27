from __future__ import annotations

from typing import Optional

from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport


class HTMLNode(ParentDOMElementNode, Reportable):

    def as_html_node(self) -> Optional[HTMLNode]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name(),
                                self.attributes())
