#
#   test_issue814_lexref_delete_hvo_live.py
#
#   Live verification for issue #814 LexReferenceOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_814_"


def _type_member_hvos(ref_type):
    """Read the ILexRefType.MembersOC HVOs back from the LCM."""
    return [int(r.Hvo) for r in ref_type.MembersOC]


def test_issue814_delete_removes_from_membersoc_by_hvo(target_sandbox):
    """Delete removes a reference when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    ref_ops = project.LexReferences
    type_name = f"{TEST_PREFIX}Synonym"
    entry1 = project.LexEntry.Create(f"{TEST_PREFIX}a")
    entry2 = project.LexEntry.Create(f"{TEST_PREFIX}b")
    entry3 = None
    try:
        sense1 = project.Senses.Create(entry1, f"{TEST_PREFIX}gloss_a")
        sense2 = project.Senses.Create(entry2, f"{TEST_PREFIX}gloss_b")
        ref_type = ref_ops.CreateType(type_name, "Symmetric")
        keep = ref_ops.Create(ref_type, [sense1, sense2])

        entry3 = project.LexEntry.Create(f"{TEST_PREFIX}c")
        sense3 = project.Senses.Create(entry3, f"{TEST_PREFIX}gloss_c")
        victim = ref_ops.Create(ref_type, [sense1, sense3])
        assert int(victim.Hvo) in _type_member_hvos(ref_type)

        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        starting = len(_type_member_hvos(ref_type))

        ref_ops.Delete(bare_view)

        assert len(_type_member_hvos(ref_type)) == starting - 1
        assert int(hvo) not in _type_member_hvos(ref_type)
        assert int(keep.Hvo) in _type_member_hvos(ref_type)
    finally:
        for entry in (entry1, entry2, entry3):
            try:
                project.LexEntry.Delete(entry)
            except Exception:
                pass
