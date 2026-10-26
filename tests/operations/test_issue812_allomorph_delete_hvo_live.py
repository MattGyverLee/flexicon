#
#   test_issue812_allomorph_delete_hvo_live.py
#
#   Live verification for issue #812 AllomorphOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_812_"


def _alternate_hvos(entry):
    return [int(a.Hvo) for a in entry.AlternateFormsOS]


def test_issue812_delete_removes_from_alternateformsos_by_hvo(target_sandbox):
    """Delete removes an alternate when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        allo_ops = project.Allomorphs
        keep = allo_ops.Create(entry, f"{TEST_PREFIX}keep", morphType="suffix")
        victim = allo_ops.Create(entry, f"{TEST_PREFIX}victim", morphType="suffix")
        assert keep is not None and victim is not None

        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        starting = entry.AlternateFormsOS.Count

        allo_ops.Delete(bare_view)

        assert entry.AlternateFormsOS.Count == starting - 1
        assert int(hvo) not in _alternate_hvos(entry)
        assert int(keep.Hvo) in _alternate_hvos(entry)
    finally:
        project.LexEntry.Delete(entry)
