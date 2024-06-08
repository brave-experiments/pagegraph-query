
from __future__ import annotations

import pathlib
from subprocess import DEVNULL, PIPE, Popen
import time


def url_for_case(test_case: pathlib.Path, port: int) -> str:
    return f"http://[::]:{port}/{test_case.name}"


def start(tests_dir: pathlib.Path,
          port: int | None = None) -> Popen:  # type: ignore[type-arg]
    start_server_cmd = [
        "/usr/bin/env", "python3",
        "-m", "http.server",
        "-d", str(tests_dir)
    ]
    if port is not None:
        start_server_cmd += ["-p", str(port)]

    print("Starting test http.server")
    handle = Popen(start_server_cmd, stdout=DEVNULL, stderr=PIPE)
    time.sleep(2)
    return handle


def shutdown(handle: Popen) -> None:  # type: ignore[type-arg]
    handle.terminate()
