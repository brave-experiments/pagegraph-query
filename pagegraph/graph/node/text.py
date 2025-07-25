from __future__ import annotations

from base64 import b64encode
import hashlib
from typing import Optional, TYPE_CHECKING

from pagegraph.graph.node.abc.dom_element import DOMElementNode
from pagegraph.serialize import Reportable, DOMElementReport

if TYPE_CHECKING:
    from pagegraph.serialize import JSONAble


class TextNode(DOMElementNode, Reportable):

    def as_text_node(self) -> Optional[TextNode]:
        return self

    def to_report(self) -> DOMElementReport:
        attrs: dict[str, JSONAble] = {"text": self.text()}
        return DOMElementReport(self.pg_id(), self.tag_name(), attrs)

    def tag_name(self) -> str:
        return "[text]"

    def text(self) -> str:
        return self.data()[self.__class__.RawAttrs.TEXT.value]

    def hash(self) -> str:
        hasher = hashlib.new("sha256")
        hasher.update(self.text().encode("utf8"))
        return b64encode(hasher.digest()).decode("utf8")
