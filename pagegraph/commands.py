from dataclasses import dataclass
from typing import cast, Any, Dict, List, TYPE_CHECKING

import pagegraph.graph
from pagegraph.serialize import FrameReport, RequestReport
from pagegraph.serialize import DOMElementReport, JSStructureReport
from pagegraph.serialize import JSInvokeReport, Report, RequestChainReport


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
    request: RequestChainReport
    frame: FrameReport


def requests(input_path: str, frame_nid: str | None,
             debug: bool) -> list[RequestsCommandReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    reports: list[RequestsCommandReport] = []

    for request_start_edge in pg.request_start_edges():
        request_frame_id = request_start_edge.frame_id()
        if frame_nid and request_frame_id != frame_nid:
            continue
        request_id = request_start_edge.request_id()
        request_chain = pg.request_chain_for_id(request_id)
        request_frame = pg.domroot_for_frame_id(request_frame_id)

        request_chain_report = request_chain.to_report()
        frame_report = request_frame.to_report()
        report = RequestsCommandReport(request_chain_report, frame_report)
        reports.append(report)
    return reports


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
