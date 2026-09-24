#
#   test_issue350_agent_gsp_offline.py
#
#   Offline regression for issue #350 (Agent GetSyncableProperties / Description).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "AgentOperations.py"


def _method_body(source: str, method_name: str) -> str:
    match = re.search(
        rf"def {method_name}\(.*?(?=\n    @OperationsMethod|\n    def |\n    # ---|\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, f"{method_name} not found"
    return match.group(0)


def test_agent_get_syncable_properties_does_not_touch_description():
    """ICmAgent has no Description; inherited GSP must not be used (issue #350)."""
    source = AGENT_OPS.read_text(encoding="utf-8")
    body = _method_body(source, "GetSyncableProperties")
    assert "def GetSyncableProperties" in body
    assert "item.Description" not in body
    assert "agent.Description" not in body
    assert "super().GetSyncableProperties" not in body
    assert "agent.Name" in body
    assert '"Human"' in body
    assert "GetVersion" in body


def test_agent_description_overrides_are_safe_noops():
    source = AGENT_OPS.read_text(encoding="utf-8")
    get_desc = _method_body(source, "GetDescription")
    assert 'return ""' in get_desc
    assert ".Description" not in get_desc

    set_desc = _method_body(source, "SetDescription")
    assert "set_String" not in set_desc
    assert ".Description" not in set_desc


def test_issue350_lex_lead_ruling_on_disk():
    ruling = REPO_ROOT / "specs" / "350-agent-gsp" / "rulings.md"
    assert ruling.is_file()
    text = ruling.read_text(encoding="utf-8")
    assert "GetSyncableProperties" in text
    assert "no `Description`" in text or "no Description" in text
