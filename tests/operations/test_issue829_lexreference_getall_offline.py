#
#   test_issue829_lexreference_getall_offline.py
#
#   Offline ratchet for issue #829: LexReferenceOperations.GetAll must not
#   use the non-existent ReferringLexReferences property.
#
#   Copyright 2026
#

import pathlib

SRC = (
    pathlib.Path(__file__).resolve().parents[2]
    / "flexicon" / "code" / "Lexicon" / "LexReferenceOperations.py"
)


def test_source_has_no_referring_lex_references():
    """ReferringLexReferences exists on no LCM interface."""
    assert "ReferringLexReferences" not in SRC.read_text(encoding="utf-8")


def test_source_uses_real_reference_properties():
    text = SRC.read_text(encoding="utf-8")
    for name in ("LexSenseReferences", "LexEntryReferences", "MembersOC"):
        assert name in text
