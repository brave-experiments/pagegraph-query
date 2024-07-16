from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Optional, TYPE_CHECKING

import pagegraph.graph
from pagegraph.types import PageGraphId
from pagegraph.serialize import Report, to_command_report

if TYPE_CHECKING:
    from pagegraph.serialize import FrameReport, ScriptReport, BasicReport
    from pagegraph.serialize import DOMElementReport, JSStructureReport
    from pagegraph.serialize import JSCallResultReport, RequestChainReport
    from pagegraph.serialize import NodeReport, EdgeReport, DOMNodeReport
    from pagegraph.serialize import CommandReport
    from pathlib import Path


@dataclass
class SubFramesCommandReport(Report):
    parent_frame: FrameReport
    iframe: DOMElementReport
    child_frames: list[FrameReport]


def subframes(input_path: Path, local_only: bool,
              debug: bool) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, debug)
    report: list[SubFramesCommandReport] = []

    for iframe_node in pg.iframe_nodes():
        domroot_for_iframe = iframe_node.domroot_node()
        if local_only and not domroot_for_iframe.is_top_level_domroot():
            continue

        parent_frame_report = domroot_for_iframe.to_report()
        iframe_elm_report = iframe_node.to_report()
        child_frame_reports: list["FrameReport"] = []

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
    return to_command_report(pg, report)


@dataclass
class RequestsCommandReport(Report):
    request: RequestChainReport
    frame: FrameReport


def requests(input_path: Path, frame_nid: Optional[PageGraphId],
             debug: bool) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, debug)
    reports: list[RequestsCommandReport] = []

    for request_start_edge in pg.request_start_edges():
        request_frame_id = request_start_edge.frame_id()
        request_frame = pg.domroot_for_frame_id(request_frame_id)

        if frame_nid and request_frame.pg_id() != frame_nid:
            continue
        request_id = request_start_edge.request_id()
        request_chain = pg.request_chain_for_id(request_id)

        request_chain_report = request_chain.to_report()
        frame_report = request_frame.to_report()
        report = RequestsCommandReport(request_chain_report, frame_report)
        reports.append(report)
    return to_command_report(pg, reports)


@dataclass
class JSCallsCommandReport(Report):
    caller: Union[ScriptReport, BasicReport]
    call: JSCallResultReport


def js_calls(input_path: Path, frame: Optional[PageGraphId],
             cross_frame: bool, method: Optional[str],
             pg_id: Optional[PageGraphId], debug: bool) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, debug)
    reports: list[JSCallsCommandReport] = []

    js_structure_nodes = pg.js_structure_nodes()
    for js_node in js_structure_nodes:
        if method and method not in js_node.name():
            continue

        for call_result in js_node.call_results():
            if frame and call_result.call_context().pg_id() != frame:
                continue
            if cross_frame and not call_result.is_cross_frame_call():
                continue
            script_node =call_result.call.incoming_node()
            if pg_id and script_node.pg_id() != pg_id:
                continue
            call_report = call_result.to_report()
            script_report = script_node.to_report()
            reports.append(JSCallsCommandReport(script_report, call_report))
    return to_command_report(pg, reports)


@dataclass
class ScriptsCommandReport(Report):
    script: ScriptReport
    frame: Optional[FrameReport] = None


def scripts(input_path: Path, frame: Optional[PageGraphId],
            pg_id: Optional[PageGraphId], include_source: bool,
            omit_executors: bool, debug: bool) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, debug)
    reports: list[ScriptsCommandReport] = []
    for script_node in pg.script_local_nodes():
        if pg_id and script_node.pg_id() != pg_id:
            continue

        script_report = script_node.to_report(include_source)
        report = ScriptsCommandReport(script_report)

        frame_id = script_node.execute_edge().frame_id()
        if frame and ("n" + str(frame_id)) != frame:
            continue
        frame_report = pg.domroot_for_frame_id(frame_id).to_report()
        report.frame = frame_report

        if omit_executors:
            report.script.executor = None

        reports.append(report)
    return to_command_report(pg, reports)


def element_query(input_path: Path, pg_id: PageGraphId, depth: int,
                  debug: bool) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, debug)
    if pg_id.startswith("n"):
        node_report = pg.node(pg_id).to_node_report(depth)
        return to_command_report(pg, node_report)
    if pg_id.startswith("e"):
        edge_report = pg.edge(pg_id).to_edge_report(depth)
        return to_command_report(pg, edge_report)
    raise ValueError("Invalid element id, should be either n## or e##.")


@dataclass
class HtmlCommandReport(Report):
    elements: list[DOMNodeReport]


def html_query_cmd(input_path: Path, frame_filter: Optional[PageGraphId],
                   at_serialization: bool, only_body_content: bool,
                   debug: bool) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, debug)
    dom_nodes = pg.dom_nodes()
    reports = []
    for node in dom_nodes:
        if frame_filter:
            domroot_for_insertion = node.domroot_for_document()
            if not domroot_for_insertion:
                continue
            if frame_filter != domroot_for_insertion.pg_id():
                continue
        if at_serialization and not node.is_present_at_serialization():
            continue
        if only_body_content and not node.is_body_content():
            continue
        reports.append(node.to_report())
    return to_command_report(pg, HtmlCommandReport(reports))


@dataclass
class EffectsCommandReport(Report):
    actor: Report
    action: Report


# The rules we follow for deciding which actions (edges) and elements (nodes)
# a node is responsible for are


# def effects(input_path: Path, pg_id: PageGraphId, loose: bool,
#             debug: bool) -> list[EffectsCommandReport]:
#     reports: list[EffectsCommandReport] = []
#     return reports


@dataclass
class UnknownCommandReport(Report):
    count: int


def unknown(input_path: Path) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, True)
    count = 0
    unknown_node = pg.unknown_node()
    if unknown_node:
        count = len(list(unknown_node.outgoing_edges()))
    return to_command_report(pg, UnknownCommandReport(count))


@dataclass
class ValidationCommandReport(Report):
    success: bool


def validate(input_path: Path) -> CommandReport:
    pg = pagegraph.graph.from_path(input_path, True)
    return to_command_report(pg, ValidationCommandReport(True))
