#
#   test_annodef_phantom_members_live.py
#
#   Live regression coverage for the AnnotationDefOperations phantom
#   members left behind by issue #361: GetMultiple / SetMultiple probed
#   AllowsMultiple, GetCopyCutPasteAllowed probed CopyCutPasteAllowed,
#   GetInstanceOf probed InstanceOf, and Duplicate copied all three.
#   None of those exist on ICmAnnotationDefn; the real fields are Multi,
#   CopyCutPastable and InstanceOfSignature (live reflection, 2026-09-23).
#
#   Every assertion re-reads the field from a fresh ICmAnnotationDefn
#   view obtained by GUID, not from the value passed in.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def _reread(project, anno_def):
    """Re-query the definition by GUID and cast to ICmAnnotationDefn."""
    from SIL.LCModel import ICmAnnotationDefn

    return ICmAnnotationDefn(project.Object(anno_def.Guid))


class TestAnnoDefMultiLive:
    @pytest.mark.live_phase("AnnotationDefOperations", "modify")
    def test_set_multiple_reaches_lcm_both_ways(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = op.Create("TEST_multi", 0)
        try:
            pre = bool(_reread(target_sandbox, d).Multi)
            assert op.GetMultiple(d) is pre

            op.SetMultiple(d, not pre)
            assert bool(_reread(target_sandbox, d).Multi) is (not pre)
            assert op.GetMultiple(d) is (not pre)

            op.SetMultiple(d, pre)
            assert bool(_reread(target_sandbox, d).Multi) is pre
            assert op.GetMultiple(d) is pre
        finally:
            op.Delete(d)

    @pytest.mark.live_phase("AnnotationDefOperations", "read")
    def test_get_multiple_accepts_hvo(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = op.Create("TEST_multi_hvo", 0)
        try:
            for value in (True, False):
                op.SetMultiple(d.Hvo, value)
                assert bool(_reread(target_sandbox, d).Multi) is value
                assert op.GetMultiple(d.Hvo) is value
        finally:
            op.Delete(d)

    @pytest.mark.live_phase("AnnotationDefOperations", "read")
    def test_copy_cut_paste_and_instance_of_read_real_fields(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = op.Create("TEST_ccp", 0)
        try:
            raw = _reread(target_sandbox, d)
            for value in (True, False):
                with target_sandbox.Transaction("TEST set CopyCutPastable"):
                    raw.CopyCutPastable = value
                assert op.GetCopyCutPasteAllowed(d) is value
            assert op.GetInstanceOf(d) == int(_reread(target_sandbox, d).InstanceOfSignature)
        finally:
            op.Delete(d)


class TestAnnoDefDuplicateFlagsLive:
    @pytest.mark.live_phase("AnnotationDefOperations", "add")
    def test_duplicate_preserves_multi_and_flags(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = op.Create("TEST_dupflags", 0)
        try:
            src = _reread(target_sandbox, d)
            # Flip every scalar away from its fresh default so a copy that
            # silently skips a field is caught.
            want_multi = not bool(src.Multi)
            want_ccp = not bool(src.CopyCutPastable)
            want_ucc = not bool(src.UserCanCreate)
            op.SetMultiple(d, want_multi)
            op.SetUserCanCreate(d, want_ucc)
            with target_sandbox.Transaction("TEST flip CopyCutPastable"):
                src.CopyCutPastable = want_ccp

            dup = op.Duplicate(d)
            try:
                got = _reread(target_sandbox, dup)
                assert got.Guid != src.Guid
                assert bool(got.Multi) is want_multi
                assert bool(got.CopyCutPastable) is want_ccp
                assert bool(got.UserCanCreate) is want_ucc
                assert int(got.InstanceOfSignature) == int(src.InstanceOfSignature)
                assert bool(got.AllowsInstanceOf) is bool(src.AllowsInstanceOf)
            finally:
                op.Delete(dup)
        finally:
            op.Delete(d)
