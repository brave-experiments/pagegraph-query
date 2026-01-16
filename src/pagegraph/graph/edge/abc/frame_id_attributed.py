from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from pagegraph.graph.edge import Edge

if TYPE_CHECKING:
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.types import FrameId


class FrameIdAttributedEdge(Edge, ABC):

    summary_methods = {
        "frame id": "frame_id",
    }

    def domroot_for_frame_id(self) -> DOMRootNode:
        frame_id = self.frame_id()
        return self.pg.domroot_for_frame_id(frame_id)

    def frame_id(self) -> FrameId:
        if self.pg.debug:
            if self.RawAttrs.FRAME_ID.value not in self.data():
                self.throw("No frame id recorded")
        return int(self.data()[self.RawAttrs.FRAME_ID.value])
