#
#   test_issue804_lexsense_delete_hvo_live.py
#
#   Live verification for issue #804 LexSenseOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_804_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


def test_issue804_delete_removes_from_sensesos_by_hvo(target_sandbox):
    """Delete removes a sense when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    entry = _make_entry(project, "entry")
    sense_ops = project.Senses

    try:
        keep = sense_ops.Create(entry, f"{TEST_PREFIX}keep")
        victim = sense_ops.Create(entry, f"{TEST_PREFIX}victim")
        assert sense_ops.GetAll(entry).Count >= 2

        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        starting = sense_ops.GetAll(entry).Count

        sense_ops.Delete(bare_view)

        assert sense_ops.GetAll(entry).Count == starting - 1
        assert not sense_ops.Exists(entry, hvo)
        assert sense_ops.Exists(entry, keep.Hvo)
    finally:
        project.LexEntry.Delete(entry)
