from dataclasses import dataclass
from typing import cast, Any, TYPE_CHECKING, Union

import pagegraph.graph
from pagegraph.types import PageGraphId
from pagegraph.serialize import FrameReport, RequestReport, ScriptReport
from pagegraph.serialize import DOMElementReport, JSStructureReport
from pagegraph.serialize import JSInvokeReport, Report, RequestChainReport
from pagegraph.serialize import NodeReport, EdgeReport
from pagegraph.versions import Feature


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
        domroot_for_iframe = iframe_node.domroot_node()
        if local_only and not domroot_for_iframe.is_top_level_domroot():
            continue

        parent_frame_report = domroot_for_iframe.to_report()
        iframe_elm_report = iframe_node.to_report()
        child_frame_reports: list[FrameReport] = []

        is_all_local_frames = True
        for child_domroot_node in iframe_node.domroot_nodes():
            if local_only and not child_domroot_node.is_local_domroot():
                is_all_local_frames = False
                break
            child_frame_reports.append(child_domroot_node.to_report())

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
        req_frame_nid = f"n{request_frame_id}"
        if frame_nid and req_frame_nid != frame_nid:
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
             method: str | None, pg_id: PageGraphId | None,
             debug: bool) -> list[JSCallsCommandReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    reports: list[JSCallsCommandReport] = []

    js_structure_nodes = pg.js_structure_nodes()
    for js_node in js_structure_nodes:
        if pg_id and js_node.pg_id() != pg_id:
            continue
        if method and method not in js_node.name():
            continue

        for call_result in js_node.call_results():
            if frame and call_result.call_context().pg_id() != frame:
                continue
            if cross_frame and not call_result.is_cross_frame_call():
                continue

            call_context = call_result.call_context()
            receiver_context = call_result.receiver_context()

            js_call_report = JSCallsCommandReport(
                js_node.to_report(), call_result.to_report(),
                call_context.to_report(), receiver_context.to_report())
            reports.append(js_call_report)
    return reports


@dataclass
class ScriptsCommandReport(Report):
    script: ScriptReport
    frame: FrameReport | None = None


def scripts(input_path: str, frame: str | None, pg_id: PageGraphId | None,
            include_source: bool, omit_executors: bool,
            debug: bool) -> list[ScriptsCommandReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    reports: list[ScriptsCommandReport] = []
    for script_node in pg.script_nodes():
        if pg_id and script_node.pg_id() != pg_id:
            continue

        script_report = script_node.to_report(include_source)
        report = ScriptsCommandReport(script_report)

        frame_id = script_node.execute_edge().frame_id()
        frame_report = pg.domroot_for_frame_id(frame_id).to_report()
        report.frame = frame_report

        if omit_executors:
            report.script.executor = None

        reports.append(report)
    return reports


def element_query(input_path: str, pg_id: PageGraphId, depth: int,
                  debug: bool) -> Union[NodeReport | EdgeReport]:
    pg = pagegraph.graph.from_path(input_path, debug)
    if pg_id.startswith("n"):
        return pg.node(pg_id).to_node_report(depth)
    elif pg_id.startswith("e"):
        return pg.edge(pg_id).to_edge_report(depth)
    else:
        raise ValueError("Invalid element id, should be either n## or e##.")


@dataclass
class EffectsCommandReport(Report):
    actor: Report
    action: Report


# The rules we follow for deciding which actions (edges) and elements (nodes)
# a node is responsible for are


def effects(input_path: str, pg_id: PageGraphId, loose: bool,
            debug: bool) -> list[EffectsCommandReport]:
    reports: list[EffectsCommandReport] = []
    return reports


@dataclass
class ValidationReport(Report):
    success: bool


def validate(input_path: str) -> ValidationReport:
    pagegraph.graph.from_path(input_path, True)
    return ValidationReport(True)
