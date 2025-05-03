from __future__ import annotations

from typing import Optional, Union, TYPE_CHECKING

from pagegraph.graph.edge import Edge
from pagegraph.versions import Feature

if TYPE_CHECKING:
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.parser import ParserNode


class CrossDOMEdge(Edge):

    incoming_node_type_names = [
        "frame owner",  # Node.Types.FRAME_OWNER
    ]

    # Note that the correct values for edges differs depending on
    # graph version.
    outgoing_node_type_names = None

    def validate(self) -> None:
        if self.__class__.outgoing_node_type_names is not None:
            return super().validate()

        if self.pg.feature_check(
                Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS):
            self.__class__.outgoing_node_type_names = ["DOM root"]
        else:
            self.__class__.outgoing_node_type_names = ["parser"]
        return super().validate()

    def as_cross_dom_edge(self) -> Optional[CrossDOMEdge]:
        return self

    def incoming_node(self) -> FrameOwnerNode:
        incoming_node = super().incoming_node().as_frame_owner_node()
        assert incoming_node
        return incoming_node

    def outgoing_node(self) -> Union[DOMRootNode, ParserNode]:
        # Note that even though we can be sure which of these the outgoing
        # node will be, it'll differ across graph versions, so we
        # have to be ambagious for now.
        outgoing_node = super().outgoing_node()
        return_node = (
            outgoing_node.as_domroot_node() or
            outgoing_node.as_parser_node()
        )
        assert return_node
        return return_node
