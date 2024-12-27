from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node import Node
from pagegraph.graph.node.dom_root import DOMRootNode

if TYPE_CHECKING:
    from pagegraph.graph.node.frame_owner import FrameOwnerNode


class ParserNode(Node):

    incoming_node_types = [
        Node.Types.FRAME_OWNER,
        # The RESOURCE case is uncommon, but occurs when something is
        # fetched that doesn't have a representation in the graph,
        # most commonly a pre* <meta> instruction.
        Node.Types.RESOURCE
    ]

    def as_parser_node(self) -> Optional[ParserNode]:
        return self

    def frame_owner_node(self) -> Optional[FrameOwnerNode]:
        parent_nodes_list = list(self.parent_nodes())
        frame_owner_nodes: list[FrameOwnerNode] = []
        for parent_node in parent_nodes_list:
            if frame_owner_node := parent_node.as_frame_owner_node():
                frame_owner_nodes.append(frame_owner_node)
        if self.pg.debug:
            if len(frame_owner_nodes) != 1:
                self.throw("Did not find exactly 1 parent frame owner node")
        return frame_owner_nodes[0]

    def created_nodes(self) -> list[Node]:
        created_nodes = []
        for edge in self.outgoing_edges():
            if create_edge := edge.as_create_edge():
                created_nodes.append(create_edge.outgoing_node())
        return created_nodes

    def domroots(self) -> list[DOMRootNode]:
        domroots = []
        already_returned = set()
        for e in self.outgoing_edges():
            if (e.as_create_edge() is None and e.as_structure_edge() is None):
                continue
            child_node = e.outgoing_node()
            if child_node in already_returned:
                continue
            if domroot_node := child_node.as_domroot_node():
                already_returned.add(domroot_node)
                domroots.append(domroot_node)
        return domroots
