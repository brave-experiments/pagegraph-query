from __future__ import annotations

from abc import ABC
from typing import Optional

from pagegraph.graph.edge import Edge


class EffectEdge(Edge, ABC):

    def as_effect_edge(self) -> Optional[EffectEdge]:
        return self
