from __future__ import annotations

from abc import ABC
from typing import Optional, TYPE_CHECKING

from pagegraph.graph.edge import Edge

if TYPE_CHECKING:
    from pagegraph.types import EventListenerId
    from pagegraph.graph.edge.event_listener_add import EventListenerAddEdge
    from pagegraph.graph.edge.event_listener_fired import EventListenerFiredEdge
    from pagegraph.graph.edge.event_listener_remove import EventListenerRemoveEdge


class EventListenerEdge(Edge, ABC):

    summary_methods = {
        "event_name": "event_name",
        "event_listener_id": "event_listener_id",
    }

    def as_event_listener_edge(self) -> Optional[EventListenerEdge]:
        return self

    def event_listener_id(self) -> EventListenerId:
        return int(self.data()[self.RawAttrs.EVENT_LISTENER_ID.value])

    def event_name(self) -> str:
        return self.data()[self.RawAttrs.KEY.value]

    def event_add_edges(self) -> list[EventListenerAddEdge]:
        listener_id = self.event_listener_id()
        return self.pg.event_listener_add_edges_for_id(listener_id)

    def event_fired_edges(self) -> list[EventListenerFiredEdge]:
        listener_id = self.event_listener_id()
        return self.pg.event_listener_fired_edges_for_id(listener_id)

    def event_removed_edges(self) -> list[EventListenerRemoveEdge]:
        listener_id = self.event_listener_id()
        return self.pg.event_listener_remove_edges_for_id(listener_id)
