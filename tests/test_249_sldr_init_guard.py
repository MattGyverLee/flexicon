#
#   test_249_sldr_init_guard.py
#
#   Module: Offline unit coverage for the SLDR init/cleanup guard in
#           flexicon.code.FLExInit (issue #249).
#
#   These tests run WITHOUT FieldWorks doing any real work: every CLR
#   touchpoint that FLExInitialize()/FLExCleanup() reach is replaced by a
#   plain-Python double. They are deliberately NOT marked
#   requires_live_project -- the live counterpart lives in
#   tests/operations/test_249_sldr_init_live.py.
#
#   Why the doubles are bound on the FLExInit module and not on the CLR
#   types themselves: `SIL.WritingSystems` (like `SIL.LCModel`) is a CLR
#   namespace and REJECTS monkeypatch.setattr, so `Sldr.IsInitialized`
#   cannot be patched in place. What is patchable is the *name* `Sldr`
#   bound in FLExInit's module globals, which is what the production code
#   actually dereferences. Recorded in
#   specs/feature-structure-sync-gap/spec.md:559-561.
#
#   The fake System.InvalidOperationException follows the precedent in
#   tests/write_path_transactions/test_a3_abort_session.py:61 -- a plain
#   Python exception class standing in for a CLR exception, carrying the
#   `.Message` property the production `except` block reads.
#
#   Platform: Python (no FieldWorks required)
#
#   Copyright 2026
#

import pytest

from flexicon.code import FLExInit


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------
#
# Facts modeled, each from live reflection against SIL.WritingSystems
# 18.0.0.0 / FieldWorks 9.3.10:
#
#   * Sldr.IsInitialized is a public static bool getter. Safe to read cold,
#     returns False before init, never throws.
#   * A second Sldr.Initialize(True) throws
#     System.InvalidOperationException, Message exactly
#     "The SLDR has already been initialized."
#   * Sldr.Cleanup() while cold throws System.InvalidOperationException,
#     Message exactly "The SLDR has not been initialized."


class FakeClrInvalidOperationError(Exception):
    """Stand-in for System.InvalidOperationException.

    The production code reads `e.Message`, which is the CLR property name,
    not the Python `str(e)`; the double therefore exposes both.
    """

    def __init__(self, message):
        super().__init__(message)
        self.Message = message


class FakeSystemNamespace:
    """Minimal stand-in for the `System` CLR namespace module.

    Only the one attribute FLExInit dereferences is provided, so a
    production change that started catching some other System exception
    would fail loudly here rather than pass silently.
    """

    InvalidOperationException = FakeClrInvalidOperationError


class FakeSldr:
    """Plain-Python double for the parts of Sldr that FLExInit touches."""

    def __init__(self, is_initialized=False, initialize_raises=None,
                 cleanup_raises=None):
        self._is_initialized = is_initialized
        self._initialize_raises = initialize_raises
        self._cleanup_raises = cleanup_raises
        self.initialize_calls = []      # offlineTestMode args actually passed
        self.cleanup_calls = 0

    @property
    def IsInitialized(self):
        """Get-only on the real type."""
        return self._is_initialized

    def Initialize(self, offlineTestMode):
        self.initialize_calls.append(offlineTestMode)
        if self._initialize_raises is not None:
            raise self._initialize_raises
        self._is_initialized = True

    def Cleanup(self):
        self.cleanup_calls += 1
        if self._cleanup_raises is not None:
            raise self._cleanup_raises
        self._is_initialized = False


class FakeFwRegistryHelper:
    def __init__(self):
        self.calls = 0

    def Initialize(self):
        self.calls += 1


class FakeFwUtils:
    def __init__(self):
        self.calls = 0

    def InitializeIcu(self):
        self.calls += 1


@pytest.fixture
def patched_flexinit(monkeypatch):
    """Neutralize every CLR touchpoint except Sldr, which each test binds.

    Returns a callable: install(sldr) -> the FakeSldr, so a test can build
    its own Sldr double and have it bound into FLExInit's globals.
    """
    monkeypatch.setattr(FLExInit, "FwRegistryHelper", FakeFwRegistryHelper())
    monkeypatch.setattr(FLExInit, "FwUtils", FakeFwUtils())
    # raising=False so this fixture cannot mask a behavioural regression as a
    # setup ERROR. If a future edit drops `import System` from FLExInit, the
    # discrimination tests must still RUN and fail on the swallowed
    # exception -- which is the actual #249 defect -- rather than erroring
    # here on a missing attribute and reporting nothing about behaviour.
    monkeypatch.setattr(FLExInit, "System", FakeSystemNamespace, raising=False)

    def install(sldr):
        monkeypatch.setattr(FLExInit, "Sldr", sldr)
        return sldr

    return install


# ---------------------------------------------------------------------------
# FLExInitialize()
# ---------------------------------------------------------------------------


class TestFLExInitializeProbesBeforeInitializing:
    """The IsInitialized probe decides whether Initialize() is called."""

    def test_cold_sldr_is_initialized_once_in_offline_mode(self, patched_flexinit):
        """IsInitialized False -> Initialize called exactly once with True."""
        sldr = patched_flexinit(FakeSldr(is_initialized=False))

        FLExInit.FLExInitialize()

        assert sldr.initialize_calls == [True], (
            "Expected exactly one Sldr.Initialize(True) call (offlineTestMode "
            f"must be True so no network SLDR access is attempted); got "
            f"{sldr.initialize_calls!r}"
        )
        assert sldr.IsInitialized is True

    def test_already_initialized_sldr_is_not_reinitialized(self, patched_flexinit):
        """IsInitialized True -> Initialize is NOT called at all.

        Repeated FLExInitialize() must be a genuine no-op: per-test setUp
        in flexicon/tests/test_CustomFields.py:37-38 calls it after the
        session fixture has already brought the SLDR up.
        """
        sldr = patched_flexinit(FakeSldr(is_initialized=True))

        FLExInit.FLExInitialize()

        assert sldr.initialize_calls == [], (
            "Sldr.Initialize() was called even though IsInitialized was "
            "already True -- repeated FLExInitialize() is no longer idempotent."
        )
        assert sldr.IsInitialized is True

    def test_repeated_calls_initialize_only_once(self, patched_flexinit):
        """Two back-to-back FLExInitialize() calls yield one Initialize()."""
        sldr = patched_flexinit(FakeSldr(is_initialized=False))

        FLExInit.FLExInitialize()
        FLExInit.FLExInitialize()

        assert sldr.initialize_calls == [True]


class TestFLExInitializeExceptionDiscrimination:
    """The `except` block must discriminate benign races from real failures."""

    def test_race_with_already_initialized_message_is_swallowed(self, patched_flexinit):
        """Probe says False but Initialize() reports already-initialized.

        Initialize()/Cleanup() serialize on a private lock, so another
        thread can win between the probe and the call. That exact message
        is the only tolerable InvalidOperationException.
        """
        sldr = patched_flexinit(
            FakeSldr(
                is_initialized=False,
                initialize_raises=FakeClrInvalidOperationError(
                    "The SLDR has already been initialized."
                ),
            )
        )

        # Must not raise.
        FLExInit.FLExInitialize()

        assert sldr.initialize_calls == [True]

    def test_real_invalid_operation_failure_propagates(self, patched_flexinit):
        """REGRESSION PIN FOR #249.

        An InvalidOperationException whose message is anything other than
        "already been initialized" is a genuine SLDR failure (dll load,
        cache path, permissions). Before the fix a bare `except Exception`
        downgraded it to a warning, the SLDR stayed down for the whole
        process, and every later LDML read threw "The SLDR has not been
        initialized" -- at which point liblcm renamed the project's .ldml
        files to .ldml.bad and re-synthesized writing systems from
        defaults, on every open, forever. It must reach the caller.
        """
        boom = FakeClrInvalidOperationError(
            "The SLDR cache directory could not be created."
        )
        sldr = patched_flexinit(
            FakeSldr(is_initialized=False, initialize_raises=boom)
        )

        with pytest.raises(FakeClrInvalidOperationError) as excinfo:
            FLExInit.FLExInitialize()

        assert excinfo.value is boom, (
            "FLExInitialize() must re-raise the original exception object, "
            "not wrap or replace it."
        )
        assert sldr.initialize_calls == [True]

    @pytest.mark.parametrize(
        "exc",
        [
            RuntimeError("SLDR dll not found"),
            OSError("access denied writing SLDR cache"),
            ValueError("bad offlineTestMode"),
        ],
        ids=["runtime", "os", "value"],
    )
    def test_non_invalid_operation_failure_propagates(self, patched_flexinit, exc):
        """Anything that is not an InvalidOperationException propagates too.

        The `except` clause is narrow by design; there is no bare
        `except Exception` left to absorb these.
        """
        sldr = patched_flexinit(
            FakeSldr(is_initialized=False, initialize_raises=exc)
        )

        with pytest.raises(type(exc)) as excinfo:
            FLExInit.FLExInitialize()

        assert excinfo.value is exc
        assert sldr.initialize_calls == [True]


# ---------------------------------------------------------------------------
# FLExCleanup()
# ---------------------------------------------------------------------------


class TestFLExCleanupIsTolerantOfColdSldr:
    """Cleanup is teardown: it must tolerate already being done."""

    def test_cold_sldr_skips_cleanup_without_raising(self, patched_flexinit):
        """IsInitialized False -> Sldr.Cleanup() is not called, no raise.

        The real Sldr.Cleanup() throws InvalidOperationException("The SLDR
        has not been initialized.") when cold, so an unguarded call made
        FLExCleanup() raise whenever FLExInitialize() had never run or
        cleanup ran twice.
        """
        sldr = patched_flexinit(
            FakeSldr(
                is_initialized=False,
                cleanup_raises=FakeClrInvalidOperationError(
                    "The SLDR has not been initialized."
                ),
            )
        )

        FLExInit.FLExCleanup()

        assert sldr.cleanup_calls == 0, (
            "Sldr.Cleanup() was called on a cold SLDR -- the IsInitialized "
            "guard is not protecting the teardown path."
        )

    def test_warm_sldr_is_cleaned_up_once(self, patched_flexinit):
        """IsInitialized True -> Sldr.Cleanup() called exactly once."""
        sldr = patched_flexinit(FakeSldr(is_initialized=True))

        FLExInit.FLExCleanup()

        assert sldr.cleanup_calls == 1
        assert sldr.IsInitialized is False

    def test_double_cleanup_does_not_raise(self, patched_flexinit):
        """Two FLExCleanup() calls: the second is a guarded no-op."""
        sldr = patched_flexinit(
            FakeSldr(
                is_initialized=True,
                cleanup_raises=None,
            )
        )

        FLExInit.FLExCleanup()
        # Second call sees IsInitialized False and must short-circuit.
        FLExInit.FLExCleanup()

        assert sldr.cleanup_calls == 1


class TestInitCleanupCycle:
    """Init -> cleanup -> init must be expressible through the guards."""

    def test_full_cycle_reinitializes(self, patched_flexinit):
        sldr = patched_flexinit(FakeSldr(is_initialized=False))

        FLExInit.FLExInitialize()
        assert sldr.IsInitialized is True

        FLExInit.FLExCleanup()
        assert sldr.IsInitialized is False
        assert sldr.cleanup_calls == 1

        FLExInit.FLExInitialize()
        assert sldr.IsInitialized is True
        assert sldr.initialize_calls == [True, True]
