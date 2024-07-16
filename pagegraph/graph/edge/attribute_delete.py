from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge.abc.attribute import AttributeEdge


class AttributeDeleteEdge(AttributeEdge):

    def as_attribute_delete_edge(self) -> Optional[AttributeDeleteEdge]:
        return self
