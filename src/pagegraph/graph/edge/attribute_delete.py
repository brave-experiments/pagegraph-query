from __future__ import annotations

from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.attribute import AttributeEdge

if TYPE_CHECKING:
    from typing import Optional


class AttributeDeleteEdge(AttributeEdge):

    def as_attribute_delete_edge(self) -> Optional[AttributeDeleteEdge]:
        return self
