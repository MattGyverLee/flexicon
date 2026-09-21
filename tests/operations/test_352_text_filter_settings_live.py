#
#   test_352_text_filter_settings_live.py
#
#   Live regression coverage for issue #352 (Text/Filter/Settings faces):
#   IText has no Title/Description; title_pattern matches Name; the
#   project name is the read-only ShortName.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


class Test352TextNoTitle:
    @pytest.mark.live_phase("TextOperations", "add")
    def test_duplicate_without_title(self, target_sandbox):
        texts = target_sandbox.Texts
        text = texts.Create("TEST_352 story")
        try:
            # Title is absent (issue #352); Description IS present live
            # (inherited multistring the declared-only snapshot missed).
            assert not hasattr(text, "Title")
            assert hasattr(text, "Description")
            dup = texts.Duplicate(text)
            try:
                props = texts.GetSyncableProperties(dup)
                assert "Title" not in props
            finally:
                texts.Delete(dup)
        finally:
            texts.Delete(text)

    @pytest.mark.live_phase("FilterOperations", "read")
    def test_title_pattern_matches_name(self, target_sandbox):
        texts = target_sandbox.Texts
        text = texts.Create("TEST_352 story")
        try:
            filt = target_sandbox.Filters
            assert filt._MatchTextCriteria(text, {"title_pattern": "TEST_352"})
            assert not filt._MatchTextCriteria(text, {"title_pattern": "ZZZ_NOPE"})
        finally:
            texts.Delete(text)


class Test352ProjectName:
    @pytest.mark.live_phase("ProjectSettingsOperations", "read")
    def test_project_name_is_shortname(self, target_sandbox):
        settings = target_sandbox.ProjectSettings
        name = settings.GetProjectName()
        assert isinstance(name, str) and name != ""

    @pytest.mark.live_phase("ProjectSettingsOperations", "read")
    def test_set_project_name_raises_actionable(self, target_sandbox):
        with pytest.raises(FP_ParameterError, match="352"):
            target_sandbox.ProjectSettings.SetProjectName("New Name")
