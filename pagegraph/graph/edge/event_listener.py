from __future__ import annotations

from typing import Optional

from pagegraph.graph.edge import Edge


class EventListenerEdge(Edge):
    def as_event_listener_edge(self) -> Optional[EventListenerEdge]:
        return self
