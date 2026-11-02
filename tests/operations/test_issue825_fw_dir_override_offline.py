#
#   test_issue825_fw_dir_override_offline.py
#
#   Offline tests for the FLEXICON_FW_DIR override of the FieldWorks
#   location (issue #825).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code import FLExGlobals


@pytest.fixture
def fake_fw(tmp_path):
    for dll in FLExGlobals.FW_REQUIRED_DLLS:
        (tmp_path / dll).write_bytes(b"")
    return tmp_path


class TestFWDirOverride:
    def test_unset_returns_none(self, monkeypatch):
        monkeypatch.delenv(FLExGlobals.FW_DIR_ENV_VAR, raising=False)
        assert FLExGlobals.GetFWDirOverride() is None

    def test_blank_returns_none(self, monkeypatch):
        monkeypatch.setenv(FLExGlobals.FW_DIR_ENV_VAR, "   ")
        assert FLExGlobals.GetFWDirOverride() is None

    def test_valid_dir_is_returned(self, monkeypatch, fake_fw):
        monkeypatch.setenv(FLExGlobals.FW_DIR_ENV_VAR, str(fake_fw))
        assert FLExGlobals.GetFWDirOverride() == str(fake_fw)

    def test_quoted_value_is_accepted(self, monkeypatch, fake_fw):
        monkeypatch.setenv(FLExGlobals.FW_DIR_ENV_VAR, '"%s"' % fake_fw)
        assert FLExGlobals.GetFWDirOverride() == str(fake_fw)

    def test_missing_dir_raises_clear_error(self, monkeypatch, tmp_path):
        monkeypatch.setenv(FLExGlobals.FW_DIR_ENV_VAR, str(tmp_path / "nope"))
        with pytest.raises(Exception, match="FLEXICON_FW_DIR.*not an existing directory"):
            FLExGlobals.GetFWDirOverride()

    def test_dir_without_dlls_raises_clear_error(self, monkeypatch, tmp_path):
        monkeypatch.setenv(FLExGlobals.FW_DIR_ENV_VAR, str(tmp_path))
        with pytest.raises(Exception, match="SIL.LCModel.dll"):
            FLExGlobals.GetFWDirOverride()
