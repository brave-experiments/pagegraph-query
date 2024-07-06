from typing import Optional

from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge


class EventListenerRemoveEdge(FrameIdAttributedEdge):
    def as_event_listener_remove_edge(self) -> Optional[
            "EventListenerRemoveEdge"]:
        return self
