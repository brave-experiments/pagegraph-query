from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING
import unittest

import pagegraph.graph
import pagegraph.tests.util.filter as PG_FILTER
import pagegraph.tests.util.paths as PG_PATHS

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import Edge
    from pagegraph.graph.node import Node


class PageGraphBaseTestClass(unittest.TestCase, ABC):
    NAME = ""
    graph: "PageGraph"

    def filter_nodes(self, nodes: list[Node]) -> list[Node]:
        return PG_FILTER.filter_artifact_nodes(self.graph, nodes)

    def filter_edges(self, edges: list[Edge]) -> list[Edge]:
        return PG_FILTER.filter_artifact_edges(self.graph, edges)

    def setUp(self) -> None:
        if self.NAME == "":
            raise ValueError("Inheritors must define NAME")
        graph_path = PG_PATHS.graphs() / (self.NAME + ".graphml")
        self.graph = pagegraph.graph.from_path(graph_path, True)
