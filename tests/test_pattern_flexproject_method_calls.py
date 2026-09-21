#
#   test_pattern_flexproject_method_calls.py
#
#   Regression guard for Operations -> FLExProject helper calls.
#   Ensures self.project.Get*Dict(...) calls in Operations classes
#   reference methods that actually exist on FLExProject.
#

import re
from pathlib import Path


CODEBASE_ROOT = Path(__file__).parent.parent / "flexicon" / "code"
FLEXPROJECT_FILE = CODEBASE_ROOT / "FLExProject.py"


def test_operations_get_dict_calls_exist_on_flexproject():
    """
    Guard against dead helper calls such as self.project.GetMultiStringDict(...)
    when FLExProject does not define that method.
    """
    flexproject_text = FLEXPROJECT_FILE.read_text(encoding="utf-8")
    defined_methods = set(re.findall(r"^\s*def\s+(\w+)\s*\(", flexproject_text, re.MULTILINE))

    pattern = re.compile(r"self\.project\.(Get\w+Dict)\s*\(")
    missing = []

    for py_file in CODEBASE_ROOT.rglob("*Operations.py"):
        for line_num, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
            code_part = line.split("#")[0] if "#" in line else line
            match = pattern.search(code_part)
            if match:
                method_name = match.group(1)
                if method_name not in defined_methods:
                    missing.append(f"{py_file.relative_to(CODEBASE_ROOT)}:{line_num} -> {method_name}")

    assert not missing, (
        "Found self.project.Get*Dict(...) calls to undefined FLExProject methods:\n"
        + "\n".join(missing)
    )
