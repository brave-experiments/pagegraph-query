from dataclasses import dataclass
from typing import Iterable, Set, Tuple, Type, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pagegraph.graph.edge import Edge, JSCallEdge, JSResultEdge
    from pagegraph.graph.edge import RequestCompleteEdge, RequestErrorEdge
    from pagegraph.graph.edge import RequestRedirectEdge
    from pagegraph.graph.node import Node, DOMRootNode, HTMLNode, ParserNode
    from pagegraph.graph.node import TextNode, FrameOwnerNode, ScriptNode


BlinkId = str
FrameId = str
RequestId = int
EdgeIterator = Iterable["Edge"]
NodeIterator = Iterable["Node"]
PageGraphId = str
PageGraphNodeId = PageGraphId
PageGraphEdgeId = PageGraphId
PageGraphEdgeKey = tuple[PageGraphNodeId, PageGraphNodeId, PageGraphEdgeId]
Url = str

DOMNode = Union["DOMRootNode", "HTMLNode", "TextNode", "FrameOwnerNode"]
ParentNode = Union["DOMRootNode", "HTMLNode", "FrameOwnerNode"]
ChildNode = Union["HTMLNode", "TextNode", "FrameOwnerNode"]
RequesterNode = Union["HTMLNode", "DOMRootNode", "ScriptNode", "ParserNode"]


@dataclass
class FrameSummary:
    created_nodes: Set["Node"]
    attached_nodes: Set[ChildNode]
    script_nodes: Set["ScriptNode"]

    def __init__(self) -> None:
        self.created_nodes = set()
        self.attached_nodes = set()
        self.script_nodes = set()

    def includes_created(self, node: "Node") -> bool:
        return node in self.created_nodes

    def includes_attached(self, node: ChildNode) -> bool:
        return node in self.attached_nodes

    def includes_executed(self, node: "ScriptNode") -> bool:
        return node in self.script_nodes
