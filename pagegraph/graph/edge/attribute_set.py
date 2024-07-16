from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge.abc.attribute import AttributeEdge


class AttributeSetEdge(AttributeEdge):

    summary_methods = {
        "value": "value",
    }

    def as_attribute_set_edge(self) -> Optional[AttributeSetEdge]:
        return self

    def value(self) -> str:
        return self.data()[self.RawAttrs.VALUE.value]
