from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from pagegraph.types import ActorNode


class NodeCreateEdge(FrameIdAttributedEdge):

    incoming_node_type_names = [
        "parser",  # Node.Types.PARSER
        "script",  # Node.Types.SCRIPT
    ]

    outgoing_node_type_names = [
        "DOM root",  # Node.Types.DOM_ROOT
        "frame owner",  # Node.Types.FRAME_OWNER
        "HTML element",  # Node.Types.HTML_NODE
        "text node",  # Node.Types.TEXT_NODE
    ]

    def incoming_node(self) -> "ActorNode":
        incoming_node = super().incoming_node()
        actor_node = incoming_node.as_actor_node()
        assert actor_node
        return actor_node

    def as_create_edge(self) -> Optional["NodeCreateEdge"]:
        return self

    def validate(self) -> bool:
        # The only times we should see a 0-reported frame id are for
        # frames that are created automatically by blink (e.g.,
        # when a frame is being set up for the to level frame, or
        # when an iframe is being created by a script, before its
        # been populated or loaded).
        frame_id = self.frame_id()
        outgoing_node = self.outgoing_node()
        if frame_id == 0 and outgoing_node.as_domroot_node() is None:
            return False
        return True
