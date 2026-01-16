from __future__ import annotations

from typing import Optional

from pagegraph.graph.node.abc.script import ScriptNode


class ScriptRemoteNode(ScriptNode):

    def as_script_remote_node(self) -> Optional[ScriptRemoteNode]:
        return self
