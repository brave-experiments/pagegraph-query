from __future__ import annotations

from dataclasses import dataclass

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
import pagegraph.graph
from pagegraph.serialize import ReportBase


@dataclass
class Result(ReportBase):
    count: int


class UnknownCommand(CommandBase):
    command_name = "unknown"
    command_desc = (
        "Print information about any events that occurred where we "
        + "could not attribute the script event to a running "
        + "script. (note this is different from the 'validate' "
        + "command, which only checks if the structure of the graph "
        + "is as expected).")

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        count = 0
        unknown_node = pg.unknown_node()
        if unknown_node:
            count = len(list(unknown_node.outgoing_edges()))
        return CommandResult(pg, Result(count))
