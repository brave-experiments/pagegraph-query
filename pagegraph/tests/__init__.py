from abc import ABC
import unittest

import pagegraph.graph
import pagegraph.tests.util.paths as PG_PATHS


class PageGraphBaseTestClass(unittest.TestCase, ABC):
    NAME = ""

    def setUp(self) -> None:
        if self.NAME == "":
            raise ValueError("Inheritors must define NAME")
        graph_path = PG_PATHS.graphs() / (self.NAME + ".graphml")
        self.graph = pagegraph.graph.from_path(str(graph_path))
