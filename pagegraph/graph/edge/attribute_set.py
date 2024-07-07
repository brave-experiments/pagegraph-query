from typing import Optional

from pagegraph.graph.edge.attribute import AttributeEdge


class AttributeSetEdge(AttributeEdge):

    def as_attribute_set_edge(self) -> Optional["AttributeSetEdge"]:
        return self

    def value(self) -> str:
        return self.data()[self.RawAttrs.VALUE.value]
