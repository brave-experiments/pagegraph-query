from typing import cast, Any, Dict, List, TYPE_CHECKING

import pagegraph.graph


if TYPE_CHECKING:
    from pagegraph.graph.node import DOMRootNode, FrameOwnerNode
    from pagegraph.graph.edge import RequestCompleteEdge, RequestErrorEdge


def _frametree_from_frame_owner(node: "FrameOwnerNode") -> List[Dict[Any, Any]]:
    rs = [_frametree_from_domroot(domroot) for domroot in node.domroots()]
    return rs


def _frametree_from_domroot(node: "DOMRootNode") -> Dict[Any, Any]:
    children: List[Dict[Any, Any]] = []
    summary = {
        "url": node.url(),
        "nid": node.id(),
        "children": children
    }

    for frame_owner in node.frame_owner_nodes():
        children += _frametree_from_frame_owner(frame_owner)
    return summary


def frametree(input_path: str) -> List[Dict[Any, Any]]:
    pg = pagegraph.graph.from_path(input_path)
    toplevel_domroot_nodes = pg.toplevel_domroot_nodes()

    trees = []
    for domroot_node in toplevel_domroot_nodes:
        trees.append(_frametree_from_domroot(domroot_node))
    return trees


def subframes(input_path: str, local_only: bool = False) -> Any:
    pg = pagegraph.graph.from_path(input_path)
    summaries = []

    for iframe_node in pg.iframe_nodes():
        iframe_summary: Dict[str, Any] = {}
        parent_frame = iframe_node.domroot()
        if parent_frame is None:
            iframe_node.throw("Couldn't find owner of iframe")
            return
        parent_frame_url = parent_frame.url()
        parent_frame_nid = parent_frame.id()
        iframe_summary["parent frame"] = {
            "url": parent_frame_url,
            "nid": parent_frame_nid
        }
        iframe_summary["iframe"] = {
            "nid": iframe_node.id()
        }

        child_documents = []
        for domroot_node in iframe_node.domroots():
            child_documents.append({
                "nid": domroot_node.id(),
                "url": domroot_node.url()
            })
        iframe_summary["child documents"] = child_documents
        summaries.append(iframe_summary)
    return summaries


def requests(input_path: str, frame_nid: str | None = None) -> Any:
    pg = pagegraph.graph.from_path(input_path)
    requests = []

    for resource_node in pg.resource_nodes():
        for response_edge in resource_node.outgoing_edges():
            request_frame_id = response_edge.frame_id()
            requester_node = response_edge.incoming_node()
            if frame_nid and frame_nid != request_frame_id:
                continue
            request_frame = pg.domroot_for_frame_id(request_frame_id)

            request_data: Dict[str, str | int] = {
                "nid": resource_node.id(),
                "url": resource_node.url(),
            }
            if response_edge.is_request_complete_edge():
                request_complete_edge = cast("RequestCompleteEdge", response_edge)
                request_data["type"] = "complete"
                request_data["hash"] = request_complete_edge.hash()
                request_data["size"] = request_complete_edge.size()
                request_data["headers"] = request_complete_edge.headers()
            else:
                request_data["type"] = "error"

            requests.append({
                "request": request_data,
                "frame": {
                    "blink_id": request_frame.blink_id(),
                    "nid": request_frame.id(),
                    "url": request_frame.url(),
                }
            })
    return requests
