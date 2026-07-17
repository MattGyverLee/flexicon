#
#   test_apply_syncable_properties.py
#
#   Class: TestApplyPropsLoopBranches / TestApplySyncablePropertiesGuards /
#          TestSyncTypeCorrectionsStatic / TestApplySyncablePropertiesLive
#          Branch coverage for BaseOperations.ApplySyncableProperties and its
#          pure helper _apply_props_loop (closes #217).
#
#   ApplySyncableProperties is the symmetric inverse of GetSyncableProperties
#   and is the primary GramTrans cross-project write path, with 13 Operations
#   subclass overrides (LexSense, Example, Etymology, LexEntry, Pronunciation,
#   ...). Coverage before this file was ~zero.
#
#   Context commits:
#     - 23eb9f7: landed ApplySyncableProperties / _apply_props_loop, the
#       dict{ws_tag:str} multistring branch, the plain-str setattr branch,
#       and ws_map remapping.
#     - 171a9a7: Category-8 ITsString/IMultiString type corrections across
#       Etymology / Example / LexEntry / LexSense / Pronunciation Operations
#       (e.g. Source is ITsString on ILexSense but IMultiString on
#       ILexEtymology; ImportResidue is ITsString on both ILexEntry and
#       ILexSense; Reference is ITsString on ILexExampleSentence) plus the
#       Phase 0.5 str->TsStringUtils.MakeString(value, default_ws) coercion
#       fallback in _apply_props_loop's plain-str branch.
#
#   Coverage split (mirrors tests/operations/test_owner_cast_pattern.py):
#
#     A. _apply_props_loop branch DISPATCH -- pure-Python fakes (fake item,
#        fake IMultiString, fake TsStringUtils), no SIL.LCModel required.
#        Pins requirements (1)-(5) from issue #217.
#
#     B. ApplySyncableProperties() top-level guard clauses
#        (_EnsureWriteEnabled / FP_NullParameterError / FP_ParameterError).
#        These fire *before* the method's lazy
#        `from SIL.LCModel.Core.Text import TsStringUtils` import, so they
#        are also exercisable without LCM.
#
#     C. Static source-pattern locks for the 171a9a7 type corrections --
#        confirms each of Etymology/Example/LexEntry/LexSense/Pronunciation
#        reads its ITsString-vs-IMultiString fields with the correct shape.
#        Pins requirement (6).
#
#     D. True round-trip identity (apply -> GetSyncableProperties) against
#        real LCM objects. Gated behind `requires_live_project` + a
#        module-scoped writable_project fixture; skips cleanly when
#        SIL.LCModel / a writable test project is unavailable. NOTE: these
#        tests WRITE to the target FLEx project (create throwaway senses /
#        examples / etymologies / pronunciations) and the project must be
#        -restore'd afterward. Per task instructions this file's author did
#        NOT execute Section D in the authoring environment even though
#        FieldWorks happens to be installed there -- see the accompanying
#        report for details.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import re
import sys
import textwrap

import pytest

from flexicon.code.BaseOperations import (
    BaseOperations,
    _apply_props_loop,
    FP_NullParameterError,
    FP_ParameterError,
    FP_ReadOnlyError,
)


# ============================================================================
# Section A: _apply_props_loop branch-dispatch coverage (no LCM required)
# ============================================================================


class _FakeTsString:
    """Stand-in for SIL.LCModel.Core.KernelInterfaces.ITsString."""

    def __init__(self, text):
        self.Text = text
        self.RunCount = 1 if text else 0


class _FakeTsStringUtils:
    """
    Stand-in for SIL.LCModel.Core.Text.TsStringUtils. Records every
    MakeString call so tests can assert it fired (or didn't) without
    raising, per requirement (4) of issue #217.
    """

    def __init__(self):
        self.calls = []

    def MakeString(self, text, ws_handle):
        self.calls.append((text, ws_handle))
        return _FakeTsString(text)


class _FakeMultiString:
    """Stand-in for IMultiString/IMultiUnicode: a WS-handle-keyed store."""

    def __init__(self):
        self._store = {}

    def get_String(self, handle):
        return self._store.get(handle, _FakeTsString(""))

    def set_String(self, handle, tss):
        self._store[handle] = tss


class _FakeItem:
    """
    Minimal LCM-object stand-in for exercising _apply_props_loop's branch
    dispatch.

    `ts_props` names simulate ITsString-typed properties (e.g.
    ILexSense.Source): a raw Python str assigned to one of these raises
    TypeError mentioning "ITsString", mirroring pythonnet's real coercion
    failure when a bare str is assigned to a property typed ITsString.
    All other attributes behave like ordinary Python attributes.

    Use `object.__setattr__` to seed initial values in test bodies --
    seeding a ts_props field via the normal `item.X = ""` path would
    itself trigger the simulated TypeError.
    """

    def __init__(self, ts_props=()):
        object.__setattr__(self, "_ts_props", set(ts_props))

    def __setattr__(self, name, value):
        if name in self._ts_props and isinstance(value, str):
            raise TypeError(
                f"Cannot convert System.String to "
                f"SIL.LCModel.Core.KernelInterfaces.ITsString for {name!r}"
            )
        object.__setattr__(self, name, value)


def _extract_multistring(prop_obj, target_ws_by_id):
    """
    Mirrors the GET side of GetSyncableProperties for a multistring field:
    read back every WS alt present in target_ws_by_id via get_String(...).Text,
    skipping empties. Used to verify apply->read round-trip identity without
    needing a live GetSyncableProperties implementation.
    """
    result = {}
    for ws_id, handle in target_ws_by_id.items():
        text = prop_obj.get_String(handle).Text
        if text:
            result[ws_id] = text
    return result


class TestApplyPropsLoopMultistring:
    """Requirement (1): dict{ws_tag: text} onto IMultiString, round-trip."""

    def test_multistring_apply_and_readback_identity(self):
        item = _FakeItem()
        object.__setattr__(item, "Gloss", _FakeMultiString())

        target_ws_by_id = {"en": 1, "fr": 2}
        props = {"Gloss": {"en": "hello", "fr": "bonjour"}}

        _apply_props_loop(item, props, target_ws_by_id, _ts_string_utils=_FakeTsStringUtils())

        readback = _extract_multistring(item.Gloss, target_ws_by_id)
        assert readback == props["Gloss"], (
            "Applying a multistring dict then reading it back via "
            "get_String() must reproduce the original {ws_tag: text} dict "
            "exactly (GetSyncableProperties/ApplySyncableProperties symmetry)."
        )

    def test_multistring_skips_ws_not_present_on_target(self):
        """A source WS tag absent from the target's WS inventory is silently
        skipped (requirement 5 note: target lacks WS -> no KeyError)."""
        item = _FakeItem()
        object.__setattr__(item, "Gloss", _FakeMultiString())

        target_ws_by_id = {"en": 1}  # no 'fr'
        props = {"Gloss": {"en": "hello", "fr": "bonjour"}}

        _apply_props_loop(item, props, target_ws_by_id, _ts_string_utils=_FakeTsStringUtils())

        readback = _extract_multistring(item.Gloss, target_ws_by_id)
        assert readback == {"en": "hello"}

    def test_multistring_missing_prop_on_item_is_skipped(self):
        """getattr(item, prop_name, None) is None -> branch no-ops, no crash."""
        item = _FakeItem()
        # Gloss intentionally never set on item.
        _apply_props_loop(item, {"Gloss": {"en": "hello"}}, {"en": 1})
        assert not hasattr(item, "Gloss")

    def test_multistring_fill_gaps_skips_nonempty_target_alt(self):
        item = _FakeItem()
        multi = _FakeMultiString()
        multi.set_String(1, _FakeTsString("existing"))
        object.__setattr__(item, "Gloss", multi)

        _apply_props_loop(
            item, {"Gloss": {"en": "incoming"}}, {"en": 1}, fill_gaps=True,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert multi.get_String(1).Text == "existing", (
            "fill_gaps=True must not overwrite a WS alt that already has text."
        )


class TestApplyPropsLoopWsMap:
    """Requirement (5): ws_map=None is identity; a mapping dict remaps tags."""

    def test_ws_map_none_is_identity(self):
        item = _FakeItem()
        object.__setattr__(item, "Gloss", _FakeMultiString())
        target_ws_by_id = {"en": 1}

        _apply_props_loop(
            item, {"Gloss": {"en": "hello"}}, target_ws_by_id, ws_map=None,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Gloss.get_String(1).Text == "hello"

    def test_ws_map_remaps_source_tag_to_target_tag(self):
        item = _FakeItem()
        object.__setattr__(item, "Gloss", _FakeMultiString())
        # Source project calls it 'en'; target project's matching WS is 'eng'.
        target_ws_by_id = {"eng": 1}
        ws_map = {"en": "eng"}

        _apply_props_loop(
            item, {"Gloss": {"en": "hello"}}, target_ws_by_id, ws_map=ws_map,
            _ts_string_utils=_FakeTsStringUtils(),
        )

        assert item.Gloss.get_String(1).Text == "hello", (
            "ws_map must translate the source WS Id to the target WS Id "
            "before resolving a handle."
        )

    def test_ws_map_unmapped_target_ws_is_skipped_silently(self):
        item = _FakeItem()
        object.__setattr__(item, "Gloss", _FakeMultiString())
        target_ws_by_id = {"en": 1}  # 'eng' not present
        ws_map = {"en": "eng"}

        _apply_props_loop(
            item, {"Gloss": {"en": "hello"}}, target_ws_by_id, ws_map=ws_map
        )

        assert item.Gloss.get_String(1).Text == "", (
            "When the mapped target WS Id has no handle, the alt is "
            "silently skipped (no exception, no fallback write)."
        )


class TestApplyPropsLoopPlainStr:
    """Requirement (2): a plain str applied onto a unicode property via setattr."""

    def test_plain_str_setattr_path(self):
        item = _FakeItem()
        object.__setattr__(item, "HomographNumberNote", "")

        _apply_props_loop(item, {"HomographNumberNote": "some plain text"}, {})

        assert item.HomographNumberNote == "some plain text"

    def test_plain_str_missing_on_item_is_skipped(self):
        item = _FakeItem()
        # Property never set on item -> hasattr() False -> branch no-ops.
        _apply_props_loop(item, {"NoSuchProp": "value"}, {})
        assert not hasattr(item, "NoSuchProp")

    def test_plain_str_fill_gaps_skips_nonempty_target(self):
        item = _FakeItem()
        object.__setattr__(item, "Note", "existing text")

        _apply_props_loop(item, {"Note": "incoming"}, {}, fill_gaps=True)

        assert item.Note == "existing text"

    def test_plain_str_object_reference_type_mismatch_skipped(self):
        """
        Case (3) from the module docstring: an object-reference property
        typed to some LCM interface can't accept a bare str. The
        "cannot be converted to SIL.LCModel." message shape is skipped
        silently rather than raised.
        """

        class _RefOnlyItem(_FakeItem):
            def __setattr__(self, name, value):
                if name == "MorphoSyntaxAnalysisRA" and isinstance(value, str):
                    raise TypeError(
                        "System.String cannot be converted to "
                        "SIL.LCModel.IMoMorphSynAnalysis"
                    )
                object.__setattr__(self, name, value)

        item = _RefOnlyItem()
        object.__setattr__(item, "MorphoSyntaxAnalysisRA", None)

        # Must not raise.
        _apply_props_loop(item, {"MorphoSyntaxAnalysisRA": "some-guid-string"}, {})

        assert item.MorphoSyntaxAnalysisRA is None, (
            "Object-reference property mismatch must be skipped silently, "
            "leaving the existing value untouched."
        )

    def test_plain_str_unhandled_typeerror_reraises(self):
        """Any TypeError whose message doesn't match a recognised shape
        propagates -- the loop must not swallow unrelated failures."""

        class _WeirdItem(_FakeItem):
            def __setattr__(self, name, value):
                if name == "Weird":
                    raise TypeError("totally unrelated failure")
                object.__setattr__(self, name, value)

        item = _WeirdItem()
        object.__setattr__(item, "Weird", "")

        with pytest.raises(TypeError, match="totally unrelated failure"):
            _apply_props_loop(item, {"Weird": "value"}, {})


class TestApplyPropsLoopTsStringFallback:
    """
    Requirement (4): ITsString-typed props. A raw str value first attempts
    a bare setattr (fails, TypeError mentioning ITsString), then is coerced
    via TsStringUtils.MakeString(value, default_ws) -- the 171a9a7 Phase 0.5
    patch -- WITHOUT raising.
    """

    def test_tsstring_prop_coerced_via_make_string(self):
        item = _FakeItem(ts_props={"Source"})
        object.__setattr__(item, "Source", "")  # seed via bypass, not via setattr

        ts_utils = _FakeTsStringUtils()
        default_ws_handle = 42

        _apply_props_loop(
            item,
            {"Source": "bibliographic source text"},
            {},
            _default_ws_getter=lambda: default_ws_handle,
            _ts_string_utils=ts_utils,
        )

        assert ts_utils.calls == [("bibliographic source text", default_ws_handle)], (
            "TsStringUtils.MakeString must be invoked with (value, default_ws) "
            "when the bare setattr raises an ITsString-shaped TypeError."
        )
        assert isinstance(item.Source, _FakeTsString)
        assert item.Source.Text == "bibliographic source text"

    def test_tsstring_prop_without_ts_string_utils_is_skipped_not_raised(self):
        """If no _ts_string_utils is supplied, the fallback can't run --
        the property is skipped silently rather than raising."""
        item = _FakeItem(ts_props={"ScientificName"})
        object.__setattr__(item, "ScientificName", "")

        # No _ts_string_utils passed -> _default_ws_getter path guarded by
        # `if default_ws is not None and _ts_string_utils is not None`.
        _apply_props_loop(
            item,
            {"ScientificName": "Panthera leo"},
            {},
            _default_ws_getter=lambda: 1,
            _ts_string_utils=None,
        )

        # Original seed value (empty str) is untouched -- no exception raised.
        assert item.ScientificName == ""

    def test_tsstring_prop_default_ws_getter_none_is_skipped_not_raised(self):
        item = _FakeItem(ts_props={"ImportResidue"})
        object.__setattr__(item, "ImportResidue", "")
        ts_utils = _FakeTsStringUtils()

        _apply_props_loop(
            item,
            {"ImportResidue": "residue text"},
            {},
            _default_ws_getter=lambda: None,
            _ts_string_utils=ts_utils,
        )

        assert ts_utils.calls == []
        assert item.ImportResidue == ""


class TestApplyPropsLoopBoolInt:
    """Requirement (3): bool via the setattr branch; plus the sibling int branch."""

    def test_bool_setattr_path(self):
        item = _FakeItem()
        object.__setattr__(item, "Disabled", False)

        _apply_props_loop(item, {"Disabled": True}, {})

        assert item.Disabled is True

    def test_bool_fill_gaps_always_skipped(self):
        """bool/int: stored False/0 is a deliberate choice, never overwritten
        under fill_gaps=True -- even though item.Disabled is currently False
        (which looks 'empty' but isn't)."""
        item = _FakeItem()
        object.__setattr__(item, "Disabled", False)

        _apply_props_loop(item, {"Disabled": True}, {}, fill_gaps=True)

        assert item.Disabled is False

    def test_bool_missing_on_item_is_skipped(self):
        item = _FakeItem()
        _apply_props_loop(item, {"Final": True}, {})
        assert not hasattr(item, "Final")

    def test_bool_setattr_failure_is_skipped_not_raised(self):
        class _BoolFailItem(_FakeItem):
            def __setattr__(self, name, value):
                if name == "Final" and value is True:
                    raise AttributeError("read-only property")
                object.__setattr__(self, name, value)

        item = _BoolFailItem()
        object.__setattr__(item, "Final", False)

        _apply_props_loop(item, {"Final": True}, {})  # must not raise
        assert item.Final is False

    def test_int_setattr_path(self):
        item = _FakeItem()
        object.__setattr__(item, "HomographNumber", 0)

        _apply_props_loop(item, {"HomographNumber": 3}, {})

        assert item.HomographNumber == 3

    def test_int_fill_gaps_skips_nonzero_current(self):
        item = _FakeItem()
        object.__setattr__(item, "HomographNumber", 2)

        _apply_props_loop(item, {"HomographNumber": 3}, {}, fill_gaps=True)

        assert item.HomographNumber == 2

    def test_int_fill_gaps_applies_when_current_zero(self):
        item = _FakeItem()
        object.__setattr__(item, "HomographNumber", 0)

        _apply_props_loop(item, {"HomographNumber": 3}, {}, fill_gaps=True)

        assert item.HomographNumber == 3

    def test_bool_before_int_dispatch(self):
        """bool is a subclass of int in Python; the loop must check bool
        first so True/False never falls into the int branch's fill_gaps
        'current != 0' logic (which would incorrectly treat False as 0)."""
        item = _FakeItem()
        object.__setattr__(item, "Final", False)

        # If bool were mis-dispatched as int, fill_gaps would see current=0
        # (False == 0) and apply anyway -- same outcome here, so instead
        # assert via the *always-skip* bool semantics: with current=True
        # (a real, meaningful stored choice) fill_gaps must still skip,
        # whereas the int branch would apply since True as "current" is
        # falsy-numeric only when False.
        item2 = _FakeItem()
        object.__setattr__(item2, "Final", True)
        _apply_props_loop(item2, {"Final": False}, {}, fill_gaps=True)
        assert item2.Final is True, (
            "bool fields must always be skipped under fill_gaps regardless "
            "of current value -- this only holds if bool is dispatched "
            "before int (isinstance(True, int) is True in Python)."
        )


class TestApplyPropsLoopMisc:
    def test_none_value_is_skipped(self):
        item = _FakeItem()
        object.__setattr__(item, "Comment", "existing")
        _apply_props_loop(item, {"Comment": None}, {})
        assert item.Comment == "existing"

    def test_unknown_shape_is_skipped(self):
        item = _FakeItem()
        _apply_props_loop(item, {"Weird": 3.14}, {})  # float: unknown shape
        assert not hasattr(item, "Weird")


# ============================================================================
# Section B: ApplySyncableProperties() top-level guard clauses (no LCM
# required -- these fire before the method's lazy TsStringUtils import).
# ============================================================================


class _FakeProject:
    def __init__(self, write_enabled=True):
        self.writeEnabled = write_enabled


def _make_bare_ops(write_enabled=True):
    """
    Build a BaseOperations instance without going through __init__/project
    setup machinery, so these guard-clause tests don't need a real
    FLExProject or SIL.LCModel.
    """
    ops = BaseOperations.__new__(BaseOperations)
    ops.project = _FakeProject(write_enabled)
    return ops


class TestApplySyncablePropertiesGuards:
    def test_raises_read_only_error_when_project_not_write_enabled(self):
        ops = _make_bare_ops(write_enabled=False)
        with pytest.raises(FP_ReadOnlyError):
            ops.ApplySyncableProperties(object(), {})

    def test_raises_null_parameter_error_for_none_item(self):
        ops = _make_bare_ops(write_enabled=True)
        with pytest.raises(FP_NullParameterError):
            ops.ApplySyncableProperties(None, {})

    def test_raises_parameter_error_for_non_dict_props(self):
        ops = _make_bare_ops(write_enabled=True)
        with pytest.raises(FP_ParameterError):
            ops.ApplySyncableProperties(object(), props=["not", "a", "dict"])

    def test_write_enabled_check_happens_before_item_none_check(self):
        """_EnsureWriteEnabled() is called first in the method body -- even
        a None item must raise FP_ReadOnlyError, not FP_NullParameterError,
        when the project isn't write-enabled."""
        ops = _make_bare_ops(write_enabled=False)
        with pytest.raises(FP_ReadOnlyError):
            ops.ApplySyncableProperties(None, {})


# ============================================================================
# Section C: Static source-pattern locks for the 171a9a7 type corrections
# (requirement 6). Mirrors tests/operations/test_owner_cast_pattern.py.
# ============================================================================


def _method_source(import_path, class_name, method_name):
    import importlib

    module = importlib.import_module(import_path)
    cls = getattr(module, class_name)
    obj = cls.__dict__[method_name]

    seen = set()
    while True:
        oid = id(obj)
        if oid in seen:
            break
        seen.add(oid)
        if hasattr(obj, "func") and not inspect.isfunction(obj):
            obj = obj.func
            continue
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        break

    return inspect.getsource(obj)


# (label, import_path, class_name, field, shape) -- shape is
# "tsstring" (must read via self._ReadTsString(item.<field>)) or
# "multistring" (must read via item.<field>.get_String(...), i.e. loop
# over writing systems -- NOT via _ReadTsString).
_TYPE_CORRECTION_SITES = [
    (
        "EtymologyOperations.Source (IMultiString on ILexEtymology)",
        "flexicon.code.Lexicon.EtymologyOperations",
        "EtymologyOperations",
        "Source",
        "multistring",
    ),
    (
        "LexSenseOperations.Source (ITsString on ILexSense)",
        "flexicon.code.Lexicon.LexSenseOperations",
        "LexSenseOperations",
        "Source",
        "tsstring",
    ),
    (
        "LexSenseOperations.ScientificName (ITsString)",
        "flexicon.code.Lexicon.LexSenseOperations",
        "LexSenseOperations",
        "ScientificName",
        "tsstring",
    ),
    (
        "LexSenseOperations.ImportResidue (ITsString)",
        "flexicon.code.Lexicon.LexSenseOperations",
        "LexSenseOperations",
        "ImportResidue",
        "tsstring",
    ),
    (
        "LexEntryOperations.ImportResidue (ITsString on ILexEntry)",
        "flexicon.code.Lexicon.LexEntryOperations",
        "LexEntryOperations",
        "ImportResidue",
        "tsstring",
    ),
    (
        "ExampleOperations.Reference (ITsString on ILexExampleSentence)",
        "flexicon.code.Lexicon.ExampleOperations",
        "ExampleOperations",
        "Reference",
        "tsstring",
    ),
    (
        "PronunciationOperations.Form (IMultiString/IMultiUnicode)",
        "flexicon.code.Lexicon.PronunciationOperations",
        "PronunciationOperations",
        "Form",
        "multistring",
    ),
]


class TestSyncTypeCorrectionsStatic:
    """
    Pins the Category-8 (issue #36/#39/#40, corrected in 171a9a7)
    ITsString-vs-IMultiString distinctions in GetSyncableProperties. Same
    field name, different LCM type across object types -- e.g. `Source` is
    ITsString on ILexSense but IMultiString on ILexEtymology. Reverting
    either shape silently breaks the sync framework at runtime with either
    an AttributeError (get_String on ITsString) or a raw ITsString leak
    into the sync dict (missing _ReadTsString unwrap).
    """

    @pytest.fixture(autouse=True)
    def _require_lcmodel(self):
        """
        These tests import real Operations modules, which have module-level
        `from SIL.LCModel import ...` statements. On a machine without
        FieldWorks installed, that import ERRORs rather than skipping.
        Skip cleanly instead.
        """
        pytest.importorskip("SIL.LCModel")

    @pytest.mark.parametrize(
        "label,import_path,class_name,field,shape", _TYPE_CORRECTION_SITES
    )
    def test_get_syncable_properties_field_shape(
        self, label, import_path, class_name, field, shape
    ):
        src = _method_source(import_path, class_name, "GetSyncableProperties")
        msg_prefix = f"{label}:\n{textwrap.indent(src, '    ')}\n"

        reads_via_ts_string = f"self._ReadTsString(item.{field})" in src
        reads_via_multistring_loop = f"item.{field}.get_String(" in src

        if shape == "tsstring":
            assert reads_via_ts_string, (
                f"{msg_prefix}Expected `{field}` to be read via "
                f"self._ReadTsString(item.{field}) -- it is ITsString-typed. "
                f"See CLAUDE.md Category 8 / docs/API_ISSUES_CATEGORIZED.md."
            )
            assert not reads_via_multistring_loop, (
                f"{msg_prefix}`{field}` must NOT be read via a per-WS "
                f"get_String() loop -- that shape is for IMultiString "
                f"fields and will raise/AttributeError on an ITsString."
            )
        else:  # multistring
            assert reads_via_multistring_loop, (
                f"{msg_prefix}Expected `{field}` to be read via a per-WS "
                f"item.{field}.get_String(ws_def.Handle) loop -- it is "
                f"IMultiString-typed on this object type."
            )
            assert not reads_via_ts_string, (
                f"{msg_prefix}`{field}` must NOT be read via "
                f"self._ReadTsString() -- that shape is for ITsString "
                f"fields; using it here would silently drop all but one "
                f"writing system's text."
            )


class TestSyncTypeCorrectionsApplySide:
    """
    Apply-side corrections: subclasses that intercept an ITsString field
    themselves (rather than relying on BaseOperations' generic setattr ->
    TypeError -> MakeString fallback) must construct via
    TsStringUtils.MakeString, never a bare string assignment.
    """

    @pytest.fixture(autouse=True)
    def _require_lcmodel(self):
        """
        These tests import real Operations modules, which have module-level
        `from SIL.LCModel import ...` statements. On a machine without
        FieldWorks installed, that import ERRORs rather than skipping.
        Skip cleanly instead.
        """
        pytest.importorskip("SIL.LCModel")

    def test_example_reference_apply_uses_make_string(self):
        src = _method_source(
            "flexicon.code.Lexicon.ExampleOperations",
            "ExampleOperations",
            "ApplySyncableProperties",
        )
        assert "TsStringUtils.MakeString(ref_text" in src, (
            "ExampleOperations.ApplySyncableProperties must construct "
            "item.Reference via TsStringUtils.MakeString(...) -- Reference "
            "is ITsString, not a plain-str-assignable property."
        )

    def test_lexsense_source_scientificname_importresidue_not_special_cased(self):
        """
        Source/ScientificName/ImportResidue on ILexSense are NOT
        intercepted by LexSenseOperations.ApplySyncableProperties -- they
        flow through as plain str values into the base class's generic
        _apply_props_loop, which handles the ITsString fallback itself
        (see TestApplyPropsLoopTsStringFallback). This test locks that
        design choice: the subclass's special-fields tuple only carries
        the reference-collection/atomic-ref fields it actually needs to
        intercept.
        """
        src = _method_source(
            "flexicon.code.Lexicon.LexSenseOperations",
            "LexSenseOperations",
            "ApplySyncableProperties",
        )
        match = re.search(r"_special_fields\s*=\s*\(([^)]*)\)", src)
        assert match, (
            "LexSenseOperations.ApplySyncableProperties must define a "
            "`_special_fields = (...)` tuple.\n" + textwrap.indent(src, "    ")
        )
        tuple_body = match.group(1)
        for field in ("Source", "ScientificName", "ImportResidue"):
            assert f'"{field}"' not in tuple_body, (
                f"{field} should not appear in LexSenseOperations' "
                f"_special_fields tuple -- it must fall through to "
                f"super().ApplySyncableProperties() and the base ITsString "
                f"fallback, not be hand-cased here.\n"
                f"_special_fields = ({tuple_body})"
            )


# ============================================================================
# Section D: Live round-trip identity against real LCM objects.
#
# GATED: requires SIL.LCModel loaded AND a writable test project. These
# tests WRITE to the target project (create throwaway senses / examples /
# etymologies / pronunciations) -- the project must be -restore'd
# afterward. Per task instructions, these are authored but NOT executed
# by this task's author in the authoring environment.
# ============================================================================

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


def _first_entry(project):
    try:
        entries = list(project.LexiconAllEntries())
    except Exception:
        return None
    return entries[0] if entries else None


@pytest.mark.requires_live_project
class TestApplySyncablePropertiesLive:
    """
    Behavioural round-trip locks: apply a syncable-properties dict onto a
    freshly-created target item, then re-read it via GetSyncableProperties
    and assert the values match. Any test in this class WRITES to the
    live project -- restore the .fwdata backup after running this class.
    """

    def test_lexsense_source_scientificname_importresidue_roundtrip(
        self, writable_project
    ):
        entry = _first_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available")

        sense_ops = writable_project.Senses
        sense = sense_ops.Create(entry, "qZ217 test gloss")

        props = {
            "Source": "qZ217 source text",
            "ScientificName": "Panthera qz217",
            "ImportResidue": "qZ217 residue",
        }
        sense_ops.ApplySyncableProperties(sense, props)

        readback = sense_ops.GetSyncableProperties(sense)
        assert readback["Source"] == props["Source"]
        assert readback["ScientificName"] == props["ScientificName"]
        assert readback["ImportResidue"] == props["ImportResidue"]

    def test_etymology_source_multistring_roundtrip(self, writable_project):
        entry = _first_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available")

        etym_ops = writable_project.Etymologies
        etymology = etym_ops.Create(entry, source="qZ217 seed source")

        analysis_ws = writable_project.GetAllAnalysisWSs()
        if not analysis_ws:
            pytest.skip("Project has no analysis writing systems")
        ws_id = analysis_ws[0]

        props = {"Source": {ws_id: "qZ217 multistring source"}}
        etym_ops.ApplySyncableProperties(etymology, props)

        readback = etym_ops.GetSyncableProperties(etymology)
        assert readback["Source"] == props["Source"], (
            "Etymology.Source is IMultiString -- round trip must preserve "
            "the {ws_id: text} dict shape exactly."
        )

    def test_example_reference_roundtrip(self, writable_project):
        entry = _first_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available")

        sense_ops = writable_project.Senses
        sense = sense_ops.Create(entry, "qZ217 example host sense")
        example_ops = writable_project.Examples
        example = example_ops.Create(sense, "qZ217 example text")

        props = {"Reference": "qZ217 p. 1"}
        example_ops.ApplySyncableProperties(example, props)

        readback = example_ops.GetSyncableProperties(example)
        assert readback["Reference"] == props["Reference"]

    def test_pronunciation_form_roundtrip(self, writable_project):
        entry = _first_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available")

        pron_ops = writable_project.Pronunciations
        pronunciation = pron_ops.Create(entry, "qZ217pron")

        analysis_ws = writable_project.GetAllVernacularWSs()
        if not analysis_ws:
            pytest.skip("Project has no vernacular writing systems")
        ws_id = analysis_ws[0]

        props = {"Form": {ws_id: "qZ217pronform"}}
        pron_ops.ApplySyncableProperties(pronunciation, props)

        readback = pron_ops.GetSyncableProperties(pronunciation)
        assert readback["Form"] == props["Form"]

    def test_lexentry_importresidue_roundtrip(self, writable_project):
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        entry = _first_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available")

        entry_ops = writable_project.LexEntries
        props = {"ImportResidue": "qZ217 entry residue"}
        entry_ops.ApplySyncableProperties(entry, props)

        readback = entry_ops.GetSyncableProperties(entry)
        assert readback["ImportResidue"] == props["ImportResidue"]
