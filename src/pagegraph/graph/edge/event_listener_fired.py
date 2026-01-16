from __future__ import annotations

from typing import TYPE_CHECKING

from pagegraph.graph.edge.abc.event_listener import EventListenerEdge

if TYPE_CHECKING:
    from typing import Optional

class EventListenerFiredEdge(EventListenerEdge):

    def as_event_listener_fired_edge(self) -> Optional[EventListenerFiredEdge]:
        return self
