#
#   test_headless_threaded_progress.py
#
#   Class: TestHeadlessThreadedProgressSurface
#          Unit coverage for HeadlessThreadedProgress and OpenProject progress=
#          default (issue #289).
#
#   Platform: Python.NET (skipped when SIL.LCModel unavailable)
#

from pathlib import Path

import inspect
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FLEXLCM_SOURCE = REPO_ROOT / "flexicon" / "code" / "FLExLCM.py"


def _import_headless_progress():
    # Skip only when the LCM itself is absent. A failure inside flexicon's own
    # import must fail the test: a blanket skip here hid a broken
    # `import flexicon` (pythonnet cannot emit IProgress.Canceling) behind a
    # green run.
    try:
        import flexicon  # noqa: F401 -- initialises the FieldWorks paths
    except ImportError as exc:  # pragma: no cover - environment-dependent
        if "SIL" not in str(exc) and "clr" not in str(exc):
            raise
        pytest.skip(f"SIL.LCModel not available: {exc}")
    from flexicon.code.headless_ui import HeadlessThreadedProgress
    from SIL.LCModel.Utils import IThreadedProgress

    return HeadlessThreadedProgress, IThreadedProgress


def _task_delegate(fn):
    """Wrap fn as the Func<IThreadedProgress, object[], object> LCM passes."""
    from System import Array, Func, Object
    from SIL.LCModel.Utils import IThreadedProgress

    return Func[IThreadedProgress, Array[Object], Object](fn)


class TestHeadlessThreadedProgressSurface:
    def test_is_genuine_ithreadedprogress(self):
        HeadlessThreadedProgress, IThreadedProgress = _import_headless_progress()
        progress = HeadlessThreadedProgress()
        assert isinstance(progress, IThreadedProgress)

    def test_run_task_executes_synchronously(self):
        HeadlessThreadedProgress, _ = _import_headless_progress()
        progress = HeadlessThreadedProgress()
        seen = []

        def task(prog, args):
            seen.append((prog, list(args)))
            return "task-result"

        # IThreadedProgress.RunTask returns the task's own result.
        assert progress.RunTask(_task_delegate(task), ["a", "b"]) == "task-result"
        assert len(seen) == 1
        assert seen[0][1] == ["a", "b"]

    def test_run_task_three_arg_overload_runs_on_caller_thread(self):
        import threading

        HeadlessThreadedProgress, _ = _import_headless_progress()
        progress = HeadlessThreadedProgress()
        caller = threading.get_ident()
        ran_on = []

        def task(prog, args):
            ran_on.append(threading.get_ident())
            return 42

        assert progress.RunTask(True, _task_delegate(task), []) == 42
        assert ran_on == [caller]

    def test_canceling_event_accepts_handlers(self):
        from System.ComponentModel import CancelEventHandler

        HeadlessThreadedProgress, _ = _import_headless_progress()
        progress = HeadlessThreadedProgress()
        handler = CancelEventHandler(lambda sender, e: None)
        progress.Canceling += handler
        progress.Canceling -= handler

    def test_is_canceling_defaults_false(self):
        HeadlessThreadedProgress, _ = _import_headless_progress()
        progress = HeadlessThreadedProgress()
        assert progress.IsCanceling is False
        assert progress.Canceled is False

    def test_synchronize_invoke_is_none(self):
        HeadlessThreadedProgress, _ = _import_headless_progress()
        progress = HeadlessThreadedProgress()
        assert progress.SynchronizeInvoke is None


class TestOpenProjectDefaultProgress:
    def test_flexlcm_openproject_defaults_to_headless_threaded_progress(
        self, monkeypatch
    ):
        try:
            import flexicon.code.FLExLCM as FLExLCM_mod
            from flexicon.code.headless_ui import HeadlessThreadedProgress
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"FLExLCM not available: {exc}")

        captured = {}

        class FakeLcmCache:
            @staticmethod
            def CreateCacheFromExistingData(
                projId, locale, ui, dirs, settings, progress
            ):
                captured["progress"] = progress
                return "FAKE_CACHE"

        monkeypatch.setattr(FLExLCM_mod, "LcmCache", FakeLcmCache)

        result = FLExLCM_mod.OpenProject("NoSuchProjectXYZ")

        assert result == "FAKE_CACHE"
        assert isinstance(captured["progress"], HeadlessThreadedProgress)

    def test_flexlcm_openproject_passes_through_explicit_progress(self, monkeypatch):
        try:
            import flexicon.code.FLExLCM as FLExLCM_mod
            from flexicon.code.headless_ui import HeadlessThreadedProgress
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"FLExLCM not available: {exc}")

        captured = {}
        explicit = HeadlessThreadedProgress()

        class FakeLcmCache:
            @staticmethod
            def CreateCacheFromExistingData(
                projId, locale, ui, dirs, settings, progress
            ):
                captured["progress"] = progress
                return "FAKE_CACHE"

        monkeypatch.setattr(FLExLCM_mod, "LcmCache", FakeLcmCache)

        FLExLCM_mod.OpenProject("NoSuchProjectXYZ", progress=explicit)

        assert captured["progress"] is explicit

    def test_flexlcm_disposes_progress_dialog_with_task(self, monkeypatch):
        try:
            import flexicon.code.FLExLCM as FLExLCM_mod
            from SIL.FieldWorks.Common.Controls import ProgressDialogWithTask
            from SIL.FieldWorks.Common.FwUtils import ThreadHelper
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"ProgressDialogWithTask not available: {exc}")

        disposed = []

        class TrackingDialog(ProgressDialogWithTask):
            def __init__(self, th):
                super().__init__(th)

            def Dispose(self):
                disposed.append(True)
                super().Dispose()

        class FakeLcmCache:
            @staticmethod
            def CreateCacheFromExistingData(
                projId, locale, ui, dirs, settings, progress
            ):
                return "FAKE_CACHE"

        monkeypatch.setattr(FLExLCM_mod, "LcmCache", FakeLcmCache)

        dlg = TrackingDialog(ThreadHelper())
        FLExLCM_mod.OpenProject("NoSuchProjectXYZ", progress=dlg)

        assert disposed == [True]

    def test_flexproject_openproject_signature_accepts_progress_kwarg(self):
        try:
            from flexicon.code.FLExProject import FLExProject
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"FLExProject not available: {exc}")

        sig = inspect.signature(FLExProject.OpenProject)
        assert "progress" in sig.parameters
        assert sig.parameters["progress"].default is None


class TestOpenProjectProgressSourceRatchet:
    def test_openproject_does_not_unconditionally_construct_progress_dialog(self):
        content = FLEXLCM_SOURCE.read_text(encoding="utf-8")
        assert "ProgressDialogWithTask(th)" not in content
        assert "HeadlessThreadedProgress()" in content
