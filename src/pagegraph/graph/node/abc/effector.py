from __future__ import annotations

from abc import ABC
from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node import Node

if TYPE_CHECKING:
    from pagegraph.graph.edge.abc.effect import EffectEdge


class EffectorNode(Node, ABC):

    def as_effector_node(self) -> Optional[EffectorNode]:
        return self

    def effects_narrow(self) -> list[EffectEdge]:
        raise NotImplementedError()

    def effects_broad(self) -> list[EffectEdge]:
        raise NotImplementedError()
