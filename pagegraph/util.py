import re
import sys
from urllib.parse import urlparse

from packaging.version import parse

from pagegraph.types import Url
from pagegraph import VERSION


def check_pagegraph_version(input_path: str) -> bool:
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
    graph_major, graph_minor, _ = graph_version.release
    if graph_major != VERSION.major or graph_minor != VERSION.minor:
        print(f"Major and minor versions of this library ({VERSION}) and " +
              f"PageGraph files ({graph_version}) do not match. " +
              "Results may be incorrect.", file=sys.stderr)
        return False
    return True


def is_url_local(url: Url, context_url: Url) -> bool:
    if url == "about:blank":
        return True
    url_parts = urlparse(url)
    context_url_parts = urlparse(context_url)
    if url_parts.netloc == "" or url_parts.netloc == context_url_parts.netloc:
        return True
    return False
