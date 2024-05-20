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


def report_field_name(field_name: str) -> str:
    return field_name.replace("_", " ")


JSONAble = Report | list[Report] | dict[str, Report] | str | int | float | bool


def to_jsonable(data: JSONAble) -> Any:
    if isinstance(data, list):
        return [to_jsonable(x) for x in data]

    if isinstance(data, dict):
        jsonable_dict: dict[str, JSONAble] = {}
        for k, v in data.items():
            report_key = report_field_name(k)
            jsonable_dict[report_key] = to_jsonable(v)
        return jsonable_dict

    if isinstance(data, Report):
        jsonable_map = {}
        for field in fields(data):
            field_name = field.name
            value = getattr(data, field_name)
            report_name = report_field_name(field_name)
            jsonable_map[report_name] = to_jsonable(value)
        return jsonable_map

    return data
