#
#   test_issue268_resolver_hvo_gate_offline.py
#
#   Offline ratchet for issue #268 HVO-entry live gates (file presence and
#   binding preconditions documented in-source).
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LIVE_GATE = (
    REPO_ROOT / "tests" / "operations" / "test_issue268_resolver_hvo_gate_live.py"
)


def test_issue268_live_gate_module_exists_with_all_gate_sites():
    assert LIVE_GATE.is_file(), "missing live gate module for #268"
    text = LIVE_GATE.read_text(encoding="utf-8")
    for site in (
        "GetCatalogSourceId",
        "GetPhoneEnv",
        "GetInflectionClasses",
        "GetAffixSlots",
        "GetFormAudio",
        "GetMorphType",
        "GetSubcategories",
        "GetEntryCount",
    ):
        assert site in text, f"missing live gate for {site}"
    assert "isinstance(hvo, int)" in text
    assert "CatalogSourceId" in text
    assert "PhoneEnvRC" in text
    assert "InflectionClassesOC" in text
    assert "AffixSlotsOC" in text
    assert "MorphTypeRA" in text
    assert "SubPossibilitiesOS" in text
    assert "requires_live_project" in text
