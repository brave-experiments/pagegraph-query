from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import cast, TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from typing import Any, ClassVar, Optional

    from pagegraph.cli.result import CommandResult


class CommandBase(ABC):
    command_name: ClassVar[str]
    command_desc: ClassVar[str]

    input_path: Path
    debug: bool

    @classmethod
    def setup_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        parser = subparser_handle.add_parser(
            cls.command_name,
            help=cls.command_desc)
        parser.add_argument(
            "input",
            type=Path,
            help="Path to PageGraph recording.")
        parser.set_defaults(command_cls=cls)
        return cast('ArgumentParser', parser)

    @classmethod
    def add_subparser(cls, subparser_handle: _SubParsersAction[Any]) -> ArgumentParser:
        return cls.setup_subparser(subparser_handle)

    @classmethod
    def from_args(cls, args: Namespace) -> CommandBase:
        return cls(args.input, args.debug)

    @classmethod
    def run(cls, args: Namespace) -> Optional[str]:
        instance = cls.from_args(args)
        instance.validate()
        result = instance.execute()
        return cls.format(result)

    @classmethod
    def format(cls, result: CommandResult) -> Optional[str]:
        return result.to_json()

    def __init__(self, input_path: Path, debug: bool = False) -> None:
        self.input_path = input_path
        self.debug = debug

    def validate(self) -> None:
        if not self.input_path.is_file():
            raise ValueError(
                f"Unable to read from input file: {self.input_path.name}")

    def execute(self) -> CommandResult:
        raise NotImplementedError()
