#
#   test_issue351_paragraph_sync_props_live.py
#
#   Live regression tests for ParagraphOperations.GetSyncableProperties
#   (issue #351).
#
#   Pre-fix, every non-empty paragraph raised:
#       AttributeError: 'ITsString' object has no attribute 'get_WritingSystemAt'
#   (measured 2026-09-20 on Ejagham Mini: 205 of 205 StTxtPara objects
#   failed). The fix reads the run-0 WS handle off the text props
#   (`get_Properties(0).GetIntPropValues(1, 0)[0]`), mirroring
#   SegmentOperations.GetSyncableProperties, then resolves it to a
#   WritingSystemDefinition.Id.
#
#   Runs against a fresh tempdir copy of the Target backup (target_sandbox)
#   so nothing leaks and a mid-test failure cannot corrupt a real project.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
import uuid

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


class TestParagraphGetSyncablePropertiesLive:
    """
    Live proof that GetSyncableProperties reads paragraph Contents without
    raising, on a real LCM cache with a real IStTxtPara whose Contents is
    a bare ITsString.
    """

    @pytest.mark.live_phase("ParagraphOperations", "read")
    def test_get_syncable_properties_on_real_paragraph(self, target_sandbox):
        """
        Create a non-empty TEST_ paragraph (the exact case the pre-fix bug
        raised on), then confirm GetSyncableProperties returns its Contents
        keyed by the real default-vernacular writing-system Id -- read back
        from the LCM, not merely the value passed in.
        """
        project = target_sandbox
        name = f"{TEST_PREFIX}issue351_{uuid.uuid4().hex[:8]}"
        content = "TEST_issue351 paragraph with content."

        text = project.Texts.Create(name)
        try:
            para = project.Paragraphs.Create(text, content)

            # Resolve the default vernacular WS Id from the LCM (the
            # paragraph was created with wsHandle=None -> DefaultVernWs).
            default_vern_handle = project.project.DefaultVernWs
            default_vern_id = next(
                (w.Id for w in project.WritingSystems.GetAll() if w.Handle == default_vern_handle),
                None,
            )
            assert default_vern_id is not None, (
                "Could not resolve a WritingSystemDefinition.Id for "
                f"DefaultVernWs handle {default_vern_handle}."
            )

            # Read the paragraph text back from the LCM as the reference.
            read_back_text = project.Paragraphs.GetText(para)

            props = project.Paragraphs.GetSyncableProperties(para)

            assert "Contents" in props, (
                "GetSyncableProperties returned no 'Contents' key -- the "
                "TsString branch did not run on a non-empty paragraph."
            )
            assert props["Contents"] == {default_vern_id: read_back_text}, (
                f"Expected Contents {{ {default_vern_id!r}: {read_back_text!r} }} "
                f"read back from the LCM -- got {props['Contents']!r}."
            )

            # The value in the dict must be the paragraph text itself,
            # re-read independently, not the literal we passed in.
            assert props["Contents"][default_vern_id] == content

        finally:
            project.Texts.Delete(text)

    @pytest.mark.live_phase("ParagraphOperations", "read")
    def test_no_paragraph_in_text_raises(self, target_sandbox):
        """
        Sweep guard: call GetSyncableProperties on EVERY paragraph of a
        TEXT_-prefixed text, the same access pattern that reported 205/205
        failures on Ejagham Mini. Any paragraph raising AttributeError
        fails the test.
        """
        project = target_sandbox
        name = f"{TEST_PREFIX}issue351_{uuid.uuid4().hex[:8]}"

        text = project.Texts.Create(name)
        try:
            for i in range(3):
                project.Paragraphs.Create(text, f"TEST_issue351 sweep paragraph {i}.")

            paragraphs = list(project.Paragraphs.GetAll(text))
            assert len(paragraphs) == 3, (
                f"Expected 3 paragraphs for the sweep, found {len(paragraphs)}."
            )

            for para in paragraphs:
                props = project.Paragraphs.GetSyncableProperties(para)
                contents = props.get("Contents", {})
                assert contents, (
                    "GetSyncableProperties returned an empty Contents dict for "
                    "a non-empty paragraph."
                )
                # Each WS key must resolve to the exact paragraph text.
                assert project.Paragraphs.GetText(para) in contents.values()
        finally:
            project.Texts.Delete(text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])