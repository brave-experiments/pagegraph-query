from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from argparse import _SubParsersAction


@dataclass
class Result(ReportBase):
    success: bool


class ValidateCommand(CommandBase):
    command_name = "validate"
    command_desc = "Runs all validation and structure checks against a graph."

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, True)
        return CommandResult(pg, Result(True))
