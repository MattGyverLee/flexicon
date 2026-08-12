#
#   test_agent_version_unicode.py
#
#   Regression coverage for AgentOperations.GetVersion / SetVersion.
#
#   ICmAgent.Version is a monolingual Unicode property in the LCM model, so
#   pythonnet surfaces it as a plain Python str. Reading it through
#   get_String() / ITsString() -- the pattern that is correct for the
#   MultiUnicode ICmAgent.Name -- raised
#   "AttributeError: 'str' object has no attribute 'get_String'" on every
#   call, making both accessors unusable.
#
#   These checks are static (AST based) so they run without a FieldWorks
#   install, matching test_wfianalysis_agent_import.py.
#

import ast
from pathlib import Path

import pytest

SOURCE_PATH = Path(__file__).resolve().parents[1] / "flexicon" / "code" / "Lists" / "AgentOperations.py"

MULTILINGUAL_CALLS = {"get_String", "set_String"}


def _function_named(name):
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    pytest.fail("AgentOperations.%s not found" % name)


def _called_attribute_names(func_node):
    return {
        node.func.attr
        for node in ast.walk(func_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


@pytest.mark.parametrize("method", ["GetVersion", "SetVersion"])
def test_version_accessors_do_not_use_multilingual_string_api(method):
    """Version is Unicode, not MultiUnicode -- get_String/set_String always fail."""
    called = _called_attribute_names(_function_named(method))
    offenders = sorted(called & MULTILINGUAL_CALLS)

    assert not offenders, (
        "%s uses %s on ICmAgent.Version, which pythonnet exposes as a plain str; "
        "assign/read it directly instead" % (method, ", ".join(offenders))
    )


def test_get_version_reads_the_attribute_directly():
    """GetVersion must read agent.Version itself, not a projection of it."""
    func = _function_named("GetVersion")
    reads = [
        node
        for node in ast.walk(func)
        if isinstance(node, ast.Attribute)
        and node.attr == "Version"
        and isinstance(node.ctx, ast.Load)
    ]

    assert reads, "GetVersion should read agent.Version directly"


def test_set_version_assigns_the_attribute_directly():
    """SetVersion must assign agent.Version, not call set_String on it."""
    func = _function_named("SetVersion")
    assignments = [
        target
        for node in ast.walk(func)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute) and target.attr == "Version"
    ]

    assert assignments, "SetVersion should assign agent.Version directly"


def test_name_accessors_still_use_the_multilingual_api():
    """Guard against over-correcting: ICmAgent.Name genuinely is MultiUnicode."""
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "agent.Name.get_String(" in source, (
        "ICmAgent.Name is MultiUnicode and must still be read via get_String()"
    )
