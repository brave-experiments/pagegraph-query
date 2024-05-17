from dataclasses import dataclass, fields
from typing import Any, cast

from pagegraph.graph.types import BlinkId, PageGraphId, Url


@dataclass
class Report:
    pass


@dataclass
class FrameReport(Report):
    nid: PageGraphId
    url: Url | None
    blink_id: BlinkId


@dataclass
class RequestReport(Report):
    nid: PageGraphId
    url: Url
    type: str
    hash: str | None
    size: int | None
    headers: str | None


@dataclass
class DOMElementReport(Report):
    nid: PageGraphId
    tag: str


@dataclass
class JSStructureReport(Report):
    name: str
    type: str


@dataclass
class JSInvokeReport(Report):
    args: Any
    result: Any


class Reportable:
    def to_report(self) -> Report:
        raise NotImplementedError()


def to_jsonable(data: Report | list[Report]) -> Any:
    if isinstance(data, list):
        return [to_jsonable(x) for x in data]

    if not isinstance(data, Report):
        return data

    jsonable_map = {}
    for field in fields(data):
        field_name = field.name
        value = getattr(data, field_name)
        report_name = field_name.replace("_", " ")
        jsonable_map[report_name] = to_jsonable(value)
    return jsonable_map
