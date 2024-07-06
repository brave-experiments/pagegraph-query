from typing import Optional

from pagegraph.graph.edge.attribute import AttributeEdge


class AttributeDeleteEdge(AttributeEdge):

    def as_attribute_delete_edge(self) -> Optional["AttributeDeleteEdge"]:
        return self
