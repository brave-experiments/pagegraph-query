from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge.abc.event_listener import EventListenerEdge


class EventListenerFiredEdge(EventListenerEdge):

    def as_event_listener_fired_edge(self) -> Optional[EventListenerFiredEdge]:
        return self
