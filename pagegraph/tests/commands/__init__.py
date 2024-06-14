import pathlib
import sys
import subprocess

import pagegraph.tests.util.paths as PG_PATHS
import pagegraph.tests.commands.cases as PG_CASES
import pagegraph.tests.commands.crawl as PG_CRAWL
import pagegraph.tests.commands.server as PG_SERVER


def print_err(msg: str) -> None:
    print(msg, file=sys.stderr)


def serve(port: int, verbose: bool, other_args: list[str]) -> None:
    PG_SERVER.start_and_wait(PG_PATHS.testcases(), port, verbose)


def setup(tool_path: str, testcase_filter: None, port: int,
          should_clear: bool, verbose: bool, other_args: list[str]) -> None:
    if should_clear:
        PG_CASES.clear_graphs()

    pg_crawl_dir = None
    try:
        pg_crawl_dir = PG_CRAWL.validate_path(tool_path)
    except ValueError as e:
        print_err("Invalid pagegraph-crawl path provided.")
        print_err(str(e))
    assert pg_crawl_dir

    test_cases = PG_CASES.matching_cases(testcase_filter)

    handle = PG_SERVER.start(PG_PATHS.testcases(), port, verbose)
    try:
        for test_case in test_cases:
            print(f" - generating graph for {test_case.name}")
            input_url = PG_SERVER.url_for_case(test_case, port)
            output_path = PG_CASES.graph_path_for_case(test_case)
            PG_CRAWL.run(pg_crawl_dir, input_url, output_path, verbose,
                         other_args)
    except subprocess.CalledProcessError as e:
        print_err("!!! Brave crashed")
        print_err(str(e))
    PG_SERVER.shutdown(handle)


def run(verbose: bool) -> None:
    unittest_files: list[str] = []
    for child in PG_PATHS.unittests().iterdir():
        if not child.is_file() or child.name == "__init__.py":
            continue
        if verbose:
            unittest_files += ["-v", str(child)]
        else:
            unittest_files.append(str(child))

    simple_test_arg = [
        "/usr/bin/env", "python3",
        "-m", "unittest",
    ] + unittest_files
    subprocess.run(simple_test_arg)
