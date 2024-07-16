from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node import Node
from pagegraph.graph.node.abc.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport

if TYPE_CHECKING:
    from pagegraph.serialize import JSONAble


class HTMLNode(DOMElementNode, Reportable):

    def as_html_node(self) -> Optional["HTMLNode"]:
        return self

    def to_report(self) -> DOMElementReport:
        return DOMElementReport(self.pg_id(), self.tag_name(),
                                self.attributes())

    def tag_name(self) -> str:
        return self.data()[Node.RawAttrs.TAG.value]

    def attributes(self) -> dict[str, "JSONAble"]:
        summary: dict[str, "JSONAble"] = {}
        incoming_edges = list(self.incoming_edges())
        incoming_edges.sort(key=lambda x: x.id())
        for edge in incoming_edges:
            if set_attr_edge := edge.as_attribute_set_edge():
                summary[set_attr_edge.key()] = set_attr_edge.value()
            elif del_attr_edge := edge.as_attribute_delete_edge():
                try:
                    del summary[del_attr_edge.key()]
                except KeyError:
                    self.throw(
                        f"Found delete attr {del_attr_edge.key()} without "
                        "an existing attribute value.")
        return summary
