import json
import pathlib
import subprocess
from typing import Optional


def run(pg_crawl_path: pathlib.Path, test_url: str, output_path: pathlib.Path,
        verbose: bool = False, other_args: Optional[list[str]] = None) -> None:
    pg_crawl_cmd = [
        "npm", "run", "crawl", "--",
        "-u", test_url,
        "-o", str(output_path),
    ]

    # Set some sane defaults too
    if other_args is None or "-t" not in other_args:
        pg_crawl_cmd += ["-t", "3"]

    if other_args:
        pg_crawl_cmd += other_args

    stdout_option = None if verbose else subprocess.DEVNULL
    subprocess.run(pg_crawl_cmd, stdout=stdout_option,
                   stderr=subprocess.PIPE, check=True,
                   cwd=pg_crawl_path)


def validate_path(path: str) -> pathlib.Path:
    # First sanity check that the given path was for a node based
    # git repo at all.
    tool_path = pathlib.Path(path)
    if not tool_path.is_dir():
        raise ValueError(
            f"Invalid pagegraph-crawl path: {tool_path} is not a directory")
    package_path = tool_path / "package.json"
    if not package_path.is_file():
        raise ValueError(
            f"Invalid pagegraph-crawl project: {package_path} is not a file")

    # And do some simple checks to make sure it looks like its for
    # the 'pagegraph-crawl' repo.
    with package_path.open("r") as handle:
        try:
            package_data = json.load(handle)
        except json.JSONDecodeError as exc:
            msg = f"Invalid pagegraph-crawl project: {package_path} is not JSON"
            raise ValueError(msg) from exc
        if package_data["name"] != "pagegraph-crawl":
            msg = (f"Invalid pagegraph-crawl project: {package_path} is not "
                "for the pagegraph-crawl project. "
                "key \"name\" does not have value \"pagegraph-crawl\".")
            raise ValueError(msg)

    # Next, do a basic check to see if it looks like pagegraph-crawl
    # has been built. If not, we can try the basic steps to build
    # it ourselves.
    built_run_path = tool_path / "built/run.js"
    if not built_run_path.is_file():
        try:
            subprocess.run(["npm", "install"], cwd=tool_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:
            msg = ("Invalid pagegraph-crawl project: project is not built, "
                  "and `npm install` failed when we tried to run it for you.")
            raise ValueError(msg) from exc

        try:
            subprocess.run(["npm", "run", "build"], cwd=tool_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:
            msg = ("Invalid pagegraph-crawl project: project is not built, " +
                  "and `npm run build` failed when we tried to run it for you.")
            raise ValueError(msg) from exc

        if not built_run_path.is_file():
            msg = ("Invalid pagegraph-crawl project: tried building the "
                f"project for you, but didn't find expected {built_run_path} "
                "file, so something went wrong.")
            raise ValueError(msg)
    return tool_path
