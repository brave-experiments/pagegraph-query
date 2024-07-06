from typing import Optional

from pagegraph.graph.edge.frame_id_attributed import FrameIdAttributedEdge


class EventListenerAddEdge(FrameIdAttributedEdge):
    def as_event_listener_add_edge(self) -> Optional["EventListenerAddEdge"]:
        return self
