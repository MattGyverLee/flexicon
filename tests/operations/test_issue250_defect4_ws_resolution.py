#
#   test_issue250_defect4_ws_resolution.py
#
#   Class: TestApplyPropsLoopWsCaseFallback / TestResolutionSiteRatchet
#          Offline coverage for issue #250 Defect 4 (D4-T2):
#          BaseOperations._apply_props_loop's normalized writing-system
#          resolution fallback, plus a lexical ratchet pinning the closed
#          three-site resolution enumeration from spec
#          specs/250-writingsystem-activation/spec.md section 3 (errata).
#
#   Scope reminder (spec 250, fence 1.2 / C-D4-2): the fix under test here
#   is LOOKUP-ONLY, inside _apply_props_loop / the new module-level
#   _resolve_ws_handle helper. It reaches exactly ONE of the three
#   resolution sites enumerated in the spec:
#
#     1. BaseOperations.py _apply_props_loop            -- REACHED (this fix)
#     2. Grammar/PhonemeOperations.py __ApplyBasicIPASymbol -- NOT reached
#     3. Lexicon/ExampleOperations.py ApplySyncableProperties's
#        TranslationsOC loop                             -- NOT reached
#
#   This file does not touch, import, or exercise sites 2/3 -- they are out
#   of scope by ruling (spec section 1.2/1.3), not by oversight. See
#   specs/250-writingsystem-activation/evidence/live-D4-T3.md for the
#   coverage-boundary statement required by acceptance criterion 8.
#
#   All tests in this file call _apply_props_loop / _resolve_ws_handle
#   directly with fabricated dicts and fake item objects -- no SIL.LCModel
#   import, no live project, no `requires_live_project` marker.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pathlib

import pytest

from flexicon.code.BaseOperations import (
    _apply_props_loop,
    _resolve_ws_handle,
    _normalize_ws_tag,
    FP_ParameterError,
)


# ============================================================================
# Fakes (self-contained; mirrors tests/operations/test_apply_syncable_properties.py's
# shapes but kept local to this file per that file's own convention of
# owning its fakes).
# ============================================================================


class _FakeTsString:
    def __init__(self, text):
        self.Text = text
        self.RunCount = 1 if text else 0


class _FakeTsStringUtils:
    def __init__(self):
        self.calls = []

    def MakeString(self, text, ws_handle):
        self.calls.append((text, ws_handle))
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
        pass


class _CountingDict(dict):
    """dict subclass that counts .items() calls, so tests can assert the
    normalized side-index is built at most once per _apply_props_loop call
    (spec 250 C-D4-4): building the index calls target_ws_by_id.items()
    exactly once; every additional miss within the same apply call must
    reuse the cached index rather than calling .items() again."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_call_count = 0

    def items(self):
        self.items_call_count += 1
        return super().items()


# ============================================================================
# Section A: _resolve_ws_handle / _normalize_ws_tag unit coverage
# ============================================================================


class TestNormalizeWsTag:
    def test_lowercases_and_folds_underscore_to_hyphen(self):
        assert _normalize_ws_tag("EN_US") == "en-us"

    def test_already_canonical_is_unchanged(self):
        assert _normalize_ws_tag("en-us") == "en-us"


class TestResolveWsHandleExactMatch:
    def test_exact_hit_never_consults_index(self):
        """C-D4-3 step 1: an exact match returns immediately and never
        builds/consults the normalized index -- proven via a counting
        fake whose .items() call count stays at zero."""
        target_ws_by_id = _CountingDict({"en-US": 1, "fr": 2})
        cache = {}

        handle = _resolve_ws_handle(target_ws_by_id, "en-US", _index_cache=cache)

        assert handle == 1
        assert target_ws_by_id.items_call_count == 0, (
            "An exact-match hit must never call target_ws_by_id.items() -- "
            "doing so would mean the normalized index was built even "
            "though it was never needed."
        )
        assert cache == {}, "Cache must remain empty after an exact-match-only path."

    def test_exact_match_is_byte_for_byte_unaffected_by_fix(self):
        """Every write that succeeds today (exact match) must resolve to
        the identical handle post-fix -- the zero-regression basis."""
        target_ws_by_id = {"en": 1, "EN": 2}  # two distinct exact keys
        assert _resolve_ws_handle(target_ws_by_id, "en") == 1
        assert _resolve_ws_handle(target_ws_by_id, "EN") == 2


class TestResolveWsHandleNormalizedFallback:
    """D4-a/b/c: case and/or separator divergence, resolved via the
    normalized fallback (spec 250 C-D4-1, C-D4-3 step 2a, C-D4-5)."""

    def test_case_divergence_resolves(self):
        # Store holds 'en-US'; caller asks for 'en-us' (D4-a/b shape).
        target_ws_by_id = {"en-US": 7}
        assert _resolve_ws_handle(target_ws_by_id, "en-us") == 7

    def test_separator_divergence_resolves(self):
        # Store holds 'en-US'; caller asks for 'en_US' (D4-c shape).
        target_ws_by_id = {"en-US": 7}
        assert _resolve_ws_handle(target_ws_by_id, "en_US") == 7

    def test_case_and_separator_divergence_resolves(self):
        target_ws_by_id = {"en-US": 7}
        assert _resolve_ws_handle(target_ws_by_id, "EN_us") == 7

    def test_genuinely_absent_ws_falls_through_to_none(self):
        """Defect 3 (OUT of scope): a truly-absent WS still resolves to
        None so the caller's existing silent `continue` fires unchanged."""
        target_ws_by_id = {"en-US": 7}
        assert _resolve_ws_handle(target_ws_by_id, "de-DE") is None

    def test_index_built_at_most_once_per_shared_cache(self):
        """C-D4-4: multiple misses sharing one _index_cache dict must build
        the normalized index exactly once."""
        target_ws_by_id = _CountingDict({"en-US": 7, "fr-FR": 9})
        cache = {}

        h1 = _resolve_ws_handle(target_ws_by_id, "en-us", _index_cache=cache)
        h2 = _resolve_ws_handle(target_ws_by_id, "fr-fr", _index_cache=cache)
        h3 = _resolve_ws_handle(target_ws_by_id, "EN-US", _index_cache=cache)

        assert (h1, h2, h3) == (7, 9, 7)
        assert target_ws_by_id.items_call_count == 1, (
            "The normalized index must be built at most once per shared "
            "_index_cache, even across multiple misses."
        )

    def test_no_index_cache_rebuilds_every_miss(self):
        """Passing _index_cache=None (the default) means no memoization --
        documented, not a defect -- exercised so the branch is covered."""
        target_ws_by_id = _CountingDict({"en-US": 7})

        assert _resolve_ws_handle(target_ws_by_id, "en-us") == 7
        assert _resolve_ws_handle(target_ws_by_id, "en-us") == 7

        assert target_ws_by_id.items_call_count == 2, (
            "Without a shared _index_cache, each miss rebuilds its own "
            "index (no cross-call memoization is possible without one)."
        )


class TestResolveWsHandleAmbiguity:
    """C-D4-3 step 2b: two-or-more DISTINCT handles normalizing together
    raises FP_ParameterError naming both spellings; NEVER picks one."""

    def test_two_distinct_handles_raises_naming_both(self):
        # Two exact-case keys that normalize to the same form, but map to
        # DIFFERENT handles -- genuinely ambiguous.
        target_ws_by_id = {"en-US": 1, "en-us": 2}
        # Query with a THIRD spelling (underscore variant) so neither key
        # is hit at step 1 (exact match) -- forces the normalized branch.
        with pytest.raises(FP_ParameterError) as excinfo:
            _resolve_ws_handle(target_ws_by_id, "en_us")

        msg = str(excinfo.value)
        assert "en-US" in msg and "en-us" in msg, (
            f"Ambiguity error must name BOTH ambiguous spellings; got: {msg!r}"
        )

    def test_ambiguity_never_picks_one(self):
        """Repeated calls must always raise -- never silently resolve to
        either candidate handle."""
        target_ws_by_id = {"en-US": 1, "en-us": 2}
        for _ in range(3):
            with pytest.raises(FP_ParameterError):
                _resolve_ws_handle(target_ws_by_id, "EN_US")

    def test_keys_normalizing_together_sharing_one_handle_do_not_raise(self):
        """Two spellings that normalize together but share the SAME handle
        are not ambiguous (deduped by handle before counting; C-D4-3
        step 2a's parenthetical)."""
        target_ws_by_id = {"en-US": 1, "en-us": 1}
        handle = _resolve_ws_handle(target_ws_by_id, "en_US")
        assert handle == 1


# ============================================================================
# Section B: _apply_props_loop integration -- D4-a, D4-b, D4-c end to end
# through the real caller shape (ws_map indirection then resolution).
# ============================================================================


class TestApplyPropsLoopWsCaseFallback:
    def test_d4a_ws_map_value_case_divergent_resolves(self):
        """D4-a: caller supplies ws_map={"en": "en-us"} but the target's
        real ws.Id is 'en-US'. Normalization applies AFTER the ws_map
        indirection (C-D4-5), so this must resolve."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        target_ws_by_id = {"en-US": 42}
        ws_map = {"en": "en-us"}

        _apply_props_loop(
            item, {"Name": {"en": "TEST_D4a"}}, target_ws_by_id, ws_map=ws_map,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Name.get_String(42).Text == "TEST_D4a"

    def test_d4b_no_ws_map_source_id_case_divergent_resolves(self):
        """D4-b: no ws_map at all -- src_ws_id passes through unchanged.
        Source spells 'en-us', target's real ws.Id is 'en-US'. This is the
        variant the original issue omits; C-D4-5 requires it be covered."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        target_ws_by_id = {"en-US": 42}

        _apply_props_loop(
            item, {"Name": {"en-us": "TEST_D4b"}}, target_ws_by_id, ws_map=None,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Name.get_String(42).Text == "TEST_D4b"

    def test_d4c_separator_divergent_resolves(self):
        """D4-c: separator divergence. Source/caller spells 'en_US'
        (underscore); target's real ws.Id is 'en-US' (hyphen)."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        target_ws_by_id = {"en-US": 42}

        _apply_props_loop(
            item, {"Name": {"en_US": "TEST_D4c"}}, target_ws_by_id, ws_map=None,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Name.get_String(42).Text == "TEST_D4c"

    def test_exact_match_still_preferred_over_normalized_when_both_present(self):
        """If the exact-case key is ALSO present, step 1 must win -- the
        fallback must never be consulted, let alone override an exact hit."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        # Both an exact 'en-us' and a case-divergent 'en-US' exist with
        # DIFFERENT handles; the source key is the exact-case one.
        target_ws_by_id = {"en-us": 1, "en-US": 2}

        _apply_props_loop(
            item, {"Name": {"en-us": "exact-wins"}}, target_ws_by_id, ws_map=None,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Name.get_String(1).Text == "exact-wins"
        assert item.Name.get_String(2).Text == "", (
            "The normalized fallback must never be consulted when an "
            "exact match exists, even if a case-divergent sibling key "
            "is also present in target_ws_by_id."
        )

    def test_ambiguous_spelling_raises_and_stops_the_apply(self):
        """A genuinely ambiguous normalized match raises FP_ParameterError
        from within _apply_props_loop, naming both spellings."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        target_ws_by_id = {"en-US": 1, "en-us": 2}

        with pytest.raises(FP_ParameterError) as excinfo:
            _apply_props_loop(
                item, {"Name": {"en_us": "should-not-write"}}, target_ws_by_id,
                ws_map=None, _ts_string_utils=_FakeTsStringUtils(),
            )

        msg = str(excinfo.value)
        assert "en-US" in msg and "en-us" in msg

    def test_absent_ws_still_hits_unchanged_silent_continue(self):
        """Defect 3 (OUT of scope): a WS genuinely absent from the target
        (under both exact and normalized matching) is still silently
        skipped -- no exception, no diagnostic, unchanged behaviour."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        target_ws_by_id = {"en-US": 1}

        _apply_props_loop(
            item, {"Name": {"de-DE": "should-be-dropped"}}, target_ws_by_id,
            ws_map=None, _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Name.get_String(1).Text == ""

    def test_index_built_at_most_once_across_multiple_props_in_one_apply_call(self):
        """C-D4-4, exercised through the real _apply_props_loop entry
        point (not just _resolve_ws_handle directly): two different
        multistring properties, each with a case-divergent alt, must
        share ONE normalized-index build for the whole apply call."""
        item = _FakeItem()
        object.__setattr__(item, "Name", _FakeMultiString())
        object.__setattr__(item, "Description", _FakeMultiString())
        target_ws_by_id = _CountingDict({"en-US": 1, "fr-FR": 2})

        _apply_props_loop(
            item,
            {
                "Name": {"en-us": "TEST_Name"},
                "Description": {"fr-fr": "TEST_Description"},
            },
            target_ws_by_id,
            ws_map=None,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Name.get_String(1).Text == "TEST_Name"
        assert item.Description.get_String(2).Text == "TEST_Description"
        assert target_ws_by_id.items_call_count == 1, (
            "_apply_props_loop must share a single _index_cache across "
            "every writing-system alt resolved within one call, so the "
            "normalized index is built at most once per apply call, not "
            "once per property or once per alt."
        )


# ============================================================================
# Section C: Resolution-site ratchet (spec 250 D4-T2, added cycle 7).
#
# Offline, lexical, no LCM. Enumerates every file under flexicon/code/
# containing the vulnerable self-resolving signature and asserts the set
# is EXACTLY the three sites closed at commit b3ba083b (spec section 3
# errata table). A fourth hit means a new self-resolving writing-system
# resolution loop was added somewhere and must route through
# _apply_props_loop / _resolve_ws_handle instead (spec 250 C-D4-7), or
# this ratchet needs updating if a site was legitimately fixed.
# ============================================================================


_RESOLUTION_SIGNATURES = (
    "ws_map.get(src_ws_id, src_ws_id)",
    "target_ws_by_id.get(",
)

_EXPECTED_RESOLUTION_SITE_FILES = frozenset(
    {
        "BaseOperations.py",
        "Grammar/PhonemeOperations.py",
        "Lexicon/ExampleOperations.py",
    }
)


def _flexicon_code_root():
    # tests/operations/this_file.py -> repo_root/tests/operations -> ../..
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    code_root = repo_root / "flexicon" / "code"
    assert code_root.is_dir(), f"Expected {code_root} to exist"
    return code_root


class TestResolutionSiteRatchet:
    def test_exactly_three_resolution_sites_exist(self):
        code_root = _flexicon_code_root()
        hit_files = set()

        for path in code_root.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if any(sig in text for sig in _RESOLUTION_SIGNATURES):
                hit_files.add(path.relative_to(code_root).as_posix())

        assert hit_files == _EXPECTED_RESOLUTION_SITE_FILES, (
            "a FOURTH self-resolving writing-system resolution loop was "
            "added; route it through `_apply_props_loop` or "
            "`_resolve_ws_handle` instead (spec 250 C-D4-7), or update "
            "this ratchet if a site was legitimately fixed.\n"
            f"Found: {sorted(hit_files)}\n"
            f"Expected: {sorted(_EXPECTED_RESOLUTION_SITE_FILES)}"
        )
