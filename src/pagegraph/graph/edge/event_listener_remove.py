from __future__ import annotations

from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.event_listener import EventListenerEdge
from pagegraph.graph.edge.abc.frame_id_attributed import FrameIdAttributedEdge

if TYPE_CHECKING:
    from typing import Optional


class EventListenerRemoveEdge(EventListenerEdge, FrameIdAttributedEdge):

    def as_event_listener_remove_edge(self) -> Optional[EventListenerRemoveEdge]:
        return self
