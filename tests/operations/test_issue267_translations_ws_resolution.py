#
#   test_issue267_translations_ws_resolution.py
#
#   Class: TestApplySyncablePropertiesTranslationsOCWsResolution
#          Offline coverage for issue #267: routing
#          ExampleOperations.ApplySyncableProperties's TranslationsOC loop
#          target writing-system lookup through the shared
#          BaseOperations._resolve_ws_handle helper (spec 250 Defect 4,
#          the last of the three sibling sites), WITHOUT reintroducing the
#          zero-alt orphaned ICmTranslation regression the issue warns
#          about.
#
#   Pre-fix shape (byte-for-byte, per issue #267):
#
#       tgt_ws_id = ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
#       tgt_handle = target_ws_by_id.get(tgt_ws_id)   # exact-match only
#       if tgt_handle is None:
#           continue                                   # silent drop
#
#   Unlike #266, a one-line substitution of _resolve_ws_handle here is
#   NOT sufficient: the pre-fix loop creates and attaches the
#   ICmTranslation (ICmTranslationFactory.Create + TranslationsOC.Add)
#   BEFORE resolving any of its alts' target writing systems. Naively
#   substituting a resolver that can raise FP_ParameterError on an
#   ambiguous normalized spelling (C-D4-3 step 2b) would therefore leave a
#   zero-alt ICmTranslation orphaned on the example when the raise fires
#   mid-loop -- worse than the silent drop being fixed.
#
#   The post-fix loop resolves every alt's target writing-system handle
#   BEFORE ICmTranslationFactory.Create / TranslationsOC.Add run, so an
#   ambiguous spelling raises before anything is attached (see
#   TestApplyTranslationsOCOrphanRegression below -- the test this issue
#   explicitly requires, which would fail against the naive one-line
#   substitution).
#
#   A genuine miss (target lacks the WS under both exact and normalized
#   matching -- Defect 3, deliberately unchanged) still skips, but the
#   skip is no longer silent: it now logs an unconditional warning
#   mirroring BaseOperations._apply_props_loop's own Defect 3 fix, closing
#   the "one sync operation, two different outcomes" asymmetry that would
#   otherwise exist between the shared multistring path (warns) and this
#   site (previously silent). See TestTranslationsOCGenuineMiss's
#   test_absent_target_ws_logs_a_warning / test_hit_paths_do_not_log_a_warning.
#
#   All tests here call the real ExampleOperations.ApplySyncableProperties
#   against a fabricated project + fabricated ILexExampleSentence-shaped
#   item -- no real LCM writes, no requires_live_project marker.
#   TsStringUtils.MakeString(text, handle) IS the real SIL.LCModel
#   implementation (confirmed to work with an arbitrary int handle and no
#   live project open); everything else the loop touches
#   (WritingSystems.GetAll, the ServiceLocator/ICmTranslationFactory
#   pairing, TranslationTagsOA.PossibilitiesOS, TranslationsOC itself) is
#   faked. The ExampleOperations import is deferred into a fixture
#   (matching tests/operations/test_issue266_phoneme_ws_resolution.py's
#   convention) so this file collects cleanly even before the
#   session-scoped FieldWorks init fixture has run.
#
#   See also tests/operations/test_issue250_defect4_ws_resolution.py
#   Section A (the pure _resolve_ws_handle behaviour) and
#   tests/operations/test_issue266_phoneme_ws_resolution.py (the sibling
#   site's own integration-point coverage, same shape minus the orphan
#   concern).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import contextlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Lazy import: ExampleOperations.py imports SIL.LCModel types at module
# scope. Deferring the import into a fixture used by each test guarantees
# the autouse session fixture (tests/conftest.py::initialize_flex_for_tests)
# has already run and registered the CLR assemblies.
# ---------------------------------------------------------------------------


@pytest.fixture()
def example_ops_class():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    from flexicon.code.Lexicon.ExampleOperations import ExampleOperations

    return ExampleOperations


@pytest.fixture()
def fp_parameter_error():
    from flexicon.code.FLExProject import FP_ParameterError

    return FP_ParameterError


TYPE_GUID = "11111111-1111-1111-1111-111111111111"


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


class _FakeMultiString:
    """Stand-in for ICmTranslation.Translation (IMultiString): a
    WS-handle-keyed store, tracking every set_String call."""

    def __init__(self):
        self._store = {}

    def set_String(self, handle, tss):
        self._store[handle] = tss

    def get_String(self, handle):
        return self._store.get(handle)


class _FakeTranslation:
    """Stand-in for a created ICmTranslation."""

    def __init__(self, type_obj):
        self.TypeRA = type_obj
        self.Translation = _FakeMultiString()


class _FakeTranslationsOC(list):
    """Stand-in for the owning-collection ICmTranslationOC: supports the
    two members the loop under test actually calls, Clear()/Add(), while
    staying a plain list everywhere else so tests can assert on it
    directly (e.g. ``len(item.TranslationsOC)``)."""

    def Clear(self):
        self.clear()

    def Add(self, obj):
        self.append(obj)


class _FakeItem:
    """Stand-in for the target ILexExampleSentence. Reference is never
    exercised by these tests (props never include "Reference")."""

    def __init__(self):
        self.TranslationsOC = _FakeTranslationsOC()


class _FakeTranslationFactory:
    """Stand-in for ICmTranslationFactory. Tracks every Create() call so
    tests can assert exactly how many ICmTranslation objects were ever
    minted -- the orphan regression test's core assertion is that this
    stays at ZERO calls when resolution raises."""

    def __init__(self):
        self.create_calls = []

    def Create(self, item, type_obj):
        self.create_calls.append((item, type_obj))
        return _FakeTranslation(type_obj)


class _FakeServiceLocator:
    def __init__(self, factory):
        self._factory = factory

    def GetService(self, factory_type):
        # The real call site passes ICmTranslationFactory as the lookup
        # key; the fake ignores the argument and always returns the one
        # fake factory, exactly like a real ServiceLocator scoped to a
        # single-factory-type test would.
        return self._factory


class _FakeInnerProject:
    def __init__(self, factory):
        self.ServiceLocator = _FakeServiceLocator(factory)
        self.DefaultAnalWs = 999  # unused unless "Reference" is in props


class _FakeTypeObj:
    """Stand-in for an ICmPossibility in TranslationTagsOA.PossibilitiesOS.
    ``str(tt.Guid)`` is called by the code under test; a plain str Guid
    round-trips through str() unchanged."""

    def __init__(self, guid_str):
        self.Guid = guid_str


class _FakeTranslationTagsOA:
    def __init__(self, type_objs):
        self.PossibilitiesOS = list(type_objs)


class _FakeLp:
    def __init__(self, type_objs):
        self.TranslationTagsOA = _FakeTranslationTagsOA(type_objs)


class _FakeProject:
    """Minimal project stand-in covering everything
    ApplySyncableProperties (both the ExampleOperations override and the
    BaseOperations super() call it delegates plain/multistring fields to)
    reads before it reaches the TranslationsOC loop under test."""

    def __init__(self, ws_list, type_objs=None, writeEnabled=True):
        self.writeEnabled = writeEnabled
        self.WritingSystems = _FakeWritingSystemsOps(ws_list)
        self.lp = _FakeLp(type_objs if type_objs is not None else [_FakeTypeObj(TYPE_GUID)])
        factory = _FakeTranslationFactory()
        self.project = _FakeInnerProject(factory)
        self._factory = factory  # convenience handle for tests
        # Never invoked in these tests (remaining_props is always empty --
        # every test's props dict contains only "TranslationsOC" -- and
        # _apply_props_loop only calls this when a plain-str property is
        # present), but BaseOperations.ApplySyncableProperties reads the
        # attribute unconditionally when building the call to
        # _apply_props_loop, so it must exist.
        self.GetDefaultAnalysisWSHandle = lambda: None


def _make_ops(example_ops_class, ws_list, type_objs=None):
    """Build an ExampleOperations instance wired to a fake project, with
    _TransactionCM replaced by a no-op context manager so no real LCM
    transaction machinery (UndoableUnitOfWorkHelper / ActionHandlerAccessor)
    is required. _TransactionCM is a plain instance method (not a data
    descriptor), so instance-dict assignment shadows it exactly like the
    SetBasicIPASymbol/GetBasicIPASymbol fakes in
    test_issue266_phoneme_ws_resolution.py.
    """
    project = _FakeProject(ws_list, type_objs)
    ops = example_ops_class(project)
    ops._TransactionCM = lambda label: contextlib.nullcontext()
    return ops, project


def _apply(ops, translations_data, ws_map=None, fill_gaps=False):
    """Call the real ApplySyncableProperties with only a TranslationsOC
    entry in props (no "Reference"), returning the target item so tests
    can inspect item.TranslationsOC afterward."""
    item = _FakeItem()
    props = {"TranslationsOC": translations_data}
    ops.ApplySyncableProperties(item, props, ws_map=ws_map, fill_gaps=fill_gaps)
    return item


def _trans_entry(translation_dict, type_guid=TYPE_GUID):
    return {"Translation": translation_dict, "TypeRA": type_guid}


# ============================================================================
# Exact match (zero-regression basis)
# ============================================================================


class TestTranslationsOCExactMatch:
    def test_exact_match_resolves_and_writes(self, example_ops_class):
        ops, project = _make_ops(example_ops_class, [_FakeWs("en-US", 42)])

        item = _apply(ops, [_trans_entry({"en-US": "hello"})])

        assert len(item.TranslationsOC) == 1
        trans = item.TranslationsOC[0]
        assert trans.Translation._store[42].Text == "hello"


# ============================================================================
# Normalized fallback: case and separator divergence (the bug being fixed)
# ============================================================================


class TestTranslationsOCNormalizedFallback:
    def test_case_divergent_alt_resolves(self, example_ops_class):
        """Source spells 'etu' (lowercase); target's real ws.Id is 'ETU'.
        Pre-fix this alt was silently dropped -- the exact bug in #267."""
        ops, project = _make_ops(example_ops_class, [_FakeWs("ETU", 7)])

        item = _apply(ops, [_trans_entry({"etu": "gloss text"})])

        assert len(item.TranslationsOC) == 1
        trans = item.TranslationsOC[0]
        assert trans.Translation._store[7].Text == "gloss text"

    def test_separator_divergent_alt_resolves(self, example_ops_class):
        """Source spells 'en_US' (underscore); target's real ws.Id is
        'en-US' (hyphen)."""
        ops, project = _make_ops(example_ops_class, [_FakeWs("en-US", 42)])

        item = _apply(ops, [_trans_entry({"en_US": "hello"})])

        assert len(item.TranslationsOC) == 1
        assert item.TranslationsOC[0].Translation._store[42].Text == "hello"

    def test_ws_map_indirection_then_normalized_resolves(self, example_ops_class):
        """Normalization applies AFTER the ws_map indirection (spec 250
        C-D4-5): ws_map points 'en' at 'en-us', but the target's real
        ws.Id is 'en-US'."""
        ops, project = _make_ops(example_ops_class, [_FakeWs("en-US", 42)])

        item = _apply(
            ops, [_trans_entry({"en": "hello"})], ws_map={"en": "en-us"}
        )

        assert item.TranslationsOC[0].Translation._store[42].Text == "hello"

    def test_exact_match_preferred_over_normalized_when_both_present(
        self, example_ops_class
    ):
        """If the exact-case key is ALSO present, it must win -- the
        normalized fallback must never be consulted."""
        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-us", 1), _FakeWs("en-US", 2)]
        )

        item = _apply(ops, [_trans_entry({"en-us": "hello"})])

        assert item.TranslationsOC[0].Translation._store[1].Text == "hello"
        assert 2 not in item.TranslationsOC[0].Translation._store


# ============================================================================
# Genuine miss (Defect 3, deliberately unchanged -- silent skip). This is
# pre-existing behaviour, unrelated to the orphan concern: a translation
# entry whose alts all miss still gets created with zero alts, exactly as
# it did pre-fix.
# ============================================================================


class TestTranslationsOCGenuineMiss:
    def test_absent_target_ws_is_silently_skipped(self, example_ops_class):
        ops, project = _make_ops(example_ops_class, [_FakeWs("en-US", 1)])

        item = _apply(ops, [_trans_entry({"de-DE": "should-be-dropped"})])

        # The ICmTranslation is still created (TypeRA-only translations are
        # a legitimate pre-existing shape) but carries no alts.
        assert len(item.TranslationsOC) == 1
        assert item.TranslationsOC[0].Translation._store == {}

    def test_absent_target_ws_logs_a_warning(self, example_ops_class, caplog):
        """The drop is no longer silent (mirrors BaseOperations
        ._apply_props_loop's own Defect 3 fix): an unconditional warning
        names the source ws id, the resolved target id, and the owning
        example's type/Hvo -- there is no translation Hvo to name yet,
        since the ICmTranslation is not created until after resolution."""
        ops, project = _make_ops(example_ops_class, [_FakeWs("en-US", 1)])

        with caplog.at_level("WARNING"):
            _apply(ops, [_trans_entry({"de-DE": "should-be-dropped"})])

        assert len(caplog.records) == 1
        msg = caplog.records[0].getMessage()
        assert "de-DE" in msg
        assert "ICmTranslation.Translation" in msg

    def test_hit_paths_do_not_log_a_warning(self, example_ops_class, caplog):
        """No warning on an exact hit or a normalized (case/separator)
        fallback hit -- only a genuine miss is diagnostic-worthy."""
        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-US", 1), _FakeWs("ETU", 7)]
        )

        with caplog.at_level("WARNING"):
            _apply(
                ops,
                [_trans_entry({"en-US": "exact", "etu": "case-divergent"})],
            )

        assert caplog.records == []


# ============================================================================
# Ambiguity: new failure mode introduced by routing through
# _resolve_ws_handle (spec 250 C-D4-3 step 2b) -- must raise, never guess.
# ============================================================================


class TestTranslationsOCAmbiguity:
    def test_ambiguous_normalized_match_raises(
        self, example_ops_class, fp_parameter_error
    ):
        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-US", 1), _FakeWs("en-us", 2)]
        )

        with pytest.raises(fp_parameter_error) as excinfo:
            _apply(ops, [_trans_entry({"en_us": "should-not-write"})])

        msg = str(excinfo.value)
        assert "en-US" in msg and "en-us" in msg, (
            f"Ambiguity error must name BOTH ambiguous spellings; got: {msg!r}"
        )

    def test_keys_normalizing_together_sharing_one_handle_do_not_raise(
        self, example_ops_class
    ):
        """Two spellings that normalize together but share the SAME handle
        are not ambiguous (deduped by handle before counting)."""
        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-US", 1), _FakeWs("en-us", 1)]
        )

        item = _apply(ops, [_trans_entry({"en_US": "hello"})])

        assert item.TranslationsOC[0].Translation._store[1].Text == "hello"


# ============================================================================
# THE REQUIRED REGRESSION TEST (issue #267's own mandate): forcing the
# ambiguous-spelling raise mid-loop must leave NO orphaned ICmTranslation
# with zero alts owned by the example. This is exactly the bug the naive
# one-line `_resolve_ws_handle` substitution would introduce -- it would
# create/attach the ICmTranslation BEFORE resolving alts, so the raise
# would leave a zero-alt object sitting in TranslationsOC. Against the
# fix under test (pre-resolve before create/attach), this test passes
# because the factory is never even called.
# ============================================================================


class TestApplyTranslationsOCOrphanRegression:
    def test_ambiguous_alt_leaves_no_orphaned_translation(
        self, example_ops_class, fp_parameter_error
    ):
        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-US", 1), _FakeWs("en-us", 2)]
        )

        with pytest.raises(fp_parameter_error):
            _apply(ops, [_trans_entry({"en_us": "should-not-write"})])

        # The critical assertion: ICmTranslationFactory.Create was NEVER
        # called for this entry, because resolution happens before
        # creation/attachment. A naive one-line substitution that resolved
        # inside the existing post-Create loop would have called Create()
        # once and left that ICmTranslation attached with zero alts.
        assert project._factory.create_calls == [], (
            "No ICmTranslation may be created before its writing systems "
            "are fully resolved -- an ambiguous spelling must raise BEFORE "
            "ICmTranslationFactory.Create, not after."
        )

    def test_ambiguous_alt_in_second_of_two_translations_leaves_first_intact_and_no_orphan(
        self, example_ops_class, fp_parameter_error
    ):
        """A prior, fully-resolved translation in the same TranslationsOC
        list is unaffected by a later entry's raise (the loop has no
        per-entry transaction of its own -- each dict is applied as it is
        reached) -- but the SECOND (raising) entry must still create zero
        ICmTranslation objects, i.e. no zero-alt orphan for the entry that
        actually raised."""
        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-US", 1), _FakeWs("en-us", 2)]
        )

        item = _FakeItem()
        props = {
            "TranslationsOC": [
                _trans_entry({"en-US": "first, resolves fine"}),
                _trans_entry({"en_us": "second, ambiguous -- raises"}),
            ]
        }

        with pytest.raises(fp_parameter_error):
            ops.ApplySyncableProperties(item, props)

        # Exactly one ICmTranslation was ever created (the first entry);
        # the second entry's ambiguity raised before its own Create() call.
        assert len(project._factory.create_calls) == 1
        assert len(item.TranslationsOC) == 1
        assert item.TranslationsOC[0].Translation._store[1].Text == (
            "first, resolves fine"
        )


# ============================================================================
# Shared index-cache identity (spec 250 C-D4-4): the TranslationsOC loop
# must build ONE cache dict per ApplySyncableProperties call and pass the
# SAME object to every _resolve_ws_handle call within that one invocation
# -- across every translation entry and every alt -- never a fresh one per
# entry or per alt.
# ============================================================================


class TestTranslationsOCSharedIndexCache:
    def test_same_index_cache_object_reused_across_alts_and_entries_in_one_call(
        self, example_ops_class, monkeypatch
    ):
        import flexicon.code.Lexicon.ExampleOperations as example_ops_module

        real_resolve = example_ops_module._resolve_ws_handle
        seen_cache_ids = []

        def _spy(target_ws_by_id, tgt_ws_id, _index_cache=None):
            seen_cache_ids.append(id(_index_cache))
            return real_resolve(target_ws_by_id, tgt_ws_id, _index_cache=_index_cache)

        monkeypatch.setattr(example_ops_module, "_resolve_ws_handle", _spy)

        ops, project = _make_ops(
            example_ops_class, [_FakeWs("en-US", 1), _FakeWs("fr-FR", 2)]
        )

        _apply(
            ops,
            [
                _trans_entry({"en-us": "a"}),
                _trans_entry({"fr-fr": "b"}),
            ],
        )

        assert len(seen_cache_ids) == 2, (
            "Expected one _resolve_ws_handle call per alt across both "
            "translation entries."
        )
        assert len(set(seen_cache_ids)) == 1, (
            "The TranslationsOC loop must pass the SAME _index_cache dict "
            "to every _resolve_ws_handle call within one "
            "ApplySyncableProperties invocation (spec 250 C-D4-4), not "
            "rebuild it per translation entry or per alt."
        )

    def test_fresh_index_cache_per_apply_call(self, example_ops_class, monkeypatch):
        """Different ApplySyncableProperties invocations must not leak the
        same cache dict across calls -- each call builds its own."""
        import flexicon.code.Lexicon.ExampleOperations as example_ops_module

        real_resolve = example_ops_module._resolve_ws_handle
        seen_cache_ids = []

        def _spy(target_ws_by_id, tgt_ws_id, _index_cache=None):
            seen_cache_ids.append(id(_index_cache))
            return real_resolve(target_ws_by_id, tgt_ws_id, _index_cache=_index_cache)

        monkeypatch.setattr(example_ops_module, "_resolve_ws_handle", _spy)

        ops, project = _make_ops(example_ops_class, [_FakeWs("en-US", 1)])

        _apply(ops, [_trans_entry({"en-us": "a"})])
        _apply(ops, [_trans_entry({"en-us": "b"})])

        assert len(set(seen_cache_ids)) == 2, (
            "Each ApplySyncableProperties call must build its own "
            "_ws_resolve_cache; reusing one across calls would be an "
            "instance-level leak, not a per-apply-call memoization."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
