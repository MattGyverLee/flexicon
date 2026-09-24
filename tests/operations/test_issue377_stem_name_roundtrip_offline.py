#
#   test_issue377_stem_name_roundtrip_offline.py
#
#   Offline ratchet for issue #377 item 1 live stem_name round-trip module.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LIVE_MODULE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue377_stem_name_roundtrip_live.py"
)


TEST_PREFIX_SENTINEL = "TEST_377_"


def test_issue377_stem_name_live_module_documents_round_trip():
    assert LIVE_MODULE.is_file(), "missing live module for #377 stem_name slice"
    text = LIVE_MODULE.read_text(encoding="utf-8")
    assert "sena3_sandbox" in text
    assert "StemNameRA" in text
    assert "Allomorph" in text
    assert "best_analysis_text" in text
    assert "MoStemAllomorph" in text
    assert TEST_PREFIX_SENTINEL in text
