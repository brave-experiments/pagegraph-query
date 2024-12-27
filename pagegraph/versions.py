"""This module tracks changes in graphs, depending on the version of those
graphs. Basically, there are difficult ways of doing things in older
versions of graphs, that newer versions make easier, and so this is
there to capture that."""

from enum import auto, Enum

from packaging.version import Version


MIN_GRAPH_VERSION = Version("0.7.0")
GRAPH_VERSION_0_7_0 = Version("0.7.0")
GRAPH_VERSION_0_7_2 = Version("0.7.2")


class Feature(Enum):
    CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS = auto()
    DOCUMENT_EDGES = auto()


PG_FEATURE_MIN_VERSION_MAPPING: dict[Feature, Version] = {
    Feature.CROSS_DOM_EDGES_POINT_TO_DOM_ROOTS: GRAPH_VERSION_0_7_0,
    Feature.DOCUMENT_EDGES: GRAPH_VERSION_0_7_0,
}


def min_version_for_feature(feature: Feature) -> Version:
    try:
        return PG_FEATURE_MIN_VERSION_MAPPING[feature]
    except KeyError as exc:
        msg = f"Feature '{feature}' not tied to any version"
        raise ValueError(msg) from exc
