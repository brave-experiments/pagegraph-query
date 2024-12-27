from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Set, Optional, TYPE_CHECKING, Union


if TYPE_CHECKING:
    import networkx as NWX
    from packaging.version import Version

    from pagegraph.graph.edge import Edge
    from pagegraph.graph.edge.js_call import JSCallEdge
    from pagegraph.graph.edge.js_result import JSResultEdge
    from pagegraph.graph.edge.request_complete import RequestCompleteEdge
    from pagegraph.graph.edge.request_error import RequestErrorEdge
    from pagegraph.graph.edge.request_redirect import RequestRedirectEdge
    from pagegraph.graph.edge.request_start import RequestStartEdge
    from pagegraph.graph.node import Node
    from pagegraph.graph.node.abc.parent_dom_element import ParentDOMElementNode
    from pagegraph.graph.node.abc.script import ScriptNode
    from pagegraph.graph.node.dom_root import DOMRootNode
    from pagegraph.graph.node.frame_owner import FrameOwnerNode
    from pagegraph.graph.node.html import HTMLNode
    from pagegraph.graph.node.parser import ParserNode
    from pagegraph.graph.node.script_local import ScriptLocalNode
    from pagegraph.graph.node.script_remote import ScriptRemoteNode
    from pagegraph.graph.node.text import TextNode
    from pagegraph.graph.node.unknown import UnknownNode
    from pagegraph.serialize import DOMElementReport, FrameReport, JSONAble


NetworkXNodeId = str
NetworkXEdgeId = str
BlinkId = int
EventListenerId = int
FrameId = int
ScriptId = int
RequestId = int
PageGraphId = str
PageGraphNodeId = PageGraphId
PageGraphEdgeId = PageGraphId
PageGraphEdgeKey = tuple[PageGraphNodeId, PageGraphNodeId, PageGraphEdgeId]
Url = str
ElementSummary = Optional[dict[str, "JSONAble"]]

LeafDomNode = Union["TextNode", "FrameOwnerNode"]
ChildDomNode = Union["HTMLNode", "TextNode", "FrameOwnerNode"]
LocalOrRemoteScriptNode = Union["ScriptLocalNode", "ScriptRemoteNode"]
JSCallingNode = Union["ScriptLocalNode", "UnknownNode"]
ScriptExecutorNode = Union["ParentDOMElementNode", "ParserNode", "ScriptNode"]
RequesterNode = Union["HTMLNode", "DOMRootNode", "LocalOrRemoteScriptNode",
                      "ParserNode"]
ActorNode = Union["ScriptLocalNode", "ParserNode", "UnknownNode"]

RequestIncoming = Union["RequestStartEdge", "RequestRedirectEdge"]
RequestOutgoing = Union["RequestRedirectEdge", "RequestCompleteEdge",
                        "RequestErrorEdge"]

RequestHeaders = list[tuple[str, str]]

# Values are defined by Blink, in `Resource::ResourceTypeToString`.
# See third_party/blink/renderer/platform/loader/fetch/resource.h.
# The OTHER catch all case covers the additional types
# defined in `blink::Resource::InitiatorTypeNameToString`.
class ResourceType(Enum):
    ATTRIBUTION_RESOURCE = "Attribution resource"
    AUDIO = "Audio"
    CSS_RESOURCE = "CSS resource"
    CSS_RESOURCE_UA = "User Agent CSS resource"
    CSS_STYLESHEET = "CSS stylesheet"
    DICTIONARY = "Dictionary"
    DOCUMENT = "Document"
    FETCH = "Fetch"
    FONT = "Font"
    ICON = "Icon"
    IMAGE = "Image"
    INTERNAL_RESOURCE = "Internal resource"
    LINK_ELM_RESOURCE = "Link element resource"
    LINK_PREFETCH = "Link prefetch resource"
    MANIFEST = "Manifest"
    MOCK = "Mock"
    PROCESSING_INSTRUCTION = "Processing instruction"
    RAW = "Raw"
    REQUEST = "Request"
    SCRIPT = "Script"
    SPECULATION_RULE = "SpeculationRule"
    SVG = "SVG document"
    SVG_USE_ELM_RESOURCE = "SVG Use element resource"
    TEXT_TRACK = "Text track"
    TRACK = "Track"
    VIDEO = "Video"
    XML_HTTP_REQUEST = "XMLHttpRequest"
    XML_RESOURCE = "XML resource"
    XSL_STYLESHEET = "XSL stylesheet"
    OTHER = "Other"  # Fallback / catchall case


@dataclass
class FrameSummary:
    created_nodes: Set[Node]
    attached_nodes: Set[ChildDomNode]
    script_nodes: Set[ScriptLocalNode]

    def __init__(self) -> None:
        self.created_nodes = set()
        self.attached_nodes = set()
        self.script_nodes = set()

    def includes_created(self, node: Node) -> bool:
        return node in self.created_nodes

    def includes_attached(self, node: ChildDomNode) -> bool:
        return node in self.attached_nodes

    def includes_executed(self, node: ScriptLocalNode) -> bool:
        return node in self.script_nodes


@dataclass
class PageGraphInput:
    url: Url
    version: Version
    graph: NWX.MultiDiGraph
    reverse_graph: NWX.MultiDiGraph


class PartyFilterOption(StrEnum):
    NONE = "none"
    FIRST_PARTY = "first-party"
    THIRD_PARTY = "third-party"
