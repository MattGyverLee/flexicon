# ----------------------------------------------------------------------------
#   test_anthropology_get_syncable_properties.py
#   Regression for issue #349: GetSyncableProperties called the per-class
#   __ResolveObject helper that AnthropologyOperations never defined.
# ----------------------------------------------------------------------------

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ANTHRO_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "AnthropologyOperations.py"


def _get_syncable_properties_body(source: str) -> str:
    lines = source.splitlines()
    in_method = False
    body: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def GetSyncableProperties("):
            in_method = True
            continue
        if in_method:
            if stripped.startswith("def ") and not stripped.startswith("def GetSyncableProperties("):
                break
            if stripped.startswith("@") and body:
                break
            body.append(line)
    return "\n".join(body)


class TestAnthropologyGetSyncablePropertiesResolve:
    def test_get_syncable_properties_uses_get_item_object(self):
        source = ANTHRO_OPS.read_text(encoding="utf-8")
        body = _get_syncable_properties_body(source)
        assert "__GetItemObject" in body
        assert "__ResolveObject" not in body

    def test_class_defines_get_item_object_helper(self):
        source = ANTHRO_OPS.read_text(encoding="utf-8")
        assert re.search(r"def __GetItemObject\s*\(", source)
        assert not re.search(r"def __ResolveObject\s*\(", source)


class TestAnthropologyGetSyncablePropertiesIssue359:
    def test_gsp_does_not_guard_phantom_anthro_members(self):
        source = ANTHRO_OPS.read_text(encoding="utf-8")
        body = _get_syncable_properties_body(source)
        assert 'hasattr(anthro_item, "AnthroCode")' not in body
        assert 'hasattr(anthro_item, "CategoryRA")' not in body
        assert 'props["Abbreviation"]' in body
        assert 'props["AnthroCode"]' in body
        assert 'props["Category"] = None' in body
