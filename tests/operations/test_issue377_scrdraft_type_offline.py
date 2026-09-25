#
#   test_issue377_scrdraft_type_offline.py
#
#   Issue #377 item 2: ScrDraftOperations.Create must apply the type label.
#
#   Platform: Python (no FieldWorks required)
#
#   Copyright 2026
#

from pathlib import Path


def _scr_draft_source() -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / "flexicon/code/Scripture/ScrDraftOperations.py").read_text(
        encoding="utf-8"
    )


def test_create_applies_draft_type_not_silent_noop():
    """Source ratchet: Create must coerce type and call the two-arg factory path."""
    source = _scr_draft_source()
    create_block = source.split("def Create(self, description, type=", 1)[1]
    create_block = create_block.split("\n    def ", 1)[0]
    assert "__CoerceDraftType(type)" in create_block
    assert "factory.Create(description, draft_type)" in create_block
    assert "new_draft.Type = draft_type" in create_block
    assert "not applied" not in create_block.lower()


def test_coerce_draft_type_maps_documented_labels():
    """Source ratchet: labels map to the two real ScrDraftType members.

    The LCM enum is SavedVersion / ImportedVersion only (live reflection,
    2026-09-25). ConsultantCheck / BackTranslation do not exist; naming them
    made every Create call raise AttributeError.
    """
    source = _scr_draft_source()
    block = source.split("def __CoerceDraftType(self, type_label):", 1)[1]
    block = block.split("\n    def ", 1)[0]
    for label, member in (
        ("saved_version", "SavedVersion"),
        ("imported_version", "ImportedVersion"),
    ):
        assert f'"{label}": "{member}"' in block
    assert "ScrDraftType.ConsultantCheck" not in source
    assert "ScrDraftType.BackTranslation" not in source


def test_legacy_labels_are_deprecated_not_removed():
    """Source ratchet: 4.9.0 labels still accepted, with a DeprecationWarning."""
    source = _scr_draft_source()
    assert '_DEPRECATED_DRAFT_TYPE_LABELS = frozenset({"consultant_check", "back_translation"})' in source
    block = source.split("def __CoerceDraftType(self, type_label):", 1)[1]
    block = block.split("\n    def ", 1)[0]
    assert "DeprecationWarning" in block
    assert "v5.0.0" in block


def test_unknown_draft_type_raises_parameter_error():
    """Source ratchet: unknown labels must raise FP_ParameterError."""
    source = _scr_draft_source()
    block = source.split("def __CoerceDraftType(self, type_label):", 1)[1]
    block = block.split("\n    def ", 1)[0]
    assert "Unknown draft type" in block
    assert "FP_ParameterError" in block
