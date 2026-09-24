#
#   test_352_annodef_live.py
#
#   Live regression coverage for issue #352 (AnnotationDef face):
#   ICmAnnotationDefn has no HelpString/Prompt members -- both are
#   surfaced from the inherited Description field.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

pytestmark = pytest.mark.requires_live_project


def _make_def(op, name):
    # The CmAnnotationType enum is not exposed via pythonnet in this env;
    # Create() only applies it behind a hasattr guard anyway, so pass 0.
    return op.Create(name, 0)


class Test352AnnoDefHelpPrompt:
    @pytest.mark.live_phase("AnnotationDefOperations", "read")
    def test_no_backing_field(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = _make_def(op, "TEST_352 shapes")
        try:
            assert not hasattr(d, "HelpString")
            assert not hasattr(d, "Prompt")
            assert hasattr(d, "Description")
        finally:
            op.Delete(d)

    @pytest.mark.live_phase("AnnotationDefOperations", "add")
    def test_help_prompt_roundtrip(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = _make_def(op, "TEST_352 help")
        try:
            assert op.GetHelpString(d) == ""
            op.SetHelpString(d, "TEST_352 help text")
            assert op.GetHelpString(d) == "TEST_352 help text"
            op.SetPrompt(d, "TEST_352 prompt text")
            assert op.GetPrompt(d) == "TEST_352 prompt text"
            props = op.GetSyncableProperties(d)
            assert props["HelpString"] == "TEST_352 prompt text"
            assert props["Prompt"] == "TEST_352 prompt text"
            assert "AnnotationType" not in props
            # GSP reads ICmAnnotationDefn.Multi, which is False on a fresh
            # definition -- compare against the value read back from LCM.
            from SIL.LCModel import ICmAnnotationDefn

            assert props["AllowsMultiple"] is bool(ICmAnnotationDefn(d).Multi)
            assert "InstanceOf" in props
            assert "AllowsInstanceOf" in props
        finally:
            op.Delete(d)

    @pytest.mark.live_phase("AnnotationDefOperations", "add")
    def test_duplicate_conserves_description(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        d = _make_def(op, "TEST_352 duphelp")
        try:
            op.SetHelpString(d, "TEST_352 conserved")
            dup = op.Duplicate(d)
            try:
                assert op.GetHelpString(dup) == "TEST_352 conserved"
            finally:
                op.Delete(dup)
        finally:
            op.Delete(d)
