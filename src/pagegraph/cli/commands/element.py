from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import networkx

from pagegraph.cli.commands.abc.base import CommandBase
from pagegraph.cli.result import CommandResult
from pagegraph.cli.validate import is_pg_id
import pagegraph.graph
from pagegraph.serialize import ReportBase

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from typing import Any, Optional, Union

    from pagegraph.serialize import ScriptReport, BasicReport, FrameReport
    from pagegraph.types import PageGraphId


@dataclass
class BytesWrittenResult(ReportBase):
    num_bytes: int


class ElementCommand(CommandBase):
    command_name = "elm"
    command_desc = "Print information about a node or edge in the graph."

    pg_id: PageGraphId
    depth: int
    output_path: Optional[Path]

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = super(ElementCommand, cls).add_subparser(subparser_handle)
        parser.add_argument(
            "id",
            help="The id of the node to print information about "
                "(as described by PageGraph node ids, in the format 'n##')")
        parser.add_argument(
            "-d", "--depth",
            default=1,
            type=int,
            help="Depth of the recursion to summarize in the graph. Defaults "
                 "to 1 (only print detailed information about target element).")
        parser.add_argument(
            "--graphml", "-g",
            type=Path,
            help="Write the element (and its surrounding subgraph, as "
                 "determined by the depth argument) to disk as a graphml "
                 "encoded graph at the given path.")
        return parser

    @classmethod
    def from_args(cls, args: Namespace) -> ElementCommand:
        return ElementCommand(args.input, args.id, args.depth, args.graphml,
                              args.debug)

    # pylint: disable=too-many-positional-arguments
    def __init__(self, input_path: Path, pg_id: PageGraphId, depth: int,
                 output_path: Optional[Path], debug: bool) -> None:
        self.pg_id = pg_id
        self.depth = depth
        self.output_path = output_path
        super().__init__(input_path, debug)

    def validate(self) -> None:
        if self.pg_id:
            is_pg_id(self.pg_id)
        return super().validate()

    def execute(self) -> CommandResult:
        pg = pagegraph.graph.from_path(self.input_path, self.debug)
        if self.pg_id.startswith("n"):
            target_node = pg.node(self.pg_id)
            if self.output_path:
                subgraph = target_node.subgraph(self.depth)
                text = "\n".join(list(networkx.generate_graphml(subgraph)))
                num_bytes = self.output_path.write_text(text)
                report = BytesWrittenResult(num_bytes)
                return CommandResult(pg, report)

            node_report = target_node.to_node_report(self.depth)
            return CommandResult(pg, node_report)

        target_edge = pg.edge(self.pg_id)
        if self.output_path:
            subgraph = target_edge.subgraph(self.depth)
            text = "\n".join(list(networkx.generate_graphml(subgraph)))
            num_bytes = self.output_path.write_text(text)
            report = BytesWrittenResult(num_bytes)
            return CommandResult(pg, report)

        edge_report = target_edge.to_edge_report(self.depth)
        return CommandResult(pg, edge_report)
