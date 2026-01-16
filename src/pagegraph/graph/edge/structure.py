from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge
from pagegraph.versions import Feature


class StructureEdge(Edge):

    # Note that the correct values for edges differs depending on
    # graph version.
    incoming_node_type_names = None

    def validate(self) -> None:
        if self.__class__.incoming_node_type_names:
            return super().validate()

        if self.pg.feature_check(Feature.DOCUMENT_EDGES):
            self.__class__.incoming_node_type_names = ["parser"]
            self.__class__.outgoing_node_type_names = [
                "extensions",  # Node.Types.EXTENSIONS
                "DOM root",  # Node.Types.DOM_ROOT
            ]
        else:
            self.__class__.incoming_node_type_names = [
                "DOM root",  # Node.Types.DOM_ROOT
                "frame owner",  # Node.Types.FRAME_OWNER
                "HTML element",  # Node.Types.HTML
                "parser",  # Node.Types.PARSER
            ]
        return super().validate()

    def as_structure_edge(self) -> Optional[StructureEdge]:
        return self
