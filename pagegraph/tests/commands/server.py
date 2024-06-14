
from __future__ import annotations

import pathlib
from subprocess import DEVNULL, PIPE, Popen, run
import time


def url_for_case(test_case: pathlib.Path, port: int) -> str:
    return f"http://[::]:{port}/{test_case.name}"


def start_and_wait(tests_dir: pathlib.Path, port: int | None = None,
                   verbose: bool = False) -> None:
    start_server_cmd = [
        "/usr/bin/env", "python3",
        "-m", "http.server",
        "-d", str(tests_dir)
    ]
    if port is not None:
        start_server_cmd += [str(port)]
    print("Starting test http.server", start_server_cmd)
    run(start_server_cmd)


def start(tests_dir: pathlib.Path,
          port: int | None = None,
          verbose: bool = False) -> Popen:  # type: ignore[type-arg]
    start_server_cmd = [
        "/usr/bin/env", "python3",
        "-m", "http.server",
        "-d", str(tests_dir)
    ]
    if port is not None:
        start_server_cmd += [str(port)]

    stdout_option = PIPE if verbose else DEVNULL

    print("Starting test http.server")
    handle = Popen(start_server_cmd, stdout=stdout_option, stderr=PIPE)
    time.sleep(2)
    return handle


def shutdown(handle: Popen) -> None:  # type: ignore[type-arg]
    handle.terminate()
