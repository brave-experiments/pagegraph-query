"""Functions for loading and that operate on graphml files, before they're
processed and loaded as proper PageGraph recordings."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING

import networkx
from packaging.version import parse

from pagegraph.graph.node import Node
from pagegraph.graph.node import url_from_network_node_data
from pagegraph.graph.node import node_type_from_networkx_node_data
from pagegraph.types import PageGraphInput

if TYPE_CHECKING:
    from typing import Optional

    from networkx import MultiDiGraph
    from packaging.version import Version

    from pagegraph.types import Url


def url_from_graphml_file(input_path: Path) -> Url:
    xml_url_pattern = r'<desc>.*?<url>(.*?)</url>.*?</desc>'
    xml_url_matcher = re.compile(xml_url_pattern, flags=re.U)

    xml_empty_url_pattern = r'<desc>.*?<url/>.*?</desc>'
    xml_empty_url_matcher = re.compile(xml_empty_url_pattern, flags=re.U)

    with input_path.open() as f:
        for line in f:
            if with_url_match := xml_url_matcher.search(line):
                return with_url_match.group(1)
            # If we couldn't find a proper URL in the PageGraph file,
            # see if we instead have a closed <url/> tag, which would indicate
            # that the graph was recorded correctly, but the top level frame's
            # URL was empty (this shouldn't happen, but may be present in
            # v0.7.x versions of PageGraph files).
            if xml_empty_url_matcher.search(line) is not None:
                return ""
    raise ValueError("Could not find <url>...</url> in graph file")


def pagegraph_version_from_graphml_file(input_path: Path) -> Version:
    pattern = r"<version>(\d+\.\d+\.\d+)<\/version>"

    graph_version = None
    with input_path.open(encoding="utf8") as f:
        for line in f:
            match = re.search(pattern, line, re.ASCII)
            if match:
                graph_version = parse(match.group(1))
                break

    if not graph_version:
        raise ValueError("Unable to determine version of PageGraph file at.")
    return graph_version


def remove_intermediate_subgraphs(graph: MultiDiGraph) -> MultiDiGraph:
    empty_domroot_node_ids: set[int] = set()
    for node_id, node_data in graph.nodes.items():
        node_type = node_type_from_networkx_node_data(node_data)
        if node_type != Node.Types.DOM_ROOT:
            continue
        domroot_url = url_from_network_node_data(node_data)
        if domroot_url:
            continue
        empty_domroot_node_ids.add(node_id)

    components = list(networkx.weakly_connected_components(graph))

    node_ids_to_remove: set[int] = set()
    for component in components:
        node_ids_in_component = set(component)
        intersection = node_ids_in_component & empty_domroot_node_ids
        if len(intersection) == 0:
            continue
        if len(node_ids_in_component & node_ids_to_remove) != 0:
            raise ValueError("Found overlapping nodes in subgraphs with empty "
                            "domroot urls")
        node_ids_to_remove |= node_ids_in_component

    new_graph = graph.copy()
    for node_id in node_ids_to_remove:
        edges = graph.edges(node_id)
        new_graph.remove_edges_from(edges)
        new_graph.remove_node(node_id)
    return new_graph


def load_from_path(input_path: Path) -> PageGraphInput:
    """Loads a networkx instance from a graphml file.

    This indirection step exists as a chance to do preprocess and modify
    networkx instances before they're consumed by the PageGraph class."""

    try:
        version = pagegraph_version_from_graphml_file(input_path)
        url = url_from_graphml_file(input_path)
        graph = networkx.read_graphml(input_path)
        # processed_graph = remove_intermediate_subgraphs(graph)
        reverse_graph = networkx.reverse_view(graph)
        return PageGraphInput(url, version, graph, reverse_graph)
    except ValueError as exc:
        raise ValueError(
            f"Unable to parse PageGraph file at {input_path}") from exc
