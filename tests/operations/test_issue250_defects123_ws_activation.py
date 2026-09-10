#
#   test_issue250_defects123_ws_activation.py
#
#   Class: TestExistsActiveOnly / TestExistsInStore / TestCreateActivation /
#          TestEnsure / TestApplyPropsLoopDefect3Diagnostics
#          Offline coverage for issue #250 Defects 1-3:
#            - Defect 1: WritingSystemOperations.Exists() must honour its
#              own documented "active only" contract instead of silently
#              scanning the whole LDML store.
#            - Defect 2: Create() must not refuse a tag that is present in
#              the store but not currently active -- it must activate it
#              instead of raising "already exists".
#            - Defect 3: the silent `continue` in
#              BaseOperations._apply_props_loop, when a target writing
#              system is genuinely absent, must be made OBSERVABLE (a
#              logged warning) rather than silent -- unconditionally, not
#              behind a strict= kwarg (see the module docstring in
#              WritingSystemOperations.py and the class docstrings below
#              for the full warn-vs-raise rationale).
#
#   Testing-note trap named in the issue: a fake that backs GetAll()/
#   Exists() with the SAME collection as the "store" cannot represent the
#   store-vs-active divergence this issue is about -- that is exactly the
#   shape that let the original consumer-side bug ship green. Every fixture
#   below keeps two DELIBERATELY SEPARATE collections:
#     - `all_ws` -- the whole LDML store (ServiceLocator.WritingSystems.
#       AllWritingSystems), the equivalent of _GetWSByTag's search space.
#     - `cur_vern_wss` / `cur_analysis_wss` -- the ACTIVE tag sets
#       (project.lp.CurVernWss / CurAnalysisWss), a strict subset.
#   Every "present but inactive" test below puts a tag in the former and
#   deliberately withholds it from the latter.
#
#   Confirmed red-then-green by reverting the fix locally and re-running
#   this file -- see specs/250-writingsystem-activation/reviews/
#   issue250-defects123-implementation.md for the before/after transcript.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from contextlib import contextmanager
from unittest.mock import Mock

import logging

import pytest

from flexicon.code.System.WritingSystemOperations import WritingSystemOperations
from flexicon.code.BaseOperations import _apply_props_loop
from flexicon.code.FLExProject import FP_ParameterError


# ============================================================================
# Fakes (self-contained per this test suite's own convention -- see
# test_issue250_defect4_ws_resolution.py's header for the precedent of each
# file owning its fakes rather than importing another test file's).
# ============================================================================


class _FakeWS:
    """Stand-in for IWritingSystemDefinition: just Id/Handle plus the two
    settable properties Create()/Ensure() write on a genuinely new WS."""

    def __init__(self, tag, handle):
        self.Id = tag
        self.Handle = handle
        self.Abbreviation = None
        self.DisplayLabel = None


@contextmanager
def _no_transaction(label):
    yield


def _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss=""):
    """
    Build a WritingSystemOperations bound to a Mock project whose STORE
    (`all_ws`) and ACTIVE sets (`cur_vern_wss` / `cur_analysis_wss`) are
    deliberately separate collections -- see module docstring.

    Returns (ops, mock_project, state) where `state` is a dict the test can
    inspect: {"all_ws": [...], "created_tags": [...], "added_vern": [...],
    "added_analysis": [...]}. `mock_project.lp.CurVernWss` /
    `CurAnalysisWss` are plain mutable-by-the-test strings (tests that
    exercise idempotency update them by hand after an Add* call, exactly as
    real LCM would via its own change-notification path -- this mock does
    not attempt to reproduce that automatically).
    """
    mock_project = Mock()
    mock_project.writeEnabled = True
    mock_project.project.ServiceLocator.WritingSystems.AllWritingSystems = all_ws
    mock_project.lp.CurVernWss = cur_vern_wss
    mock_project.lp.CurAnalysisWss = cur_analysis_wss

    state = {
        "all_ws": all_ws,
        "created_tags": [],
        "added_vern": [],
        "added_analysis": [],
    }

    def _ws_manager_create(tag):
        ws = _FakeWS(tag, handle=1000 + len(state["created_tags"]))
        state["created_tags"].append(tag)
        all_ws.append(ws)
        return ws

    mock_project.project.ServiceLocator.WritingSystemManager.Create.side_effect = (
        _ws_manager_create
    )
    mock_project.project.ServiceLocator.WritingSystemManager.Set = Mock()

    mock_project.lp.AddToCurrentVernacularWritingSystems.side_effect = (
        lambda ws: state["added_vern"].append(ws.Id)
    )
    mock_project.lp.AddToCurrentAnalysisWritingSystems.side_effect = (
        lambda ws: state["added_analysis"].append(ws.Id)
    )

    ops = WritingSystemOperations(mock_project)
    ops._TransactionCM = _no_transaction

    return ops, mock_project, state


# ============================================================================
# Defect 1: Exists() must be active-only, matching its own docstring and
# GetAll()'s semantics -- not a whole-store scan.
# ============================================================================


class TestExistsActiveOnly:
    def test_active_tag_exists(self):
        all_ws = [_FakeWS("en", 1), _FakeWS("etu", 2)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="etu", cur_analysis_wss="en")

        assert ops.Exists("en") is True

    def test_store_present_but_inactive_tag_does_not_exist(self):
        """The named reproduction from the issue: `fr` has an LDML in the
        store but is not in CurAnalysisWss -- Exists() must now say False,
        where the pre-fix whole-store scan said True."""
        all_ws = [_FakeWS("en", 1), _FakeWS("etu", 2), _FakeWS("fr", 3)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="etu", cur_analysis_wss="en")

        assert ops.Exists("fr") is False

    def test_absent_from_store_entirely_does_not_exist(self):
        all_ws = [_FakeWS("en", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")

        assert ops.Exists("qaa-x-nope") is False

    def test_case_and_separator_divergence_still_resolves_against_active_set(self):
        """Exists()'s normalization is preserved -- it just now ALSO
        requires the normalized match to land in the active set."""
        all_ws = [_FakeWS("en-US", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en-US")

        assert ops.Exists("en_us") is True
        assert ops.Exists("EN-US") is True

    def test_case_divergent_but_inactive_tag_does_not_exist(self):
        """The other live-confirmed route named in the issue: case-folds
        to a store match, but that store entry is not active."""
        all_ws = [_FakeWS("EN", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="")

        assert ops.Exists("en") is False


class TestExistsInStore:
    """The whole-store predicate under its own name (issue #250 Defect 1's
    proposed fix: keep a whole-store probe, but not as Exists())."""

    def test_active_tag_is_in_store(self):
        all_ws = [_FakeWS("en", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")
        assert ops.ExistsInStore("en") is True

    def test_inactive_store_tag_is_in_store(self):
        all_ws = [_FakeWS("en", 1), _FakeWS("fr", 2)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")
        assert ops.ExistsInStore("fr") is True

    def test_absent_tag_is_not_in_store(self):
        all_ws = [_FakeWS("en", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")
        assert ops.ExistsInStore("qaa-x-nope") is False

    def test_normalization_still_applies(self):
        all_ws = [_FakeWS("en_US", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="")
        assert ops.ExistsInStore("en-us") is True


# ============================================================================
# Defect 2: Create() must not conflate store-presence with usability.
# ============================================================================


class TestCreateActivation:
    def test_genuinely_new_tag_creates_and_activates(self):
        all_ws = [_FakeWS("en", 1)]
        ops, mock_project, state = _make_ops(
            all_ws, cur_vern_wss="", cur_analysis_wss="en"
        )

        ws = ops.Create("qaa-x-kal", "Kalaba", is_vernacular=True)

        assert state["created_tags"] == ["qaa-x-kal"], (
            "A genuinely absent tag must still go through "
            "WritingSystemManager.Create() -- this path is unchanged."
        )
        assert state["added_vern"] == ["qaa-x-kal"]
        assert ws.DisplayLabel == "Kalaba"

    def test_store_present_but_inactive_tag_is_activated_not_recreated(self):
        """The Defect 2 reproduction: `fr` already has an LDML (store-
        present) but is not in CurAnalysisWss. Create() must activate the
        EXISTING definition, not call WritingSystemManager.Create() again
        (which would attempt a duplicate registration) and must not raise
        "already exists" (Exists() now correctly says False for this tag)."""
        existing_fr = _FakeWS("fr", 42)
        all_ws = [_FakeWS("en", 1), existing_fr]
        ops, mock_project, state = _make_ops(
            all_ws, cur_vern_wss="", cur_analysis_wss="en"
        )

        ws = ops.Create("fr", "French", is_vernacular=False)

        assert state["created_tags"] == [], (
            "Create() must NOT call WritingSystemManager.Create() for a "
            "tag that already has a store entry -- that would attempt a "
            "duplicate registration for an Id the manager already tracks."
        )
        assert ws is existing_fr, (
            "Create() must reuse the existing store definition, not "
            "fabricate a new object."
        )
        assert state["added_analysis"] == ["fr"], (
            "The store-present-but-inactive tag must still be activated "
            "(added to the current analysis list)."
        )

    def test_already_active_tag_still_raises(self):
        """Zero-regression: an already-ACTIVE tag must still raise exactly
        as it did before this fix -- Create() is not a silent no-op for a
        genuine duplicate-activation request."""
        all_ws = [_FakeWS("en", 1)]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")

        with pytest.raises(FP_ParameterError, match="already exists"):
            ops.Create("en", "English", is_vernacular=False)

    def test_name_ignored_when_reusing_store_present_tag(self):
        existing_fr = _FakeWS("fr", 42)
        existing_fr.DisplayLabel = "Original French Label"
        all_ws = [_FakeWS("en", 1), existing_fr]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")

        ops.Create("fr", "A Different Name", is_vernacular=False)

        assert existing_fr.DisplayLabel == "Original French Label", (
            "Create() must not overwrite an existing WS's DisplayLabel "
            "when reusing a store-present definition -- `name` is "
            "documented as ignored in that path."
        )


# ============================================================================
# Defect 2 (API gap): Ensure() -- idempotent activate-or-create.
# ============================================================================


class TestEnsure:
    def test_already_active_is_a_true_no_op(self):
        all_ws = [_FakeWS("en", 1)]
        ops, mock_project, state = _make_ops(
            all_ws, cur_vern_wss="", cur_analysis_wss="en"
        )

        ws, created = ops.Ensure("en", "English", is_vernacular=False)

        assert created is False
        assert ws.Id == "en"
        assert state["created_tags"] == []
        assert state["added_analysis"] == [], (
            "Already-active tag: Ensure() must not re-add it."
        )
        assert state["added_vern"] == []

    def test_store_present_but_inactive_is_activated_not_created(self):
        existing_fr = _FakeWS("fr", 42)
        all_ws = [_FakeWS("en", 1), existing_fr]
        ops, _, state = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")

        ws, created = ops.Ensure("fr", "French", is_vernacular=False)

        assert created is False, (
            "created=False distinguishes 'already active' and "
            "'activated from store' from 'genuinely new' (see docstring)."
        )
        assert ws is existing_fr
        assert state["created_tags"] == []
        assert state["added_analysis"] == ["fr"]

    def test_genuinely_new_tag_is_created(self):
        all_ws = [_FakeWS("en", 1)]
        ops, _, state = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")

        ws, created = ops.Ensure("qaa-x-kal", "Kalaba", is_vernacular=True)

        assert created is True
        assert state["created_tags"] == ["qaa-x-kal"]
        assert state["added_vern"] == ["qaa-x-kal"]
        assert ws.DisplayLabel == "Kalaba"

    def test_never_raises_for_store_present_inactive_tag(self):
        """The core deadlock Ensure() exists to break: Create() alone would
        raise nothing here either post-fix (it now activates), but the
        OLD Create() would have raised "already exists" via the whole-
        store Exists(). Ensure() must not reproduce that failure mode."""
        existing_fr = _FakeWS("fr", 42)
        all_ws = [_FakeWS("en", 1), existing_fr]
        ops, _, _ = _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="en")

        # Must not raise.
        ws, created = ops.Ensure("fr", "French", is_vernacular=False)
        assert ws is existing_fr
        assert created is False

    def test_active_in_other_category_is_added_not_moved(self):
        """A tag active as vernacular, requested as analysis: Ensure() adds
        it to the analysis list too rather than erroring or migrating it
        (FLEx allows a WS to be both simultaneously)."""
        vern_ws = _FakeWS("etu", 7)
        all_ws = [vern_ws]
        ops, _, state = _make_ops(all_ws, cur_vern_wss="etu", cur_analysis_wss="")

        ws, created = ops.Ensure("etu", "Etu", is_vernacular=False)

        assert created is False
        assert state["created_tags"] == [], (
            "The tag already exists in the store (as an active vernacular "
            "WS) -- Ensure() must not create a duplicate."
        )
        assert state["added_analysis"] == ["etu"]
        assert state["added_vern"] == [], (
            "Must not re-add to vernacular; it is already active there."
        )

    def test_idempotent_second_call_is_a_no_op(self):
        """Calling Ensure() twice for the same store-present-but-inactive
        tag: the second call must see it as already active and no-op,
        exactly the guarantee a sync pre-pass needs."""
        existing_fr = _FakeWS("fr", 42)
        all_ws = [_FakeWS("en", 1), existing_fr]
        ops, mock_project, state = _make_ops(
            all_ws, cur_vern_wss="", cur_analysis_wss="en"
        )

        ws1, created1 = ops.Ensure("fr", "French", is_vernacular=False)
        assert created1 is False
        assert state["added_analysis"] == ["fr"]

        # Simulate the real LCM's change-notification path keeping
        # CurAnalysisWss in sync with AddToCurrentAnalysisWritingSystems
        # (this mock does not do that automatically -- see _make_ops
        # docstring).
        mock_project.lp.CurAnalysisWss = "en fr"

        ws2, created2 = ops.Ensure("fr", "French", is_vernacular=False)
        assert created2 is False
        assert ws2 is existing_fr
        # No SECOND activation call recorded beyond the first.
        assert state["added_analysis"] == ["fr"]


# ============================================================================
# Defect 3: the silent drop in _apply_props_loop must be observable.
# ============================================================================


class _FakeTsString:
    def __init__(self, text):
        self.Text = text
        self.RunCount = 1 if text else 0


class _FakeTsStringUtils:
    def MakeString(self, text, ws_handle):
        return _FakeTsString(text)


class _FakeMultiString:
    def __init__(self):
        self._store = {}

    def get_String(self, handle):
        return self._store.get(handle, _FakeTsString(""))

    def set_String(self, handle, tss):
        self._store[handle] = tss


class _FakeItem:
    def __init__(self):
        self.Hvo = 12345
        self.Name = _FakeMultiString()


class TestApplyPropsLoopDefect3Diagnostics:
    def test_genuinely_absent_ws_drop_is_logged_at_warning(self, caplog):
        item = _FakeItem()
        target_ws_by_id = {"en": 1}  # target genuinely lacks 'fr'

        with caplog.at_level(logging.WARNING, logger="flexicon"):
            _apply_props_loop(
                item,
                {"Name": {"fr": "Bonjour"}},
                target_ws_by_id,
                ws_map=None,
            )

        assert item.Name.get_String(1).Text == "", (
            "Sanity: the drop itself is unchanged -- 'fr' still does not "
            "resolve and nothing is written."
        )
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1, (
            f"Expected exactly one WARNING for the genuinely-absent WS "
            f"drop; got {len(warnings)}: {[r.message for r in warnings]}"
        )
        msg = warnings[0].getMessage()
        assert "fr" in msg and "Name" in msg, (
            f"Warning must name the property and the writing-system id "
            f"that was dropped; got: {msg!r}"
        )

    def test_resolvable_ws_does_not_log_a_warning(self, caplog):
        """Zero-regression: a hit (exact or normalized) must NOT log
        anything -- the warning is scoped to the genuine drop only."""
        item = _FakeItem()
        target_ws_by_id = {"en": 1}

        with caplog.at_level(logging.WARNING, logger="flexicon"):
            _apply_props_loop(
                item,
                {"Name": {"en": "Hello"}},
                target_ws_by_id,
                ws_map=None,
                _ts_string_utils=_FakeTsStringUtils(),
            )

        assert item.Name.get_String(1).Text == "Hello"
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warnings == []

    def test_drop_does_not_raise(self):
        """Explicit negative: Defect 3's fix is warn, not raise (see class
        docstring / implementation review for the full rationale) -- a
        genuinely-absent target WS must never propagate an exception,
        since that is business-as-usual for a cross-project sync with
        partial writing-system overlap."""
        item = _FakeItem()
        target_ws_by_id = {"en": 1}

        # Must not raise.
        _apply_props_loop(
            item, {"Name": {"fr": "Bonjour"}}, target_ws_by_id, ws_map=None
        )
