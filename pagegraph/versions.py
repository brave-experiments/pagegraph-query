# This module tracks changes in graphs, depending on the version of those
# graphs. Basically, there are difficult ways of doing things in older
# versions of graphs, that newer versions make easier, and so this is
# there to capture that.

from enum import auto, Enum
from packaging.version import Version
import re
import sys
from typing import TYPE_CHECKING, Union

from packaging.version import parse, Version

from pagegraph import VERSION


class PageGraphFeature(Enum):
    EXECUTE_EDGES_HAVE_FRAME_ID = auto()


PG_0_6_3_FEATURES = (PageGraphFeature.EXECUTE_EDGES_HAVE_FRAME_ID,)
PG_FEATURE_VERSION_MAPPING: dict[tuple[PageGraphFeature], Version] = {
    PG_0_6_3_FEATURES: Version("0.6.3")
}


def min_version_for_feature(feature: PageGraphFeature) -> Version:
    for version_set, graph_version in PG_FEATURE_VERSION_MAPPING.items():
        if feature in version_set:
            return graph_version
    raise ValueError(f'PageGraphFeature "{feature}" not tied to any version')


def extract_pagegraph_version(input_path: str) -> Version:
    pattern = r"<version>(\d+\.\d+\.\d+)<\/version>"

    graph_version = None
    with open(input_path) as f:
        for line in f:
            match = re.search(pattern, line, re.ASCII)
            if match:
                graph_version = parse(match.group(1))
                break

    if not graph_version:
        raise Exception("Unable to determine version of PageGraph file")
    else:
        return graph_version


def check_pagegraph_version(input_path: str) -> Union[Version, None]:
    graph_version = extract_pagegraph_version(input_path)
    graph_major, graph_minor, _ = graph_version.release
    if graph_major != VERSION.major or graph_minor != VERSION.minor:
        print(f"Major and minor versions of this library ({VERSION}) and " +
              f"PageGraph files ({graph_version}) do not match. " +
              "Results may be incorrect.", file=sys.stderr)
        return None
    return graph_version
