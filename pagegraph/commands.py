from typing import cast, Any, Dict, List, TYPE_CHECKING

import pagegraph.graph


if TYPE_CHECKING:
    from pagegraph.graph.node import DOMRootNode, FrameOwnerNode
    from pagegraph.graph.edge import RequestCompleteEdge, RequestErrorEdge


def _tree_from_frame_owner(node: "FrameOwnerNode") -> List[Dict[Any, Any]]:
    rs = [_tree_from_domroot(domroot) for domroot in node.domroots()]
    return rs


def _tree_from_domroot(node: "DOMRootNode") -> Dict[Any, Any]:
    children: List[Dict[Any, Any]] = []
    summary = {
        "url": node.url(),
        "nid": node.id(),
        "children": children
    }

    for frame_owner in node.frame_owner_nodes():
        children += _tree_from_frame_owner(frame_owner)
    return summary


def frametree(input_path: str, debug: bool = False) -> List[Dict[Any, Any]]:
    pg = pagegraph.graph.from_path(input_path, debug)
    toplevel_domroot_nodes = pg.toplevel_domroot_nodes()

    trees = []
    for domroot_node in toplevel_domroot_nodes:
        trees.append(_tree_from_domroot(domroot_node))
    return trees


def subframes(input_path: str, local_only: bool = False,
              debug: bool = False) -> Any:
    pg = pagegraph.graph.from_path(input_path, debug)
    summaries = []

    for iframe_node in pg.iframe_nodes():
        parent_frame = iframe_node.domroot()
        if parent_frame is None:
            iframe_node.throw("Couldn't find owner of iframe")
            return

        if local_only and not parent_frame.is_top_level_frame():
            continue

        parent_frame_url = parent_frame.url()
        parent_frame_nid = parent_frame.id()

        child_documents = []
        is_all_local_frames = True
        for child_domroot in iframe_node.domroots():
            if local_only and not child_domroot.is_local_frame():
                is_all_local_frames = False
                break
            child_documents.append({
                "nid": child_domroot.id(),
                "url": child_domroot.url()
            })

        if len(child_documents) == 0:
            continue

        if local_only and not is_all_local_frames:
            continue

        iframe_summary: Dict[str, Any] = {
            "parent frame": {
                "url": parent_frame_url,
                "nid": parent_frame_nid
            },
            "iframe": {
                "nid": iframe_node.id()
            },
            "child frames": child_documents
        }
        summaries.append(iframe_summary)
    return summaries


def requests(input_path: str, frame_nid: str | None = None,
             debug: bool = False) -> Any:
    pg = pagegraph.graph.from_path(input_path, debug)
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
                request_complete_edge = cast(
                        "RequestCompleteEdge", response_edge)
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
