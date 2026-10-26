#
#   test_issue742_lexreference_target_hvo_live.py
#
#   Live verification for issue #742 LexReferenceOperations TargetsRS HVO membership.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_742_"


def _ensure_ref_type(project, name):
    ref_type = project.LexReferences.FindType(name)
    if ref_type is None:
        ref_type = project.LexReferences.CreateType(
            f"{TEST_PREFIX}{name}", "Symmetric"
        )
    return ref_type


def test_issue742_remove_target_after_hvo_refetch(target_sandbox):
    """RemoveTarget unlinks when caller holds Object(hvo) view."""
    project = target_sandbox
    entries = list(project.LexEntry.GetAll())
    assert len(entries) >= 3, "Target needs at least 3 lex entries for this test"
    sense_a = list(entries[0].SensesOS)[0]
    sense_b = list(entries[1].SensesOS)[0]
    sense_c = list(entries[2].SensesOS)[0]
    ref_type = _ensure_ref_type(project, "Synonym742")
    ref = project.LexReferences.Create(ref_type, [sense_a, sense_b, sense_c])
    try:
        bare_c = project.Object(sense_c.Hvo)
        project.LexReferences.RemoveTarget(ref, bare_c)
        remaining = list(project.LexReferences.GetTargets(ref))
        assert all(s.Hvo != sense_c.Hvo for s in remaining)
        assert len(remaining) == 2
    finally:
        project.LexReferences.Delete(ref)
