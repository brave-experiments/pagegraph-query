import pathlib

import pagegraph.tests.util.paths as PG_PATHS


HTML_FILETYPE = ".html"
GRAPH_FILETYPE = ".graphml"


def matching_cases(test_filter: None | str = None) -> list[pathlib.Path]:
    cases = []
    for test_case in PG_PATHS.testcases().iterdir():
        if not test_case.is_file():
            continue
        if not test_case.name.endswith(HTML_FILETYPE):
            continue
        if not test_filter or test_filter in test_case.name:
            cases.append(test_case)
    return cases


def graph_path_for_case(test_case: pathlib.Path) -> pathlib.Path:
    graph_file_name = test_case.name.replace(HTML_FILETYPE, GRAPH_FILETYPE)
    return PG_PATHS.generated_graphs() / graph_file_name


def clear_generated_graphs() -> None:
    for graph in PG_PATHS.generated_graphs().iterdir():
        if graph.name.endswith(GRAPH_FILETYPE):
            graph.unlink()
