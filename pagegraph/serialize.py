from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, fields
from typing import Any, Optional, TYPE_CHECKING, Union, Sequence

from pagegraph.types import BlinkId, PageGraphId, RequestHeaders

if TYPE_CHECKING:
    from pagegraph.graph import PageGraph
    from pagegraph.types import Url, RequestId
    from packaging.version import Version


@dataclass
class Report:
    pass


@dataclass
class BasicReport(Report):
    name: str


JSONAble = Report | list[Report] | dict[str, Report] | str | int | float | bool | None


@dataclass
class FrameReport(Report):
    id: PageGraphId
    url: Url | None
    blink_id: BlinkId


@dataclass
class DOMElementReport(Report):
    id: PageGraphId
    tag: str
    attrs: dict[str, JSONAble] | None = None


@dataclass
class JSStructureReport(Report):
    name: str
    type: str


@dataclass
class JSCallResultReport(Report):
    method: str
    args: Any
    result: Any
    call_context: FrameReport
    execution_context: Optional[FrameReport] = None


@dataclass
class RequestReport(Report):
    id: PageGraphId
    url: Url | None


@dataclass
class RequestCompleteReport(Report):
    id: PageGraphId
    size: int
    hash: str
    headers: RequestHeaders
    status: str = "complete"


@dataclass
class RequestErrorReport(Report):
    id: PageGraphId
    headers: RequestHeaders | None
    status: str = "error"


@dataclass
class RequestChainReport(Report):
    request_id: RequestId
    request_type: str
    request: RequestReport
    redirects: list[RequestReport]
    result: RequestCompleteReport | RequestErrorReport | None


@dataclass
class ScriptReport(Report):
    id: PageGraphId
    type: str
    hash: str
    url: Url | None = None
    source: str | None = None
    executor: Union[DOMElementReport, "ScriptReport", None] = None


@dataclass
class ElementReport(Report):
    id: PageGraphId
    type: str
    details: Union[dict[str, JSONAble], None]


DOMNodeReport = Union[DOMElementReport, FrameReport]

BriefNodeReport = ElementReport
BriefEdgeReport = ElementReport


@dataclass
class NodeReport(ElementReport):
    incoming_edges: list[Union["BriefEdgeReport", "EdgeReport", str]]
    outgoing_edges: list[Union["BriefEdgeReport", "EdgeReport", str]]
    kind: str = "node"


@dataclass
class EdgeReport(ElementReport):
    incoming_node: Union["NodeReport", "BriefNodeReport", str, None]
    outgoing_node: Union["NodeReport", "BriefNodeReport", str, None]
    kind: str = "edge"


@dataclass
class Reportable(ABC):
    def to_report(self) -> Report:
        raise NotImplementedError()


@dataclass
class CommandReport(Report):
    @dataclass
    class Metadata(Report):
        @dataclass
        class Versions(Report):
            tool: str
            graph: str
        versions: Versions
        url: Url
    meta: Metadata
    report: Union[Report, Sequence[Report]]


def to_command_report(pg: PageGraph,
                      report: Union[Report, Sequence[Report]]) -> CommandReport:
    versions_data = CommandReport.Metadata.Versions(
        str(pg.tool_version), str(pg.graph_version))
    metadata = CommandReport.Metadata(versions_data, pg.url)
    return CommandReport(metadata, report)


def report_field_name(field_name: str) -> str:
    return field_name.replace("_", " ")


def to_jsonable(data: JSONAble) -> Any:
    if isinstance(data, list):
        return [to_jsonable(x) for x in data if x is not None]

    if isinstance(data, dict):
        jsonable_dict: dict[str, JSONAble] = {}
        for k, v in data.items():
            if v is None:
                continue
            report_key = report_field_name(k)
            jsonable_dict[report_key] = to_jsonable(v)
        return jsonable_dict

    if isinstance(data, Report):
        jsonable_map = {}
        for field in fields(data):
            field_name = field.name
            value = getattr(data, field_name)
            if value is None:
                continue
            report_name = report_field_name(field_name)
            jsonable_map[report_name] = to_jsonable(value)
        return jsonable_map

    return data
