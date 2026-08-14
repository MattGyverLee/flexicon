#
#   test_headless_lcm_ui.py
#
#   Class: TestHeadlessLcmUISurface
#          Unit coverage for flexicon.code.headless_ui.HeadlessLcmUI (issue
#          #238 / Track A of specs/write-path-transactions).
#
#          Covers:
#            - All 12 ILcmUI members (10 methods + LastActivityTime +
#              SynchronizeInvoke) implemented and behaving non-destructively.
#            - ConflictingSave() raises FP_ConflictingSaveError and never
#              returns True.
#            - No member marshals through ISynchronizeInvoke.
#            - Regression: FLExLCM.OpenProject(name) with no ui= still
#              constructs FwLcmUI (backward compatibility).
#            - Static sweep: no "RollbackToMark" reference survives anywhere
#              under flexicon/code/ (issue #236), mirroring the pattern in
#              tests/test_custom_field_create_refusal.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pathlib

import pytest

# ---------------------------------------------------------------------------
# Live-pythonnet fixtures: HeadlessLcmUI subclasses SIL.LCModel.ILcmUI, so
# importing it requires the SIL.LCModel assembly to be loaded. The session
# fixture in tests/conftest.py already attempts this and falls back to mock
# mode on failure; skip the whole module cleanly if that fallback happened.
# ---------------------------------------------------------------------------


def _import_headless_ui():
    try:
        from flexicon.code.headless_ui import HeadlessLcmUI
        # Canonical location is flexicon.code.exceptions; headless_ui.py
        # re-imports it for backward compatibility (see headless_ui.py and
        # docs/EXCEPTION_HANDLING.md). Import from the canonical location
        # here so this test exercises the real hierarchy placement.
        from flexicon.code.exceptions import FP_ConflictingSaveError, FP_RuntimeError
        from SIL.LCModel import ILcmUI, MessageType, FileSelection, YesNoCancel
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"SIL.LCModel / HeadlessLcmUI not available: {exc}")
    return HeadlessLcmUI, FP_ConflictingSaveError, ILcmUI, MessageType, FileSelection, YesNoCancel, FP_RuntimeError


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HEADLESS_UI_SOURCE = REPO_ROOT / "flexicon" / "code" / "headless_ui.py"


# ---------------------------------------------------------------------------
# 12-member surface coverage
# ---------------------------------------------------------------------------


class TestHeadlessLcmUISurface:
    """Exercise each of the 12 ILcmUI members in isolation."""

    def test_is_real_ilcmui_instance(self):
        """HeadlessLcmUI must be a genuine .NET ILcmUI, not a Python duck-type."""
        HeadlessLcmUI, _, ILcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert isinstance(ui, ILcmUI)

    def test_conflicting_save_raises_by_default(self):
        HeadlessLcmUI, FP_ConflictingSaveError, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        with pytest.raises(FP_ConflictingSaveError):
            ui.ConflictingSave()

    def test_conflicting_save_error_is_an_fp_runtime_error(self):
        """
        Regression for the cycle-2 QC P0 finding: FP_ConflictingSaveError must
        live in the FP_* hierarchy (subclassing FP_RuntimeError) so that a
        caller doing the documented `except FP_RuntimeError` catches it too.
        It must NOT be a bare Exception subclass defined locally in
        headless_ui.py.
        """
        _, FP_ConflictingSaveError, _, _, _, _, FP_RuntimeError = _import_headless_ui()
        assert issubclass(FP_ConflictingSaveError, FP_RuntimeError)

    def test_conflicting_save_never_returns_true(self):
        """
        Even with raise_on_conflicting_save=False, ConflictingSave() must
        return False -- never True, which LCM's
        GetUserInputOnConflictingSave interprets as "discard my changes".
        """
        HeadlessLcmUI, _, *_ = _import_headless_ui()
        ui = HeadlessLcmUI(raise_on_conflicting_save=False)
        result = ui.ConflictingSave()
        assert result is False

    def test_display_message_does_not_raise(self):
        HeadlessLcmUI, _, _, MessageType, _, _, _ = _import_headless_ui()
        ui = HeadlessLcmUI()
        for level in (MessageType.Info, MessageType.Warning, MessageType.Error):
            ui.DisplayMessage(level, "a message", "a caption", "")

    def test_report_exception_returns_false(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.ReportException(Exception("boom"), True) is False
        assert ui.ReportException(Exception("boom"), False) is False

    def test_report_duplicate_guids_does_not_raise(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        ui.ReportDuplicateGuids("dup-guid-text")

    def test_display_circular_ref_breaker_report_does_not_raise(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        ui.DisplayCircularRefBreakerReport("msg", "caption")

    def test_retry_returns_false(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.Retry("msg", "caption") is False

    def test_offer_to_restore_returns_false(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.OfferToRestore("C:\\proj", "C:\\backup") is False

    def test_restore_linked_files_in_project_folder_returns_false(self):
        """
        Regression: this member was missing from the initial HeadlessLcmUI
        implementation (discovered while writing this test). Non-destructive
        branch is False -- leave linked files at their original location.
        """
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.RestoreLinkedFilesInProjectFolder() is False

    def test_cannot_restore_linked_files_returns_okno(self):
        HeadlessLcmUI, _, _, _, _, YesNoCancel, _ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.CannotRestoreLinkedFilesToOriginalLocation() == YesNoCancel.OkNo

    def test_choose_files_to_use_returns_ok_keep_newer(self):
        HeadlessLcmUI, _, _, _, FileSelection, _, _ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.ChooseFilesToUse() == FileSelection.OkKeepNewer

    def test_last_activity_time_is_a_real_timestamp(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.LastActivityTime is not None

    def test_synchronize_invoke_is_none(self):
        """
        SynchronizeInvoke must be None: nothing may marshal to a UI thread
        that does not exist in a headless process.
        """
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        assert ui.SynchronizeInvoke is None


# ---------------------------------------------------------------------------
# No member touches ISynchronizeInvoke
# ---------------------------------------------------------------------------


class TestNoSynchronizeInvokeMarshalling:
    """
    Static + runtime evidence that HeadlessLcmUI never marshals through
    ISynchronizeInvoke (the deadlock path described in issue #238).
    """

    def test_source_never_calls_invoke_or_begin_invoke(self):
        """
        No member should call .Invoke(/.BeginInvoke( -- the two entry
        points FwLcmUI uses to marshal onto a (nonexistent) UI thread.
        """
        content = HEADLESS_UI_SOURCE.read_text(encoding="utf-8")
        assert ".Invoke(" not in content
        assert ".BeginInvoke(" not in content

    def test_synchronize_invoke_property_returns_none_not_a_stub_object(self):
        HeadlessLcmUI, *_ = _import_headless_ui()
        ui = HeadlessLcmUI()
        # Explicitly not some Mock/dummy ISynchronizeInvoke implementation --
        # a real None, so any caller that tries to use it fails fast rather
        # than silently marshalling through a fake.
        assert ui.SynchronizeInvoke is None
        assert ui.get_SynchronizeInvoke() is None


# ---------------------------------------------------------------------------
# Regression: OpenProject without ui= still constructs FwLcmUI
# ---------------------------------------------------------------------------


class TestOpenProjectDefaultUi:
    """
    Regression guard for backward compatibility (A1a/A1c): FLExLCM.OpenProject
    and FLExProject.OpenProject must still hand LCM a FwLcmUI when the caller
    does not pass ui=.

    Uses a monkeypatched LcmCache.CreateCacheFromExistingData to capture the
    `ui` argument without actually opening any project (no live-LCM write,
    no real project touched).
    """

    def test_flexlcm_openproject_defaults_to_fwlcmui(self, monkeypatch):
        try:
            import flexicon.code.FLExLCM as FLExLCM_mod
            from SIL.FieldWorks.FdoUi import FwLcmUI
        except Exception as exc:  # pragma: no cover - environment-dependent
            pytest.skip(f"FLExLCM / FwLcmUI not available: {exc}")

        captured = {}

        class FakeLcmCache:
            @staticmethod
            def CreateCacheFromExistingData(projId, locale, ui, dirs, settings, dlg):
                captured["ui"] = ui
                return "FAKE_CACHE"

        monkeypatch.setattr(FLExLCM_mod, "LcmCache", FakeLcmCache)

        result = FLExLCM_mod.OpenProject("NoSuchProjectXYZ")

        assert result == "FAKE_CACHE"
        assert isinstance(captured["ui"], FwLcmUI)

    def test_flexlcm_openproject_passes_through_explicit_ui(self, monkeypatch):
        """Companion check: an explicit ui= is passed straight through, unwrapped."""
        try:
            import flexicon.code.FLExLCM as FLExLCM_mod
            from flexicon.code.headless_ui import HeadlessLcmUI
        except Exception as exc:  # pragma: no cover - environment-dependent
            pytest.skip(f"FLExLCM / HeadlessLcmUI not available: {exc}")

        captured = {}

        class FakeLcmCache:
            @staticmethod
            def CreateCacheFromExistingData(projId, locale, ui, dirs, settings, dlg):
                captured["ui"] = ui
                return "FAKE_CACHE"

        monkeypatch.setattr(FLExLCM_mod, "LcmCache", FakeLcmCache)

        headless = HeadlessLcmUI()
        result = FLExLCM_mod.OpenProject("NoSuchProjectXYZ", ui=headless)

        assert result == "FAKE_CACHE"
        assert captured["ui"] is headless

    def test_flexproject_openproject_signature_accepts_ui_kwarg(self):
        """
        FLExProject.OpenProject must accept a `ui=` keyword (A1c). Verified
        via inspect.signature rather than a live open, since the latter
        requires a real project.
        """
        import inspect

        try:
            from flexicon.code.FLExProject import FLExProject
        except Exception as exc:  # pragma: no cover - environment-dependent
            pytest.skip(f"FLExProject not available: {exc}")

        sig = inspect.signature(FLExProject.OpenProject)
        params = sig.parameters
        assert "ui" in params
        assert params["ui"].default is None


# ---------------------------------------------------------------------------
# Static sweep: no RollbackToMark reference survives in flexicon/code/
# ---------------------------------------------------------------------------


class TestNoRollbackToMarkReferenceSurvives:
    """
    Regression for issue #236 (mirrors tests/test_custom_field_create_refusal.py's
    string-level pattern): RollbackToMark does not exist anywhere in liblcm or
    FieldWorks, so no source file under flexicon/code/ may reference it, in
    code or in a docstring/comment.
    """

    CODE_ROOT = REPO_ROOT / "flexicon" / "code"

    # Fragility note (cycle-2 QC P1/Q3): this is a literal string sweep for
    # "RollbackToMark". It catches today's known-absent API being referenced
    # again, but it is blind to the same capability resurfacing under a
    # different name (e.g. if a future liblcm version exposes rollback via a
    # differently-named method/property). If that happens, this test will
    # stay green while the docstrings' "no rollback API exists" claims go
    # stale -- re-verify by reflection (see specs/write-path-transactions/
    # spec.md D1) rather than trusting this sweep alone.
    def test_no_rollbacktomark_string_anywhere_in_flexicon_code(self):
        offenders = []
        for path in self.CODE_ROOT.rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            if "RollbackToMark" in content:
                offenders.append(str(path.relative_to(REPO_ROOT)))

        assert offenders == [], (
            "RollbackToMark does not exist anywhere in liblcm or FieldWorks "
            "(issue #236); it must not be referenced in flexicon/code/. "
            f"Found in: {offenders}"
        )

    def test_get_transaction_api_method_is_gone(self):
        """
        FLExProject._GetTransactionAPI performed fictional Mark/RollbackToMark
        discovery and always returned (None, None). It has been removed
        outright rather than reduced to a stub.
        """
        try:
            from flexicon.code.FLExProject import FLExProject
        except Exception as exc:  # pragma: no cover - environment-dependent
            pytest.skip(f"FLExProject not available: {exc}")

        assert not hasattr(FLExProject, "_GetTransactionAPI")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
