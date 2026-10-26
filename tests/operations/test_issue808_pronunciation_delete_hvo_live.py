#
#   test_issue808_pronunciation_delete_hvo_live.py
#
#   Live verification for issue #808 PronunciationOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_808_"


def _entry_has_hvo(pron_ops, entry, hvo):
    return any(int(p.Hvo) == int(hvo) for p in pron_ops.GetAll(entry))


def test_issue808_delete_removes_from_pronunciationsos_by_hvo(target_sandbox):
    """Delete removes a pronunciation when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        pron_ops = project.Pronunciations
        keep = pron_ops.Create(entry, f"{TEST_PREFIX}keep")
        victim = pron_ops.Create(entry, f"{TEST_PREFIX}victim")
        assert len(list(pron_ops.GetAll(entry))) >= 2

        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        starting = len(list(pron_ops.GetAll(entry)))

        pron_ops.Delete(bare_view)

        assert len(list(pron_ops.GetAll(entry))) == starting - 1
        assert not _entry_has_hvo(pron_ops, entry, hvo)
        assert _entry_has_hvo(pron_ops, entry, keep.Hvo)
    finally:
        project.LexEntry.Delete(entry)
