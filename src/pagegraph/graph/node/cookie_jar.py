from __future__ import annotations

from typing import TYPE_CHECKING

from pagegraph.graph.node.storage_area import StorageAreaNode

if TYPE_CHECKING:
    from typing import Optional


class CookieJarNode(StorageAreaNode):

    def as_cookie_jar_node(self) -> Optional[CookieJarNode]:
        return self
