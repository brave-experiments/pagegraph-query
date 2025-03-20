# Tools for removing things Brave injects browser side from graphs,
# to make test results better match expectations.
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence

    from pagegraph.graph import PageGraph
    from pagegraph.graph.edge import Edge
    from pagegraph.graph.node import Node


ELM_PICKER_SCRIPT_NEEDLE = "./components/brave_extension/extension/brave_extension/content_element_picker.ts"
HAS_CACHED: bool = False
ARTIFACT_NODES: set[Node] = set()
ARTIFACT_EDGES: set[Edge] = set()


def build_caches(pg: PageGraph) -> None:
    global HAS_CACHED
    if HAS_CACHED:
        return
    script_nodes = pg.script_local_nodes()
    for node in script_nodes:
        if ELM_PICKER_SCRIPT_NEEDLE in node.source():
            ARTIFACT_NODES.add(node)
            for edge in node.incoming_edges():
                ARTIFACT_EDGES.add(edge)
    HAS_CACHED = True


def filter_artifact_nodes(pg: PageGraph, nodes: list[Node]) -> list[Node]:
    build_caches(pg)
    filtered_nodes = []
    for node in nodes:
        if node in ARTIFACT_NODES:
            continue
        filtered_nodes.append(node)
    return filtered_nodes


def filter_artifact_edges(pg: PageGraph, edges: list[Edge]) -> list[Edge]:
    build_caches(pg)
    filtered_edges = []
    for edge in edges:
        if edge in ARTIFACT_EDGES:
            continue
        filtered_edges.append(edge)
    return filtered_edges
