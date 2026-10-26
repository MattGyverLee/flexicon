#
#   test_issue806_etymology_delete_hvo_live.py
#
#   Live verification for issue #806 EtymologyOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_806_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


def _entry_has_hvo(etym_ops, entry, hvo):
    return any(int(e.Hvo) == int(hvo) for e in etym_ops.GetAll(entry))


def test_issue806_delete_removes_from_etymologyos_by_hvo(target_sandbox):
    """Delete removes an etymology when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    entry = _make_entry(project, "entry")
    etym_ops = project.Etymologies

    try:
        keep = etym_ops.Create(entry, source=f"{TEST_PREFIX}keep")
        victim = etym_ops.Create(entry, source=f"{TEST_PREFIX}victim")
        assert len(list(etym_ops.GetAll(entry))) >= 2

        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        starting = len(list(etym_ops.GetAll(entry)))

        etym_ops.Delete(bare_view)

        assert len(list(etym_ops.GetAll(entry))) == starting - 1
        assert not _entry_has_hvo(etym_ops, entry, hvo)
        assert _entry_has_hvo(etym_ops, entry, keep.Hvo)
    finally:
        project.LexEntry.Delete(entry)
