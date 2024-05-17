from dataclasses import dataclass
from typing import cast, Any, Dict, List, TYPE_CHECKING

import pagegraph.graph
from pagegraph.graph.edge import Edge
from pagegraph.graph.serialize import FrameReport, RequestReport
from pagegraph.graph.serialize import DOMElementReport, JSStructureReport
from pagegraph.graph.serialize import JSInvokeReport, Report


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


@dataclass
class SubFramesCommandReport(Report):
    parent_frame: FrameReport
    iframe: DOMElementReport
    child_frames: list[FrameReport]


def subframes(input_path: str, local_only: bool,
              debug: bool) -> list[SubFramesCommandReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    report: list[SubFramesCommandReport] = []

    for iframe_node in pg.iframe_nodes():
        parent_frame = iframe_node.domroot()
        if parent_frame is None:
            iframe_node.throw("Couldn't find owner of iframe")
            continue

        if local_only and not parent_frame.is_top_level_frame():
            continue

        parent_frame_report = parent_frame.to_report()
        iframe_elm_report = iframe_node.to_report()
        child_frame_reports: list[FrameReport] = []

        is_all_local_frames = True
        for child_domroot in iframe_node.domroots():
            if local_only and not child_domroot.is_local_frame():
                is_all_local_frames = False
                break
            child_frame_reports.append(child_domroot.to_report())

        if len(child_frame_reports) == 0:
            continue

        if local_only and not is_all_local_frames:
            continue

        subframe_report = SubFramesCommandReport(
            parent_frame_report, iframe_elm_report, child_frame_reports)
        report.append(subframe_report)
    return report


@dataclass
class RequestsCommandReport(Report):
    request: RequestReport
    frame: FrameReport


def requests(input_path: str, frame_nid: str | None,
             debug: bool) -> list[RequestsCommandReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    report: list[RequestsCommandReport] = []

    for resource_node in pg.resource_nodes():
        for response_edge in resource_node.outgoing_edges():
            request_frame_id = response_edge.frame_id()
            requester_node = response_edge.incoming_node()
            if frame_nid and frame_nid != request_frame_id:
                continue
            request_frame = pg.domroot_for_frame_id(request_frame_id)

            request_report = response_edge.to_report()
            frame_report = request_frame.to_report()
            report.append(RequestsCommandReport(request_report, frame_report))
    return report


@dataclass
class JSCallsCommandReport(Report):
    method: JSStructureReport
    invocation: JSInvokeReport
    call_context: FrameReport
    receiver_context: FrameReport


def js_calls(input_path: str, frame: str | None, cross_frame: bool,
             method: str | None, debug: bool) -> list[JSCallsCommandReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    report: list[JSCallsCommandReport] = []

    js_structure_nodes = pg.js_structure_nodes()
    for js_node in js_structure_nodes:
        if method and method not in js_node.name():
            continue

        for call_result in js_node.call_results():
            if frame and call_result.call_context().id() != frame:
                continue
            if cross_frame and not call_result.is_cross_frame_call():
                continue

            call_context = call_result.call_context()
            receiver_context = call_result.receiver_context()

            js_call_report = JSCallsCommandReport(
                js_node.to_report(), call_result.to_report(),
                call_context.to_report(), receiver_context.to_report())
            report.append(js_call_report)
    return report
