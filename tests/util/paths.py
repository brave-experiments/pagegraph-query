from inspect import getsourcefile
from os.path import abspath
from pathlib import Path


# Adapted from https://stackoverflow.com/a/18489147
THIS_FILE = Path(abspath(str(getsourcefile(lambda: 0))))
PROJECT_ROOT_DIR = THIS_FILE.parent.parent.parent
TESTS_CODE_DIR = THIS_FILE.parent.parent / "cases"
TEST_ASSETS_DIR = PROJECT_ROOT_DIR / "tests/assets"


def testcases() -> Path:
    return TEST_ASSETS_DIR / "html"


def graphs() -> Path:
    return TEST_ASSETS_DIR / "graphs"


def generated_graphs() -> Path:
    return graphs() / "gen"


def saved_graphs() -> Path:
    return graphs() / "saved"


def unittests(add_verbose_flag: bool = False) -> list[str]:
    unittest_files: list[str] = []
    for child in TESTS_CODE_DIR.iterdir():
        if not child.is_file() or child.name == "__init__.py":
            continue
        if child.name.startswith("."):
            continue
        if add_verbose_flag:
            unittest_files += ["-v", str(child)]
        else:
            unittest_files.append(str(child))
    return unittest_files
