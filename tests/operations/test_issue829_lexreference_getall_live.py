#
#   test_issue829_lexreference_getall_live.py
#
#   Live verification for issue #829: LexReferences.GetAll.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_829_"


def _walk_member_hvos(project):
    """Independent walk of ReferencesOA -> MembersOC."""
    from SIL.LCModel import ILexRefType

    hvos = set()
    stack = list(project.lexDB.ReferencesOA.PossibilitiesOS)
    while stack:
        rt = ILexRefType(stack.pop())
        hvos.update(int(r.Hvo) for r in rt.MembersOC)
        stack.extend(rt.SubPossibilitiesOS)
    return hvos


def test_issue829_getall_matches_membersoc_walk_sena3(sena3_sandbox):
    project = sena3_sandbox
    got = {int(r.Hvo) for r in project.LexReferences.GetAll()}
    expected = _walk_member_hvos(project)
    print(f"[INFO] GetAll={len(got)} MembersOC walk={len(expected)}")
    assert got, "Sena 3 should contain lexical references"
    assert got == expected


def test_issue829_getall_sense_entry_and_project_target(target_sandbox):
    project = target_sandbox
    ops = project.LexReferences
    e1 = project.LexEntry.Create(f"{TEST_PREFIX}a")
    e2 = project.LexEntry.Create(f"{TEST_PREFIX}b")
    s1 = project.Senses.Create(e1, f"{TEST_PREFIX}gloss_a")
    s2 = project.Senses.Create(e2, f"{TEST_PREFIX}gloss_b")
    ref_type = ops.CreateType(f"{TEST_PREFIX}Synonym", "Symmetric")
    ref = ops.Create(ref_type, [s1, s2])
    hvo = int(ref.Hvo)
    refetched = project.Object(hvo)
    assert int(refetched.Hvo) == hvo

    assert hvo in {int(r.Hvo) for r in ops.GetAll(s1)}
    assert hvo in {int(r.Hvo) for r in ops.GetAll(s2)}
    assert hvo in {int(r.Hvo) for r in ops.GetAll(e1)}
    assert hvo in {int(r.Hvo) for r in ops.GetAll(e2)}
    assert hvo in {int(r.Hvo) for r in ops.GetAll()}
    assert {int(r.Hvo) for r in ops.GetAll()} == _walk_member_hvos(project)


def test_issue829_getall_entry_level_reference(target_sandbox):
    project = target_sandbox
    ops = project.LexReferences
    e1 = project.LexEntry.Create(f"{TEST_PREFIX}c")
    e2 = project.LexEntry.Create(f"{TEST_PREFIX}d")
    ref_type = ops.CreateType(f"{TEST_PREFIX}EntryRel", "Symmetric")
    ref = ops.Create(ref_type, [e1, e2])
    hvo = int(ref.Hvo)
    assert hvo in {int(r.Hvo) for r in ops.GetAll(e1)}
    assert hvo in {int(r.Hvo) for r in ops.GetAll(e2)}
    assert hvo in {int(r.Hvo) for r in ops.GetAll()}
