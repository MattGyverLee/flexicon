#
#   test_issue810_example_delete_hvo_live.py
#
#   Live verification for issue #810 ExampleOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_810_"


def _sense_has_example_hvo(example_ops, sense, hvo):
    return any(int(ex.Hvo) == int(hvo) for ex in example_ops.GetAll(sense))


def test_issue810_delete_removes_from_examplesos_by_hvo(target_sandbox):
    """Delete removes an example when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        sense = project.Senses.Create(entry, f"{TEST_PREFIX}gloss")
        example_ops = project.Examples
        keep = example_ops.Create(sense, f"{TEST_PREFIX}keep")
        victim = example_ops.Create(sense, f"{TEST_PREFIX}victim")
        assert len(list(example_ops.GetAll(sense))) >= 2

        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        starting = len(list(example_ops.GetAll(sense)))

        example_ops.Delete(bare_view)

        assert len(list(example_ops.GetAll(sense))) == starting - 1
        assert not _sense_has_example_hvo(example_ops, sense, hvo)
        assert _sense_has_example_hvo(example_ops, sense, keep.Hvo)
    finally:
        project.LexEntry.Delete(entry)
