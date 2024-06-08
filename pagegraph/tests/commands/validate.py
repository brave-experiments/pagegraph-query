import json
import pathlib
import subprocess


def validate_path(path: str) -> bool:
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
        except json.JSONDecodeError:
            raise ValueError(
               f"Invalid pagegraph-crawl project: {package_path} is not JSON")
        if package_data["name"] != "pagegraph-crawl":
            raise ValueError(
                f"Invalid pagegraph-crawl project: {package_path} is not "
                "for the pagegraph-crawl project. "
                "key \"name\" does not have value \"pagegraph-crawl\".")

    # Next, do a basic check to see if it looks like pagegraph-crawl
    # has been built. If not, we can try the basic steps to build
    # it ourselves.
    built_run_path = tool_path / "built/run.js"
    if not built_run_path.is_file():
        try:
            subprocess.run(["npm", "install"], cwd=tool_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise ValueError(
                f"Invalid pagegraph-crawl project: project is not built, "
                "and `npm install` failed when we tried to run it for you.")

        try:
            subprocess.run(["npm", "run", "build"], cwd=tool_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise ValueError(
                f"Invalid pagegraph-crawl project: project is not built, "
                "and `npm run build` failed when we tried to run it for you.")

        if not built_run_path.is_file():
            raise ValueError(
                "Invalid pagegraph-crawl project: tried building the project "
                f"for you, but didn't find expected {built_run_path} file, "
                "so something went wrong.")
    return True
