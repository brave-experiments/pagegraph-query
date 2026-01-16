from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Union, Sequence

from pagegraph.types import BlinkId, PageGraphId, ResponseHeaders

if TYPE_CHECKING:
    from typing import Any, Optional

    from pagegraph.graph import PageGraph
    from pagegraph.types import Url, RequestId, RequestHeaders
    from packaging.version import Version


@dataclass
class ReportBase(ABC):
    pass


@dataclass
class BasicReport(ReportBase):
    name: str


JSONAble = (
    ReportBase | Sequence[ReportBase] | dict[str, ReportBase] | str | int |
    float | bool | None)


@dataclass
class FrameReport(ReportBase):
    id: PageGraphId
    main_frame: bool
    url: Optional[Url]
    security_origin: Optional[Url]
    blink_id: BlinkId


@dataclass
class DOMElementReport(ReportBase):
    id: PageGraphId
    tag: str
    attrs: dict[str, JSONAble] | None = None


@dataclass
class JSStructureReport(ReportBase):
    name: str
    type: str


@dataclass
class JSCallResultReport(ReportBase):
    method: str
    args: Any
    result: Any
    call_context: FrameReport
    execution_context: Optional[FrameReport] = None


@dataclass
class RequestReport(ReportBase):
    id: PageGraphId
    url: Url | None
    headers: RequestHeaders | None


@dataclass
class RequestCompleteReport(ReportBase):
    id: PageGraphId
    size: int
    hash: str
    headers: ResponseHeaders | None
    status: str = "complete"


@dataclass
class RequestErrorReport(ReportBase):
    id: PageGraphId
    headers: ResponseHeaders | None
    status: str = "error"


@dataclass
class RequestChainReport(ReportBase):
    request_id: RequestId
    request_type: str
    request: RequestReport
    redirects: list[RequestReport]
    result: RequestCompleteReport | RequestErrorReport | None


@dataclass
class ScriptReport(ReportBase):
    id: PageGraphId
    type: str
    hash: str
    url: Url | None = None
    source: str | None = None
    executor: Union[DOMElementReport, ScriptReport, None] = None


@dataclass
class ElementReport(ReportBase):
    id: PageGraphId
    type: str
    details: Union[dict[str, JSONAble], None]


DOMNodeReport = Union[DOMElementReport, FrameReport]

BriefNodeReport = ElementReport
BriefEdgeReport = ElementReport


@dataclass
class NodeReport(ElementReport):
    incoming_edges: list[Union[BriefEdgeReport, EdgeReport, str]]
    outgoing_edges: list[Union[BriefEdgeReport, EdgeReport, str]]
    kind: str = "node"


@dataclass
class EdgeReport(ElementReport):
    incoming_node: Union[NodeReport, BriefNodeReport, str, None]
    outgoing_node: Union[NodeReport, BriefNodeReport, str, None]
    kind: str = "edge"


@dataclass
class Reportable(ABC):
    def to_report(self) -> ReportBase:
        raise NotImplementedError()


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

    if isinstance(data, ReportBase):
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
