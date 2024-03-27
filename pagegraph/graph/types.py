from typing import Iterable, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pagegraph.graph.edge import Edge
    from pagegraph.graph.node import Node, DOMRootNode, HTMLNode
    from pagegraph.graph.node import TextNode, FrameOwnerNode


BlinkId = str
EdgeIterator = Iterable["Edge"]
NodeIterator = Iterable["Node"]
PageGraphId = str
PageGraphNodeId = PageGraphId
PageGraphEdgeId = PageGraphId
PageGraphEdgeKey = tuple[PageGraphNodeId, PageGraphNodeId, PageGraphEdgeId]
Url = str

ParentNode = Type["DOMRootNode"] | Type["HTMLNode"]
ChildNode = Type["HTMLNode"] | Type["TextNode"] | Type["FrameOwnerNode"]