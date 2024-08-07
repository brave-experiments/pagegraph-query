# This module tracks changes in graphs, depending on the version of those
# graphs. Basically, there are difficult ways of doing things in older
# versions of graphs, that newer versions make easier, and so this is
# there to capture that.

from enum import auto, Enum
from pathlib import Path
import re
import sys

from packaging.version import parse, Version


MIN_GRAPH_VERSION = Version("0.7.0")
GRAPH_VERSION_0_7_0 = Version("0.7.0")


class Feature(Enum):
    CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS = auto()
    DOCUMENT_EDGES = auto()


PG_FEATURE_VERSION_MAPPING: dict[Feature, Version] = {
    Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS: GRAPH_VERSION_0_7_0,
    Feature.DOCUMENT_EDGES: GRAPH_VERSION_0_7_0,
}


def min_version_for_feature(feature: Feature) -> Version:
    try:
        return PG_FEATURE_VERSION_MAPPING[feature]
    except KeyError as exc:
        msg = f"Feature '{feature}' not tied to any version"
        raise ValueError(msg) from exc


def extract_pagegraph_version(input_path: Path) -> Version:
    pattern = r"<version>(\d+\.\d+\.\d+)<\/version>"

    graph_version = None
    with input_path.open(encoding="utf8") as f:
        for line in f:
            match = re.search(pattern, line, re.ASCII)
            if match:
                graph_version = parse(match.group(1))
                break

    if not graph_version:
        raise ValueError("Unable to determine version of PageGraph file")
    return graph_version


def check_pagegraph_version(input_path: Path) -> Version:
    graph_version = extract_pagegraph_version(input_path)
    graph_major, graph_minor, _ = graph_version.release
    min_major, min_minor, _ = MIN_GRAPH_VERSION.release
    if (graph_major < min_major or
            min_major == graph_major and graph_minor < min_minor):
        print("This pagegraph file version is not supported. "
              f"Detected {graph_version}, min supported version is "
              f"{MIN_GRAPH_VERSION}", file=sys.stderr)
    return graph_version
