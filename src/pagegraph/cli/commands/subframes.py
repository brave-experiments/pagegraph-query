from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
import pagegraph.graph
from pagegraph.serialize import ReportBase
from pagegraph.types import PartyFilterOption

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from typing import Any

    from pagegraph.serialize import DOMElementReport, FrameReport


@dataclass
class Result(ReportBase):
    parent_frame: FrameReport
    iframe: DOMElementReport
    child_frames: list[FrameReport]


class SubFramesCommand(CommandBase):
    command_name = "subframes"
    command_desc = "Print information about subframes created by page."

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = super(SubFramesCommand, cls).add_subparser(subparser_handle)
        parser.add_argument(
            "-l", "--local",
            action="store_true",
            help="Print information about frames that are inherit their parent "
                "frame's security context (i.e., about:blank, about:srcdoc) at "
                "serialization time.")
        parser.add_argument(
            "--party-filter",
            choices=PartyFilterOption,
            default=PartyFilterOption.NONE.value,
            help="Only return frames that have the same (first-party) or "
                 "different (third-party) security origin as the top-level "
                 "document.")
        return parser

    @classmethod
    def from_args(cls, args: Namespace) -> SubFramesCommand:
        return SubFramesCommand(args.input, args.local, args.party_filter,
                                args.debug)

    def __init__(self, input_path: Path, local_only: bool,
                 party_filter: PartyFilterOption, debug: bool = False) -> None:
        self.local_only = local_only
        self.party_filter = party_filter
        super().__init__(input_path, debug)

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        results: list[Result] = []
        for iframe_node in pg.iframe_nodes():
            if (self.local_only and
                not iframe_node.is_security_origin_inheriting()):
                continue

            child_domroot_nodes = iframe_node.child_domroot_nodes()
            if (self.party_filter != PartyFilterOption.NONE and
                    len(child_domroot_nodes) == 0):
                continue

            if (self.party_filter == PartyFilterOption.FIRST_PARTY and
                    iframe_node.is_third_party_to_root()):
                continue

            if (self.party_filter == PartyFilterOption.THIRD_PARTY and
                    not iframe_node.is_third_party_to_root()):
                continue

            parent_frame_report = iframe_node.execution_context().to_report()
            iframe_elm_report = iframe_node.to_report()
            child_frame_reports: list[FrameReport] = []
            for child_domroot in child_domroot_nodes:
                child_frame_reports.append(child_domroot.to_report())

            subframe_report = Result(parent_frame_report, iframe_elm_report,
                                     child_frame_reports)
            results.append(subframe_report)
        return CommandResult(pg, results)
