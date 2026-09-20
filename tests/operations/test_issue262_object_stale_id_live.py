#
#   test_issue262_object_stale_id_live.py
#
#   Live LCM verification for issue #262: FLExProject.Object(hvoOrGuid)
#   used to leak the raw CLR
#   System.Collections.Generic.KeyNotFoundException when hvoOrGuid was
#   well-formed but stale. The fix (commit a2feff1) wraps the
#   ServiceLocator.GetObject() call and re-raises FP_ParameterError,
#   preserving the original CLR exception as __cause__.
#
#   This file discharges the "Probes to discharge" list in
#   specs/262-object-not-found/HANDOFF.md section 4. It is deliberately
#   NOT merged into the existing offline test_issue262_object_stale_id.py
#   -- that file is mock-only and must not be touched; this file proves
#   the mocked shape (KeyNotFoundException on a stale id) actually
#   matches what a live LCM raises.
#
#   Runs exclusively against target_sandbox (a tempdir copy of the
#   Target .fwbackup fixture) -- never the in-place target_project --
#   because other sessions on this machine may hold the real,
#   machine-global Target project open concurrently.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import pathlib

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_262_"

_EVIDENCE_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "specs" / "262-object-not-found" / "evidence"
)
_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
_EVIDENCE_JSON_PATH = _EVIDENCE_DIR / "live-262-probes-raw.json"


def _write_evidence(evidence):
    """
    Merge `evidence` into the shared raw-evidence JSON file so multiple
    tests in this module (and re-runs) accumulate rather than clobber
    each other. Mirrors the pattern in
    test_issue290_const_chart_reflection.py.
    """
    existing = {}
    if _EVIDENCE_JSON_PATH.exists():
        try:
            existing = json.loads(_EVIDENCE_JSON_PATH.read_text())
        except Exception:
            existing = {}
    existing.update(evidence)
    _EVIDENCE_JSON_PATH.write_text(json.dumps(existing, indent=2, default=str))


def _cause_shape(exc):
    """
    Capture the __cause__'s type identity (module, name, MRO) so the
    evidence file records exactly what CLR exception type the live LCM
    actually raised -- the production except clause's correctness
    depends on this being KeyNotFoundException.
    """
    cause = exc.__cause__
    if cause is None:
        return {
            "cause_present": False,
            "cause_module": None,
            "cause_name": None,
            "cause_mro": None,
        }
    cause_type = type(cause)
    return {
        "cause_present": True,
        "cause_module": cause_type.__module__,
        "cause_name": cause_type.__name__,
        "cause_mro": [f"{t.__module__}.{t.__name__}" for t in cause_type.__mro__],
        "cause_str": str(cause),
    }


class TestStaleIdAllThreeInputForms:
    """
    Probe 1 (HANDOFF.md section 4, item 1): create an object, capture
    .Guid and .Hvo, delete it, then call Object() with all three
    well-formed-but-stale input forms (guid str, System.Guid, hvo int).
    Every form must raise FP_ParameterError with __cause__ carrying the
    live CLR exception -- captured and asserted on, not assumed to be
    KeyNotFoundException.
    """

    @pytest.mark.live_phase("FLExProject", "read")
    def test_stale_guid_str_hvo_all_raise_fp_parameter_error(self, target_sandbox):
        import System
        from flexicon.code.FLExProject import FP_ParameterError

        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}stale_probe")
        guid_obj = entry.Guid
        guid_str = str(guid_obj)
        hvo = entry.Hvo

        entries.Delete(entry)

        evidence = {"probe1_guid_str": guid_str, "probe1_hvo": hvo}

        # -- guid str --
        with pytest.raises(FP_ParameterError) as exc_str:
            target_sandbox.Object(guid_str)
        evidence["probe1_guid_str_cause"] = _cause_shape(exc_str.value)

        # -- System.Guid --
        with pytest.raises(FP_ParameterError) as exc_guid:
            target_sandbox.Object(System.Guid(guid_str))
        evidence["probe1_system_guid_cause"] = _cause_shape(exc_guid.value)

        # -- hvo int --
        with pytest.raises(FP_ParameterError) as exc_hvo:
            target_sandbox.Object(hvo)
        evidence["probe1_hvo_cause"] = _cause_shape(exc_hvo.value)

        _write_evidence(evidence)

        print(f"[262 probe1] guid_str cause: {evidence['probe1_guid_str_cause']}")
        print(f"[262 probe1] system.guid cause: {evidence['probe1_system_guid_cause']}")
        print(f"[262 probe1] hvo cause: {evidence['probe1_hvo_cause']}")

        for key in (
            "probe1_guid_str_cause",
            "probe1_system_guid_cause",
            "probe1_hvo_cause",
        ):
            shape = evidence[key]
            assert shape["cause_present"], (
                f"{key}: FP_ParameterError was raised with no __cause__ -- "
                "the except clause's `from e` was lost."
            )
            assert shape["cause_name"] == "KeyNotFoundException", (
                f"{key}: live LCM raised {shape['cause_module']}."
                f"{shape['cause_name']} on a stale id, not "
                "KeyNotFoundException. The production except tuple in "
                "FLExProject.Object() is built around "
                "System.Collections.Generic.KeyNotFoundException and does "
                "not actually cover this live shape -- this is a genuine "
                "finding, not a test bug."
            )


class TestNeverExistedVsDeletedControlledAB:
    """
    Probe 2: in one controlled run, compare the CLR exception raised for
    a never-issued Hvo against the CLR exception raised for a Hvo that
    existed and was deleted. Prior evidence covers each case separately;
    this asserts they are identical within a single process/session.
    """

    @pytest.mark.live_phase("FLExProject", "read")
    def test_never_existed_and_deleted_hvo_raise_identical_clr_type(
        self, target_sandbox
    ):
        from flexicon.code.FLExProject import FP_ParameterError

        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}ab_probe")
        deleted_hvo = entry.Hvo
        entries.Delete(entry)

        never_existed_hvo = 999999999

        with pytest.raises(FP_ParameterError) as exc_deleted:
            target_sandbox.Object(deleted_hvo)
        with pytest.raises(FP_ParameterError) as exc_never:
            target_sandbox.Object(never_existed_hvo)

        deleted_shape = _cause_shape(exc_deleted.value)
        never_shape = _cause_shape(exc_never.value)

        evidence = {
            "probe2_deleted_hvo": deleted_hvo,
            "probe2_deleted_cause": deleted_shape,
            "probe2_never_existed_hvo": never_existed_hvo,
            "probe2_never_existed_cause": never_shape,
        }
        _write_evidence(evidence)

        print(f"[262 probe2] deleted cause: {deleted_shape}")
        print(f"[262 probe2] never-existed cause: {never_shape}")

        assert deleted_shape["cause_present"] and never_shape["cause_present"], (
            "One or both of the deleted/never-existed probes raised "
            "FP_ParameterError with no __cause__."
        )
        assert deleted_shape["cause_module"] == never_shape["cause_module"], (
            "Deleted-Hvo and never-existed-Hvo raised __cause__ from "
            f"different CLR modules: {deleted_shape['cause_module']!r} "
            f"vs {never_shape['cause_module']!r}."
        )
        assert deleted_shape["cause_name"] == never_shape["cause_name"], (
            "Deleted-Hvo and never-existed-Hvo raised different __cause__ "
            f"types: {deleted_shape['cause_name']!r} vs "
            f"{never_shape['cause_name']!r}. The two cases are NOT "
            "equivalent live -- a genuine finding, do not paper over it."
        )


class TestEdgeInputsNoPriorEvidence:
    """
    Probe 3: Hvo=0, a negative Hvo, and a syntactically valid but
    foreign/random System.Guid. None of these has prior live evidence.
    Each must surface as FP_ParameterError -- not as a bare
    ArgumentException, OverflowException, or anything else that would
    slip past the production except tuple.
    """

    @pytest.mark.live_phase("FLExProject", "read")
    def test_hvo_zero_raises_fp_parameter_error(self, target_sandbox):
        from flexicon.code.FLExProject import FP_ParameterError

        try:
            with pytest.raises(FP_ParameterError) as exc:
                target_sandbox.Object(0)
            shape = _cause_shape(exc.value)
            _write_evidence({"probe3_hvo_zero_cause": shape})
            print(f"[262 probe3] Hvo=0 cause: {shape}")
        except FP_ParameterError:
            raise
        except Exception as exc:
            _write_evidence(
                {
                    "probe3_hvo_zero_escaped_type": (
                        f"{type(exc).__module__}.{type(exc).__name__}"
                    ),
                    "probe3_hvo_zero_escaped_str": str(exc),
                }
            )
            raise AssertionError(
                f"Object(0) escaped the FP_ParameterError contract with "
                f"{type(exc).__module__}.{type(exc).__name__}: {exc}. "
                "This is exactly the failure mode the fix's except tuple "
                "is supposed to prevent -- widen the tuple, do not widen "
                "this assertion."
            ) from exc

    @pytest.mark.live_phase("FLExProject", "read")
    def test_negative_hvo_raises_fp_parameter_error(self, target_sandbox):
        from flexicon.code.FLExProject import FP_ParameterError

        try:
            with pytest.raises(FP_ParameterError) as exc:
                target_sandbox.Object(-1)
            shape = _cause_shape(exc.value)
            _write_evidence({"probe3_negative_hvo_cause": shape})
            print(f"[262 probe3] Hvo=-1 cause: {shape}")
        except FP_ParameterError:
            raise
        except Exception as exc:
            _write_evidence(
                {
                    "probe3_negative_hvo_escaped_type": (
                        f"{type(exc).__module__}.{type(exc).__name__}"
                    ),
                    "probe3_negative_hvo_escaped_str": str(exc),
                }
            )
            raise AssertionError(
                f"Object(-1) escaped the FP_ParameterError contract with "
                f"{type(exc).__module__}.{type(exc).__name__}: {exc}. "
                "This is exactly the failure mode the fix's except tuple "
                "is supposed to prevent -- widen the tuple, do not widen "
                "this assertion."
            ) from exc

    @pytest.mark.live_phase("FLExProject", "read")
    def test_random_foreign_guid_raises_fp_parameter_error(self, target_sandbox):
        import System
        from flexicon.code.FLExProject import FP_ParameterError

        foreign_guid = System.Guid.NewGuid()

        try:
            with pytest.raises(FP_ParameterError) as exc:
                target_sandbox.Object(foreign_guid)
            shape = _cause_shape(exc.value)
            _write_evidence(
                {
                    "probe3_foreign_guid": str(foreign_guid),
                    "probe3_foreign_guid_cause": shape,
                }
            )
            print(f"[262 probe3] foreign guid cause: {shape}")
        except FP_ParameterError:
            raise
        except Exception as exc:
            _write_evidence(
                {
                    "probe3_foreign_guid_escaped_type": (
                        f"{type(exc).__module__}.{type(exc).__name__}"
                    ),
                    "probe3_foreign_guid_escaped_str": str(exc),
                }
            )
            raise AssertionError(
                f"Object(random guid) escaped the FP_ParameterError "
                f"contract with {type(exc).__module__}.{type(exc).__name__}: "
                f"{exc}. This is exactly the failure mode the fix's except "
                "tuple is supposed to prevent -- widen the tuple, do not "
                "widen this assertion."
            ) from exc


class TestValidCaseRoundTripUnchanged:
    """
    Probe 4: the try/except must not have disturbed the success path.
    Round-trips a live object through both Object(hvo) and Object(guid)
    and reads .Guid/.Hvo/.ClassName back from the LCM (not from what was
    passed in) to confirm the correct object comes back both ways.
    """

    @pytest.mark.live_phase("FLExProject", "read")
    def test_object_by_hvo_and_guid_returns_same_correct_object(
        self, target_sandbox
    ):
        entries = target_sandbox.LexEntry
        created = None
        try:
            created = entries.Create(lexeme_form=f"{TEST_PREFIX}valid_roundtrip")
            expected_hvo = created.Hvo
            expected_guid = created.Guid
            expected_guid_str = str(expected_guid)
            expected_classname = created.ClassName

            by_hvo = target_sandbox.Object(expected_hvo)
            by_guid_obj = target_sandbox.Object(expected_guid)
            by_guid_str = target_sandbox.Object(expected_guid_str)

            _write_evidence(
                {
                    "probe4_expected_hvo": expected_hvo,
                    "probe4_expected_guid": expected_guid_str,
                    "probe4_expected_classname": expected_classname,
                    "probe4_by_hvo_hvo": by_hvo.Hvo,
                    "probe4_by_hvo_guid": str(by_hvo.Guid),
                    "probe4_by_hvo_classname": by_hvo.ClassName,
                    "probe4_by_guid_obj_hvo": by_guid_obj.Hvo,
                    "probe4_by_guid_str_hvo": by_guid_str.Hvo,
                }
            )

            # Read every field back from the resolved object, not from
            # what was passed in, per the "read back from the LCM"
            # requirement.
            assert by_hvo.Hvo == expected_hvo
            assert str(by_hvo.Guid) == expected_guid_str
            assert by_hvo.ClassName == expected_classname

            assert by_guid_obj.Hvo == expected_hvo
            assert str(by_guid_obj.Guid) == expected_guid_str
            assert by_guid_obj.ClassName == expected_classname

            assert by_guid_str.Hvo == expected_hvo
            assert str(by_guid_str.Guid) == expected_guid_str
            assert by_guid_str.ClassName == expected_classname
        finally:
            if created is not None:
                try:
                    entries.Delete(created)
                except Exception:
                    pass


class TestCascadeDeleteRegression:
    """
    Probe 5: tests/operations/test_wfi_analysis.py
    (TestWfiAnalysisCascadeDelete, per the "the assert MUST stay outside
    the try" comment around line 676) relies on Object() raising for a
    deleted Hvo as its cascade-delete "gone" signal, caught by a broad
    `except Exception:` that maps any exception (including the pre-fix
    raw KeyNotFoundException) to `leftover = None`. This reproduces that
    exact pattern against the post-fix FP_ParameterError to confirm the
    broad `except Exception:` still catches it and the assertion still
    passes.

    Nothing here indicates the pattern will fail: FP_ParameterError is a
    subclass of FP_RuntimeError -> Exception (flexicon/code/exceptions.py),
    so the bare `except Exception:` in test_wfi_analysis.py catches it
    exactly as it caught the old KeyNotFoundException. This test exists
    to confirm that live, not to assume it from the class hierarchy.
    """

    @pytest.mark.live_phase("TextsWords", "modify")
    def test_object_lookup_on_deleted_hvo_is_caught_by_broad_except(
        self, target_sandbox
    ):
        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}cascade_probe")
        deleted_hvo = entry.Hvo
        entries.Delete(entry)

        # Exact pattern from test_wfi_analysis.py's cascade-delete test:
        # deliberately catch-all, mapping any exception to leftover=None.
        try:
            leftover = target_sandbox.Object(deleted_hvo)
        except Exception as exc:
            leftover = None
            caught_type = f"{type(exc).__module__}.{type(exc).__name__}"
        else:
            caught_type = None

        _write_evidence(
            {
                "probe5_deleted_hvo": deleted_hvo,
                "probe5_caught_type": caught_type,
                "probe5_leftover": repr(leftover),
            }
        )
        print(f"[262 probe5] caught_type={caught_type} leftover={leftover!r}")

        assert leftover is None, (
            "test_wfi_analysis.py's cascade-delete pattern "
            "(`except Exception: leftover = None`) did not fire for a "
            "deleted Hvo post-fix -- Object() must still raise for a "
            "stale id, not return a live object or silently succeed."
        )
        assert caught_type is not None and caught_type.endswith(
            "FP_ParameterError"
        ), (
            f"Expected the broad except to have caught FP_ParameterError, "
            f"got {caught_type!r} instead."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
