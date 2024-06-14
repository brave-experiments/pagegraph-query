from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Set, Tuple, Type, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pagegraph.graph.edge import Edge, JSCallEdge, JSResultEdge
    from pagegraph.graph.edge import RequestCompleteEdge, RequestErrorEdge
    from pagegraph.graph.edge import RequestRedirectEdge
    from pagegraph.graph.node import Node, DOMRootNode, HTMLNode, ParserNode
    from pagegraph.graph.node import TextNode, FrameOwnerNode, ScriptNode


BlinkId = int
FrameId = int
RequestId = int
EdgeIterator = Iterable["Edge"]
NodeIterator = Iterable["Node"]
PageGraphId = str
PageGraphNodeId = PageGraphId
PageGraphEdgeId = PageGraphId
PageGraphEdgeKey = tuple[PageGraphNodeId, PageGraphNodeId, PageGraphEdgeId]
Url = str

DOMNode = Union["DOMRootNode", "HTMLNode", "TextNode", "FrameOwnerNode"]
AttrDOMNode = Union["DOMRootNode", "HTMLNode", "FrameOwnerNode"]
LeafDOMNode = Union["TextNode", "FrameOwnerNode"]
ParentDOMNode = Union["DOMRootNode", "HTMLNode", "FrameOwnerNode"]
ChildDOMNode = Union["HTMLNode", "TextNode", "FrameOwnerNode"]
RequesterNode = Union["HTMLNode", "DOMRootNode", "ScriptNode", "ParserNode"]
ActorNode = Union["ScriptNode", "ParserNode"]


# Values are defined by Blink, in `Resource::ResourceTypeToString`.
# See third_party/blink/renderer/platform/loader/fetch/resource.h.
# The OTHER catch all case covers the additional types
# defined in `blink::Resource::InitiatorTypeNameToString`.
class ResourceType(StrEnum):
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
    created_nodes: Set["Node"]
    attached_nodes: Set[ChildDOMNode]
    script_nodes: Set["ScriptNode"]

    def __init__(self) -> None:
        self.created_nodes = set()
        self.attached_nodes = set()
        self.script_nodes = set()

    def includes_created(self, node: "Node") -> bool:
        return node in self.created_nodes

    def includes_attached(self, node: ChildDOMNode) -> bool:
        return node in self.attached_nodes

    def includes_executed(self, node: "ScriptNode") -> bool:
        return node in self.script_nodes
