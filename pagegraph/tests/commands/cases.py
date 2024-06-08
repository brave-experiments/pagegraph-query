import pathlib

import pagegraph.tests.util.paths as PG_PATHS


HTML_FILETYPE = ".html"
GRAPH_FILETYPE = ".graphml"


def matching_cases(test_filter: None | str = None) -> list[pathlib.Path]:
    matching_cases = []
    for test_case in PG_PATHS.testcases().iterdir():
        if not test_case.is_file():
            continue
        if not test_case.name.endswith(HTML_FILETYPE):
            continue
        if not test_filter or test_filter in test_case.name:
            matching_cases.append(test_case)
    return matching_cases


def graph_path_for_case(test_case: pathlib.Path) -> pathlib.Path:
    graph_file_name = test_case.name.replace(HTML_FILETYPE, GRAPH_FILETYPE)
    return PG_PATHS.graphs() / graph_file_name


def clear_graphs() -> None:
    for graph in PG_PATHS.graphs().iterdir():
        if graph.name.endswith(GRAPH_FILETYPE):
            graph.unlink()
