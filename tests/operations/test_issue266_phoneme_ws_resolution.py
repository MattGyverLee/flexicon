#
#   test_issue266_phoneme_ws_resolution.py
#
#   Class: TestApplyBasicIPASymbolWsResolution
#          Offline coverage for issue #266: routing
#          PhonemeOperations.__ApplyBasicIPASymbol's target writing-system
#          lookup through the shared BaseOperations._resolve_ws_handle
#          helper (spec 250 Defect 4, C-D4-7 -- the deliberately-parameterised
#          module-level resolver named ahead of time for exactly this
#          substitution).
#
#   Pre-fix shape (byte-for-byte, per issue #266):
#
#       tgt_ws_id = ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
#       tgt_handle = target_ws_by_id.get(tgt_ws_id)   # exact-match only
#       if tgt_handle is None:
#           continue                                   # silent drop
#
#   Post-fix, the handle lookup goes through _resolve_ws_handle, which
#   adds a case/separator-tolerant normalized fallback and raises
#   FP_ParameterError on a genuinely ambiguous normalized match (spec 250
#   C-D4-3 step 2b) -- a new failure mode for SetBasicIPASymbol, documented
#   in CHANGELOG.md.
#
#   All tests here call PhonemeOperations.__ApplyBasicIPASymbol directly
#   (via its name-mangled attribute) against a fabricated project + faked
#   SetBasicIPASymbol/GetBasicIPASymbol -- no real LCM writes, no
#   requires_live_project marker. The PhonemeOperations import itself is
#   deferred into a fixture (matching tests/operations/test_basic_ipa.py's
#   lazy-import convention) so this file collects cleanly even before the
#   session-scoped FieldWorks init fixture has run.
#
#   See also tests/operations/test_issue250_defect4_ws_resolution.py
#   Section A, which pins the equivalent _resolve_ws_handle behaviour
#   (exact hit / case fallback / separator fallback / genuine miss /
#   ambiguity raise / index-cache-built-once) directly against the pure
#   helper. This file pins the same set of behaviours at the
#   PhonemeOperations integration point instead.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# ---------------------------------------------------------------------------
# Lazy import: PhonemeOperations.py imports SIL.LCModel types at module
# scope, so importing it before the session-scoped FieldWorks-init fixture
# (tests/conftest.py::initialize_flex_for_tests, autouse) has registered
# the CLR assemblies would fail at collection time. Deferring the import
# into a fixture used by each test guarantees the autouse session fixture
# (higher scope) has already run.
# ---------------------------------------------------------------------------


@pytest.fixture()
def phoneme_ops_class():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

    return PhonemeOperations


@pytest.fixture()
def fp_parameter_error():
    from flexicon.code.FLExProject import FP_ParameterError

    return FP_ParameterError


# ============================================================================
# Fakes
# ============================================================================


class _FakeWs:
    """Stand-in for an IWritingSystemDefinition: only .Id / .Handle read."""

    def __init__(self, ws_id, handle):
        self.Id = ws_id
        self.Handle = handle


class _FakeWritingSystemsOps:
    def __init__(self, ws_list):
        self._ws_list = list(ws_list)

    def GetAll(self):
        return self._ws_list


class _FakeProject:
    """Minimal project stand-in: only .WritingSystems.GetAll() is read by
    __ApplyBasicIPASymbol before it delegates to SetBasicIPASymbol /
    GetBasicIPASymbol (both faked directly on the operations instance so
    no real LCM write ever happens)."""

    def __init__(self, ws_list):
        self.WritingSystems = _FakeWritingSystemsOps(ws_list)


class _FakePhoneme:
    """Opaque stand-in for an IPhPhoneme. __GetPhonemeObject returns any
    non-int input unchanged, so this never needs real LCM behaviour."""


def _make_ops(phoneme_ops_class, ws_list, existing_ipa=None):
    """Build a PhonemeOperations instance wired to a fake project, with
    SetBasicIPASymbol/GetBasicIPASymbol replaced by tracking fakes so the
    test observes only the writing-system resolution behaviour of
    __ApplyBasicIPASymbol, never a real LCM write.

    Returns (ops, set_calls, get_calls) where set_calls is a list of
    (text, wsHandle) tuples and get_calls is a list of wsHandle values
    passed to GetBasicIPASymbol (fill_gaps path only).
    """
    ops = phoneme_ops_class(_FakeProject(ws_list))
    set_calls = []
    get_calls = []
    existing_ipa = existing_ipa or {}

    def _fake_set(phoneme_or_hvo, ipa, wsHandle=None):
        set_calls.append((ipa, wsHandle))

    def _fake_get(phoneme_or_hvo, wsHandle=None):
        get_calls.append(wsHandle)
        return existing_ipa.get(wsHandle, "")

    # OperationsMethod is a non-data descriptor (no __set__), so an
    # instance-dict assignment shadows it -- these fakes are picked up by
    # ordinary attribute lookup on `ops` exactly like a bound method would.
    ops.SetBasicIPASymbol = _fake_set
    ops.GetBasicIPASymbol = _fake_get
    return ops, set_calls, get_calls


def _apply(ops, ws_values, ws_map=None, fill_gaps=False):
    """Call the name-mangled private method under test directly."""
    method = getattr(ops, "_PhonemeOperations__ApplyBasicIPASymbol")
    return method(_FakePhoneme(), ws_values, ws_map, fill_gaps)


# ============================================================================
# Exact match (zero-regression basis)
# ============================================================================


class TestApplyBasicIPASymbolExactMatch:
    def test_exact_match_resolves_and_writes(self, phoneme_ops_class):
        ops, set_calls, _ = _make_ops(phoneme_ops_class, [_FakeWs("en-US", 42)])

        _apply(ops, {"en-US": "p"})

        assert set_calls == [("p", 42)]


# ============================================================================
# Normalized fallback: case and separator divergence (the bug being fixed)
# ============================================================================


class TestApplyBasicIPASymbolNormalizedFallback:
    def test_case_divergent_alt_resolves(self, phoneme_ops_class):
        """Source spells 'etu' (lowercase); target's real ws.Id is 'ETU'.
        Pre-fix this alt was silently dropped -- the exact bug in #266."""
        ops, set_calls, _ = _make_ops(phoneme_ops_class, [_FakeWs("ETU", 7)])

        _apply(ops, {"etu": "ɯ"})

        assert set_calls == [("ɯ", 7)]

    def test_separator_divergent_alt_resolves(self, phoneme_ops_class):
        """Source spells 'en_US' (underscore); target's real ws.Id is
        'en-US' (hyphen)."""
        ops, set_calls, _ = _make_ops(phoneme_ops_class, [_FakeWs("en-US", 42)])

        _apply(ops, {"en_US": "p"})

        assert set_calls == [("p", 42)]

    def test_ws_map_indirection_then_normalized_resolves(self, phoneme_ops_class):
        """Normalization applies AFTER the ws_map indirection (spec 250
        C-D4-5): ws_map points 'en' at 'en-us', but the target's real
        ws.Id is 'en-US'."""
        ops, set_calls, _ = _make_ops(phoneme_ops_class, [_FakeWs("en-US", 42)])

        _apply(ops, {"en": "p"}, ws_map={"en": "en-us"})

        assert set_calls == [("p", 42)]

    def test_exact_match_preferred_over_normalized_when_both_present(
        self, phoneme_ops_class
    ):
        """If the exact-case key is ALSO present, it must win -- the
        normalized fallback must never be consulted."""
        ops, set_calls, _ = _make_ops(
            phoneme_ops_class, [_FakeWs("en-us", 1), _FakeWs("en-US", 2)]
        )

        _apply(ops, {"en-us": "p"})

        assert set_calls == [("p", 1)]


# ============================================================================
# Genuine miss (Defect 3, deliberately unchanged -- silent continue)
# ============================================================================


class TestApplyBasicIPASymbolGenuineMiss:
    def test_absent_target_ws_is_silently_skipped(self, phoneme_ops_class):
        ops, set_calls, _ = _make_ops(phoneme_ops_class, [_FakeWs("en-US", 1)])

        _apply(ops, {"de-DE": "should-be-dropped"})

        assert set_calls == []


# ============================================================================
# Ambiguity: new failure mode introduced by routing through
# _resolve_ws_handle (spec 250 C-D4-3 step 2b) -- must raise, never guess.
# ============================================================================


class TestApplyBasicIPASymbolAmbiguity:
    def test_ambiguous_normalized_match_raises(
        self, phoneme_ops_class, fp_parameter_error
    ):
        ops, set_calls, _ = _make_ops(
            phoneme_ops_class, [_FakeWs("en-US", 1), _FakeWs("en-us", 2)]
        )

        with pytest.raises(fp_parameter_error) as excinfo:
            _apply(ops, {"en_us": "should-not-write"})

        msg = str(excinfo.value)
        assert "en-US" in msg and "en-us" in msg, (
            f"Ambiguity error must name BOTH ambiguous spellings; got: {msg!r}"
        )
        assert set_calls == [], "No write may happen once ambiguity is detected."

    def test_keys_normalizing_together_sharing_one_handle_do_not_raise(
        self, phoneme_ops_class
    ):
        """Two spellings that normalize together but share the SAME handle
        are not ambiguous (deduped by handle before counting)."""
        ops, set_calls, _ = _make_ops(
            phoneme_ops_class, [_FakeWs("en-US", 1), _FakeWs("en-us", 1)]
        )

        _apply(ops, {"en_US": "p"})

        assert set_calls == [("p", 1)]


# ============================================================================
# fill_gaps interaction: unchanged wiring, exercised through the resolved
# handle so a regression in "which handle GetBasicIPASymbol is queried
# with" would be caught here.
# ============================================================================


class TestApplyBasicIPASymbolFillGaps:
    def test_fill_gaps_skips_when_target_alt_already_set(self, phoneme_ops_class):
        ops, set_calls, get_calls = _make_ops(
            phoneme_ops_class, [_FakeWs("ETU", 7)], existing_ipa={7: "already-set"}
        )

        _apply(ops, {"etu": "new-value"}, fill_gaps=True)

        assert get_calls == [7]
        assert set_calls == [], "fill_gaps must not overwrite a non-empty target alt."

    def test_fill_gaps_writes_when_target_alt_empty(self, phoneme_ops_class):
        ops, set_calls, get_calls = _make_ops(phoneme_ops_class, [_FakeWs("ETU", 7)])

        _apply(ops, {"etu": "new-value"}, fill_gaps=True)

        assert get_calls == [7]
        assert set_calls == [("new-value", 7)]


# ============================================================================
# Shared index-cache identity (spec 250 C-D4-4): __ApplyBasicIPASymbol must
# build ONE cache dict per apply call and pass the SAME object to every
# _resolve_ws_handle call within that one invocation, never a fresh one
# per alt. The per-key "build the normalized index at most once" property
# of _resolve_ws_handle itself is already pinned directly in
# test_issue250_defect4_ws_resolution.py Section A; this test pins the
# integration-point contract that makes that memoization reachable here.
# ============================================================================


class TestApplyBasicIPASymbolSharedIndexCache:
    def test_same_index_cache_object_reused_across_alts_in_one_call(
        self, phoneme_ops_class, monkeypatch
    ):
        import flexicon.code.Grammar.PhonemeOperations as phoneme_ops_module

        real_resolve = phoneme_ops_module._resolve_ws_handle
        seen_cache_ids = []

        def _spy(target_ws_by_id, tgt_ws_id, _index_cache=None):
            seen_cache_ids.append(id(_index_cache))
            return real_resolve(target_ws_by_id, tgt_ws_id, _index_cache=_index_cache)

        monkeypatch.setattr(phoneme_ops_module, "_resolve_ws_handle", _spy)

        ops, set_calls, _ = _make_ops(
            phoneme_ops_class, [_FakeWs("en-US", 1), _FakeWs("fr-FR", 2)]
        )

        _apply(ops, {"en-us": "a", "fr-fr": "b"})

        assert len(seen_cache_ids) == 2, "Expected one _resolve_ws_handle call per alt."
        assert len(set(seen_cache_ids)) == 1, (
            "__ApplyBasicIPASymbol must pass the SAME _index_cache dict to "
            "every _resolve_ws_handle call within one apply invocation "
            "(spec 250 C-D4-4), not rebuild it per alt."
        )
        assert set_calls == [("a", 1), ("b", 2)]

    def test_fresh_index_cache_per_apply_call(self, phoneme_ops_class, monkeypatch):
        """Different __ApplyBasicIPASymbol invocations must not leak the
        same cache dict across calls -- each call builds its own."""
        import flexicon.code.Grammar.PhonemeOperations as phoneme_ops_module

        real_resolve = phoneme_ops_module._resolve_ws_handle
        seen_cache_ids = []

        def _spy(target_ws_by_id, tgt_ws_id, _index_cache=None):
            seen_cache_ids.append(id(_index_cache))
            return real_resolve(target_ws_by_id, tgt_ws_id, _index_cache=_index_cache)

        monkeypatch.setattr(phoneme_ops_module, "_resolve_ws_handle", _spy)

        ops, _, _ = _make_ops(phoneme_ops_class, [_FakeWs("en-US", 1)])

        _apply(ops, {"en-us": "a"})
        _apply(ops, {"en-us": "b"})

        assert len(set(seen_cache_ids)) == 2, (
            "Each __ApplyBasicIPASymbol call must build its own "
            "_index_cache; reusing one across calls would be an "
            "instance-level leak, not a per-apply-call memoization."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
