#
#   test_agent_syncable_properties_offline.py
#
#   Offline coverage for issue #350 without importing flexicon (no LCM on Linux CI).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "AgentOperations.py"


def _method_body(source: str, method_name: str) -> str:
    match = re.search(
        rf"def {method_name}\(.*?(?=\n    def |\n    # ---|\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, f"{method_name} not found"
    return match.group(0)


def test_agent_get_syncable_properties_does_not_read_description():
    source = AGENT_OPS.read_text(encoding="utf-8")
    assert "def GetSyncableProperties" in source
    body = _method_body(source, "GetSyncableProperties")
    assert "item.Description" not in body
    assert "agent.Description" not in body
    assert '"Human"' in body or "'Human'" in body
    assert "GetVersion" in body


def test_agent_description_overrides_are_safe():
    source = AGENT_OPS.read_text(encoding="utf-8")
    get_desc = _method_body(source, "GetDescription")
    set_desc = _method_body(source, "SetDescription")
    assert "item.Description" not in get_desc
    assert "item.Description" not in set_desc
    assert 'return ""' in get_desc
