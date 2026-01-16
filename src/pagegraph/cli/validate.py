from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pagegraph.types import PageGraphId, PageGraphNodeId


def is_node_id(node_id: PageGraphNodeId) -> bool:
    if node_id[0] != "n":
        raise ValueError(
            f"Node ids must start with a 'n': {node_id}")
    return True

def is_pg_id(pg_id: PageGraphId) -> bool:
    if pg_id[0] not in ["n", "e"]:
        raise ValueError(
            f"PageGraph element ids start with either 'n' or 'e': {pg_id}")
    return True
