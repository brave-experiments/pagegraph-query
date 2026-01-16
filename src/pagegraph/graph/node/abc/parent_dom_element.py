from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.node.abc.dom_element import DOMElementNode

if TYPE_CHECKING:
    from typing import Optional

    from pagegraph.serialize import JSONAble


class ParentDOMElementNode(DOMElementNode, ABC):

    def validate(self) -> None:
        summary: dict[str, JSONAble] = {}
        incoming_edges = list(self.incoming_edges())
        incoming_edges.sort(key=lambda x: x.id())
        for edge in incoming_edges:
            if set_attr_edge := edge.as_attribute_set_edge():
                summary[set_attr_edge.key()] = set_attr_edge.value()
                continue
            if del_attr_edge := edge.as_attribute_delete_edge():
                try:
                    del summary[del_attr_edge.key()]
                except KeyError:
                    self.throw(
                        f"Found delete attr {del_attr_edge.key()} without "
                        "an existing attribute value.")
        super().validate()

    def as_parent_dom_element_node(self) -> Optional[ParentDOMElementNode]:
        return self

    def tag_name(self) -> str:
        return self.data()[self.RawAttrs.TAG.value]

    def attributes(self) -> dict[str, JSONAble]:
        summary: dict[str, JSONAble] = {}
        incoming_edges = list(self.incoming_edges())
        incoming_edges.sort(key=lambda x: x.id())
        for edge in incoming_edges:
            if set_attr_edge := edge.as_attribute_set_edge():
                summary[set_attr_edge.key()] = set_attr_edge.value()
                continue
            if del_attr_edge := edge.as_attribute_delete_edge():
                try:
                    del summary[del_attr_edge.key()]
                except KeyError:
                    # This is an unexpected situation, where we see an
                    # attribute being deleted in the graph that we
                    # don't have a record of ever being completed. Here
                    # we ignore this oddity, but in the validate() method
                    # we throw.
                    pass
        return summary

    def attributes_ever(self) -> dict[str, list[JSONAble]]:
        summary: dict[str, list[JSONAble]] = {}
        incoming_edges = list(self.incoming_edges())
        incoming_edges.sort(key=lambda x: x.id())
        for edge in incoming_edges:
            if set_attr_edge := edge.as_attribute_set_edge():
                attr_key = set_attr_edge.key()
                attr_value = set_attr_edge.value()
                if attr_key in summary:
                    summary[attr_key].append(attr_value)
                else:
                    summary[attr_key] = [attr_value]
                continue
        return summary

    def get_attribute(self, attr_name: str) -> Optional[JSONAble]:
        return self.attributes().get(attr_name)

    def get_attribute_ever(self, attr_name: str) -> Optional[list[JSONAble]]:
        return self.attributes_ever().get(attr_name)
