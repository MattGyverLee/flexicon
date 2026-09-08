#
#   test_issue252_pos_feature_sync.py
#
#   Class: TestPOSSyncStatic / TestPOSSyncCapture / TestPOSSyncApply*
#          Coverage for POSOperations.GetSyncableProperties /
#          ApplySyncableProperties -- spec feature-structure-sync-gap,
#          task T7, closes issue #252.
#
#   Context: PartOfSpeech has TWO feature-struct-owning properties in the
#   frozen C1 table (Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE
#   "PartOfSpeech" row): DefaultFeaturesOA (slot="Default") and
#   InherFeatValOA (slot="InherFeatVal"). Neither was ever captured or
#   applied before T7, so a synced POS carried correct Name/Abbreviation/
#   Description/CatalogSourceId but a permanently null feature structure.
#
#   Unlike #251 (MSAOperations), #252's __ResolveObject ALSO had an
#   independent C2 hole on the HVO entry path that silently dropped the
#   four PRE-EXISTING scalar/multistring properties too -- see
#   specs/feature-structure-sync-gap/evidence/live-T7.md prediction P1.
#   Patterns below are copied from test_issue251_msa_feature_sync.py AS
#   AMENDED by T6b (falsy-but-present presence-gate tests, direct live
#   cast test, real on_unresolved propagation assertion, hasattr
#   allowlisting) -- never from T6's original pre-T6b shapes.
#
#   Sections A-C are entirely OFFLINE (no live FLEx project). Section D
#   (bottom of file, `requires_live_project`) is the LIVE coverage against
#   a `target_sandbox` (tempdir copy of Target). See
#   specs/feature-structure-sync-gap/evidence/live-T7.md for the
#   run_mode/pass-fail record.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import inspect
import textwrap

import pytest


@pytest.fixture(autouse=True)
def _require_lcmodel():
    """
    POSOperations has module-level `from SIL.LCModel import ...`
    statements. On a machine without FieldWorks installed, that import
    ERRORs rather than skipping cleanly -- so skip explicitly instead.
    Nothing in Sections A-C opens a live project.
    """
    pytest.importorskip("SIL.LCModel")


def _method_source(method_name):
    from flexicon.code.Grammar.POSOperations import POSOperations

    obj = POSOperations.__dict__[method_name]

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


def _private_method_source(mangled_name):
    """Like _method_source, but for a name-mangled private (__x) method,
    looked up by its already-mangled dict key (e.g.
    '_POSOperations__ApplyFeatureStrucProp')."""
    from flexicon.code.Grammar.POSOperations import POSOperations

    obj = POSOperations.__dict__[mangled_name]
    return inspect.getsource(obj)


def _hasattr_second_args(src):
    """
    Walk the full AST of a function's source and return the second-
    argument string literal(s) of every `hasattr(...)` call found
    anywhere in the body (see test_issue251_msa_feature_sync.py's
    identical helper for the full rationale).

    Amended for POSOperations (unlike MSAOperations, whose hasattr calls
    are all literal): GetSyncableProperties' multistring loop is
    `for prop_name in ["Name", "Abbreviation", "Description"]: if
    hasattr(pos, prop_name):` -- the second arg is a loop variable, not a
    literal. When the second arg is an `ast.Name`, resolve it by finding
    the nearest enclosing `for` loop that binds that name to a literal
    list/tuple of strings, and expand to ALL of that list's values. Any
    other non-literal shape still fails loudly, same as before.
    """
    dedented = textwrap.dedent(src)
    tree = ast.parse(dedented)

    # Map every ast.Name-bound for-loop target to the literal string
    # values it iterates over, so a `hasattr(x, loop_var)` inside that
    # loop's body can be resolved to the concrete literal set.
    for_loop_values = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.For)
            and isinstance(node.target, ast.Name)
            and isinstance(node.iter, (ast.List, ast.Tuple))
            and all(
                isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                for elt in node.iter.elts
            )
        ):
            for_loop_values.setdefault(node.target.id, set()).update(
                elt.value for elt in node.iter.elts
            )

    names = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hasattr"
        ):
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                names.append(arg.value)
                continue
            if isinstance(arg, ast.Name) and arg.id in for_loop_values:
                names.extend(sorted(for_loop_values[arg.id]))
                continue
            raise AssertionError(
                f"hasattr() call with an unresolvable second argument: "
                f"{ast.dump(node)}"
            )
    return names


def _body_only(src):
    """
    Strip the docstring (and decorator) out of a method's source so
    source-pattern assertions test CODE, not prose -- this file's
    docstrings deliberately use words like 'hasattr' descriptively, which
    would otherwise produce false matches.
    """
    dedented = textwrap.dedent(src)
    tree = ast.parse(dedented)
    func = tree.body[0]
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(
        getattr(body[0], "value", None), ast.Constant
    ):
        body = body[1:]
    if not body:
        return ""
    lines = dedented.splitlines()
    start = body[0].lineno
    end = body[-1].end_lineno
    return "\n".join(lines[start - 1:end])


# ============================================================================
# Section A: static source-pattern locks (no fake objects, no live project)
# ============================================================================


class TestPOSSyncStatic:
    """Locks the shape of the #252 fix without exercising any LCM object."""

    # Lead ruling 3: GetSyncableProperties keeps its PRE-EXISTING hasattr
    # gates on Name/Abbreviation/Description/CatalogSourceId -- once
    # __ResolveObject casts (T7), they are redundant but safe (same shape
    # as the ChangeAffixVariant leg-7 resolution). This is an explicit
    # ALLOWLIST, not a zero-hasattr rule: the BaseOperations boundary is
    # that a hasattr probe on a FEATURE-STRUC property (DefaultFeaturesOA/
    # InherFeatValOA) would still be forbidden -- discrimination for those
    # two lives entirely in __CaptureFeatureStrucProp/__ApplyFeatureStrucProp
    # via _ResolveFeatureStrucOwner, never via hasattr.
    _ALLOWED_HASATTR_ATTRS_IN_GETSYNCABLE = frozenset(
        {"Name", "Abbreviation", "Description", "CatalogSourceId"}
    )

    def test_get_syncable_properties_hasattr_calls_are_allowlisted(self):
        src = _body_only(_method_source("GetSyncableProperties"))
        names = _hasattr_second_args(src)
        assert names, (
            "expected the four pre-existing hasattr gates in "
            "GetSyncableProperties (lead ruling 3 keeps them)."
        )
        for attr in names:
            assert attr in self._ALLOWED_HASATTR_ATTRS_IN_GETSYNCABLE, (
                f"GetSyncableProperties calls hasattr(x, {attr!r}) -- only "
                f"{sorted(self._ALLOWED_HASATTR_ATTRS_IN_GETSYNCABLE)} are "
                f"permitted. A feature-struct property "
                f"(DefaultFeaturesOA/InherFeatValOA) must be discriminated "
                f"via _ResolveFeatureStrucOwner, never hasattr (D5)."
            )

    def test_zero_hasattr_in_apply_and_feature_helpers(self):
        """
        The functions where #252's discrimination actually lives must
        contain ZERO hasattr calls: ApplySyncableProperties (the base-loop
        pop + two feature-struct dispatches), the two new private
        feature-struct helpers, and __ResolveObject itself (the C2 cast
        site -- discriminates on .ClassName via getattr, never hasattr).
        """
        src = _body_only(_method_source("ApplySyncableProperties"))
        assert "hasattr" not in src, (
            "POSOperations.ApplySyncableProperties must not gate on "
            "hasattr for a feature-struct property (D5)."
        )
        for mangled in (
            "_POSOperations__CaptureFeatureStrucProp",
            "_POSOperations__ApplyFeatureStrucProp",
            "_POSOperations__ResolveObject",
        ):
            src = _body_only(_private_method_source(mangled))
            assert "hasattr" not in src, (
                f"POSOperations.{mangled} must not contain a hasattr call "
                f"(D5 / C2 -- discrimination is via .ClassName + explicit "
                f"cast, not hasattr)."
            )

    def test_resolve_object_casts_on_classname_and_never_raises(self):
        """
        C2: self.project.Object(hvo) returns a bare ICmObject.
        __ResolveObject must cast to IPartOfSpeech when ClassName ==
        "PartOfSpeech", and must never raise on any other input (mirrors
        the MSAOperations.__GetMsaObject shape -- lead ruling 1).
        """
        src = _body_only(_private_method_source("_POSOperations__ResolveObject"))
        assert "self.project.Object(pos_or_hvo)" in src
        assert 'getattr(obj, "ClassName", None) == "PartOfSpeech"' in src
        assert "IPartOfSpeech(obj)" in src
        assert "raise" not in src, (
            "__ResolveObject must never raise -- a ClassName miss (or a "
            "GUID str, out of scope per T12) is returned UNCHANGED."
        )

    def test_pop_before_super_source_shape(self):
        """
        C6: the four feature-struct keys must be filtered OUT of the dict
        passed to super().ApplySyncableProperties -- confirmed
        behaviourally in TestPOSSyncApplyPopBeforeSuper below; this pins
        the source shape too.
        """
        src = _body_only(_method_source("ApplySyncableProperties"))
        filter_idx = src.index("__FEATURE_STRUC_KEYS")
        super_idx = src.index("super().ApplySyncableProperties")
        assert filter_idx < super_idx, (
            "The feature-struct key filter must be built BEFORE "
            "super().ApplySyncableProperties is called (C6)."
        )

    def test_apply_gates_on_key_presence_not_truthiness(self):
        """C6: 'if key in props or guid_key in props', never 'if value:'."""
        src = _body_only(
            _private_method_source("_POSOperations__ApplyFeatureStrucProp")
        )
        assert "in props" in src, (
            "__ApplyFeatureStrucProp must gate on key PRESENCE ('in "
            "props'), never on the value's truthiness (C6)."
        )
        assert "props.get(key) or {}" in src, (
            "A present-but-empty spec must default to {} (an empty but "
            "attached struct), not be treated as absent."
        )

    def test_both_slots_passed_explicitly_in_capture_and_apply(self):
        """
        Unlike MoStemMsa's single-row None, PartOfSpeech has TWO rows --
        every call site must pass slot="Default" or slot="InherFeatVal"
        explicitly (never None).
        """
        capture_src = _body_only(_method_source("GetSyncableProperties"))
        assert '"Default"' in capture_src and '"InherFeatVal"' in capture_src

        apply_src = _body_only(_method_source("ApplySyncableProperties"))
        assert '"Default"' in apply_src and '"InherFeatVal"' in apply_src


class TestPOSSyncResolveObjectGuidStringOutOfScope:
    """
    Lead ruling 2 (T12 rider): GUID-string support is explicitly OUT of
    scope for __ResolveObject -- a str falls through unresolved and is
    returned unchanged. This pins CURRENT behaviour so a future T12 fix
    is a deliberate, reviewed change, not an accidental regression this
    file would otherwise miss.
    """

    def test_guid_string_falls_through_unchanged(self):
        from flexicon.code.Grammar.POSOperations import POSOperations

        class _FakeProject:
            writeEnabled = True

        pos_ops = POSOperations(_FakeProject())
        guid_str = "11111111-1111-1111-1111-111111111111"
        result = pos_ops._POSOperations__ResolveObject(guid_str)
        assert result == guid_str


# ============================================================================
# Sections B/C: fake-object dispatch coverage (no live project, no real cast)
# ============================================================================


class _FakeGuid:
    def __init__(self, s):
        self._s = s

    def __str__(self):
        return self._s


class _FakeFeatStruct:
    """Stand-in for IFsFeatStruc -- only needs a .Guid for capture."""

    def __init__(self, guid="11111111-1111-1111-1111-111111111111"):
        self.Guid = _FakeGuid(guid)


class _FakePos:
    """Stand-in for an LCM PartOfSpeech object: only the feature-struct-
    owning attributes the test wants populated. hasattr(pos, "Name") etc.
    correctly returns False for these -- GetSyncableProperties' four
    pre-existing scalar/multistring keys are out of scope for these tests."""

    def __init__(self, **attrs):
        for k, v in attrs.items():
            setattr(self, k, v)


class _FakeWritingSystems:
    def GetAll(self):
        return []


class _FakeProject:
    """Minimal stand-in -- every test in this file monkeypatches away the
    three feature-struct seams and __ResolveObject, so POSOperations never
    actually touches self.project beyond WritingSystems.GetAll()."""

    writeEnabled = True
    WritingSystems = _FakeWritingSystems()


_POS_PROP_BY_SLOT = {
    "Default": "DefaultFeaturesOA",
    "InherFeatVal": "InherFeatValOA",
}


def _make_fake_resolver(calls):
    def _fake(self, owner, slot=None):
        calls.append((owner, slot))
        prop_name = _POS_PROP_BY_SLOT[slot]
        return owner, prop_name

    return _fake


def _fake_get_feature_struc(self, struct):
    if struct is None:
        return None
    return {
        "TypeGuid": None,
        "specs": {"FAKE-FEAT-GUID": "FAKE-VAL-GUID"},
        "_source_guid": str(struct.Guid),
    }


def _make_super_spy(records):
    def _spy(self, item, props, ws_map=None, fill_gaps=False):
        records.append(
            {
                "item": item,
                "props": dict(props),
                "ws_map": ws_map,
                "fill_gaps": fill_gaps,
            }
        )

    return _spy


def _make_apply_spy(records, raise_guid=None):
    def _spy(self, owner, prop_name, spec_dict, struct_guid=None,
              on_unresolved="raise", label=None):
        from flexicon.code.BaseOperations import FP_ParameterError

        records.append(
            {
                "owner": owner,
                "prop_name": prop_name,
                "spec_dict": spec_dict,
                "struct_guid": struct_guid,
                "on_unresolved": on_unresolved,
                "label": label,
            }
        )
        if raise_guid is not None:
            raise FP_ParameterError(
                f"ApplySyncableProperties: reference to GUID {raise_guid} "
                f"which does not exist in the target project."
            )
        return object()

    return _spy


@pytest.fixture
def pos_ops(monkeypatch):
    """POSOperations instance with __ResolveObject stubbed to identity, so
    tests can hand it a plain _FakePos directly without needing a real
    SIL.LCModel cast."""
    from flexicon.code.Grammar.POSOperations import POSOperations

    monkeypatch.setattr(
        POSOperations, "_POSOperations__ResolveObject", lambda self, x: x
    )
    return POSOperations(_FakeProject())


class TestPOSSyncCapture:
    """GetSyncableProperties feature-struct dispatch (C1 "PartOfSpeech" row)."""

    def test_capture_both_slots_populated(self, monkeypatch, pos_ops):
        from flexicon.code.Grammar.POSOperations import POSOperations

        calls = []
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver(calls)
        )
        monkeypatch.setattr(
            POSOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        default_guid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        inher_guid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        pos = _FakePos(
            DefaultFeaturesOA=_FakeFeatStruct(default_guid),
            InherFeatValOA=_FakeFeatStruct(inher_guid),
        )

        props = pos_ops.GetSyncableProperties(pos)

        assert calls == [(pos, "Default"), (pos, "InherFeatVal")]
        assert props["DefaultFeaturesGuid"] == default_guid
        assert props["InherFeatValGuid"] == inher_guid
        assert set(props.keys()) == {
            "DefaultFeatures", "DefaultFeaturesGuid",
            "InherFeatVal", "InherFeatValGuid",
        }

    def test_capture_only_one_slot_populated(self, monkeypatch, pos_ops):
        """Presence gate on the CAPTURE side: an unpopulated slot emits
        neither of its keys, even though the resolver is still consulted
        for it (both slots are always dispatched)."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        calls = []
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver(calls)
        )
        monkeypatch.setattr(
            POSOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        inher_guid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        pos = _FakePos(
            DefaultFeaturesOA=None, InherFeatValOA=_FakeFeatStruct(inher_guid)
        )

        props = pos_ops.GetSyncableProperties(pos)

        assert calls == [(pos, "Default"), (pos, "InherFeatVal")]
        assert set(props.keys()) == {"InherFeatVal", "InherFeatValGuid"}

    def test_capture_null_structs_emit_no_feature_keys(self, monkeypatch, pos_ops):
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        monkeypatch.setattr(
            POSOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        pos = _FakePos(DefaultFeaturesOA=None, InherFeatValOA=None)
        props = pos_ops.GetSyncableProperties(pos)
        assert props == {}


class TestPOSSyncApplyGuards:
    """Top-of-method guards, fire before touching pos/resolver at all."""

    def test_none_item_raises_fp_parameter_error(self, pos_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="item is None"):
            pos_ops.ApplySyncableProperties(None, {})

    def test_non_dict_props_raises_fp_parameter_error(self, pos_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        pos = _FakePos()
        with pytest.raises(FP_ParameterError, match="props must be a dict"):
            pos_ops.ApplySyncableProperties(pos, ["not", "a", "dict"])


class TestPOSSyncApplyPopBeforeSuper:
    """C6, explicit behavioural test: the four feature-struct keys must
    never reach BaseOperations.ApplySyncableProperties / _apply_props_loop,
    which would route a C4 dict into the multistring branch and drop it."""

    def test_apply_pops_all_four_feature_keys_before_super(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.POSOperations import POSOperations

        super_calls = []
        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy(super_calls)
        )
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            POSOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        pos = _FakePos()
        props = {
            "DefaultFeatures": {"TypeGuid": None, "specs": {}},
            "DefaultFeaturesGuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "SomeOtherPlainProp": "value",
        }

        pos_ops.ApplySyncableProperties(pos, props)

        assert len(super_calls) == 1
        received = super_calls[0]["props"]
        for key in (
            "DefaultFeatures", "DefaultFeaturesGuid",
            "InherFeatVal", "InherFeatValGuid",
        ):
            assert key not in received, (
                f"{key!r} must be popped out of props before "
                f"super().ApplySyncableProperties is called (C6)."
            )
        assert received == {"SomeOtherPlainProp": "value"}
        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] == {"TypeGuid": None, "specs": {}}


class TestPOSSyncApplyPresenceGate:
    """
    C6: gate on key PRESENCE, never truthiness. T6b lesson applied FROM
    THE START (never introduced as a truthy-only fixture then amended):
    every fixture below carries a FALSY-BUT-PRESENT value so presence and
    truthiness come apart immediately.
    """

    def test_falsy_but_present_feature_struct_key_still_triggers_apply(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            POSOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        pos = _FakePos()
        # Both the struct key AND its guid sibling are PRESENT but FALSY.
        props = {"DefaultFeatures": {}, "DefaultFeaturesGuid": ""}

        pos_ops.ApplySyncableProperties(pos, props)

        assert len(apply_calls) == 1, (
            "A present-but-falsy DefaultFeatures/DefaultFeaturesGuid pair "
            "must still trigger _ApplyFeatureStruc (C6 presence gate, not "
            "truthiness)."
        )
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == ""

    def test_falsy_but_present_guid_only_key_still_triggers_apply(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            POSOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        pos = _FakePos()
        props = {"InherFeatValGuid": ""}

        pos_ops.ApplySyncableProperties(pos, props)

        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == ""

    def test_guid_only_present_still_triggers_apply_with_empty_spec(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            POSOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        pos = _FakePos()
        guid = "12121212-1212-1212-1212-121212121212"
        # "DefaultFeatures" key intentionally ABSENT -- a present-but-empty
        # source struct emits only its Guid sibling (C4/C6).
        props = {"DefaultFeaturesGuid": guid}

        pos_ops.ApplySyncableProperties(pos, props)

        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == guid

    def test_neither_key_present_never_calls_apply_feature_struc(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            POSOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        pos = _FakePos()
        pos_ops.ApplySyncableProperties(pos, {})

        assert apply_calls == []


class TestPOSSyncApplyBothSlots:
    def test_apply_dispatches_both_slots_with_correct_prop_names(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        resolver_calls = []
        monkeypatch.setattr(
            POSOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(resolver_calls),
        )
        apply_calls = []
        monkeypatch.setattr(
            POSOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        pos = _FakePos()
        props = {
            "DefaultFeatures": {"TypeGuid": None, "specs": {}},
            "DefaultFeaturesGuid": "default-guid",
            "InherFeatVal": {"TypeGuid": None, "specs": {}},
            "InherFeatValGuid": "inher-guid",
        }

        pos_ops.ApplySyncableProperties(pos, props)

        assert resolver_calls == [(pos, "Default"), (pos, "InherFeatVal")]
        assert [c["prop_name"] for c in apply_calls] == [
            "DefaultFeaturesOA", "InherFeatValOA",
        ]
        assert apply_calls[0]["struct_guid"] == "default-guid"
        assert apply_calls[1]["struct_guid"] == "inher-guid"


class TestPOSSyncApplyRaisePropagationThroughPublicSurface:
    """
    C7 raise-PROPAGATION coverage only -- NOT enforcement coverage (T6b
    item 2's lesson applied from the start). The test double raises
    unconditionally and never reads on_unresolved; the assertion that
    actually locks C7 is that the recorded call carried
    on_unresolved == "raise", which DOES die under a raise->skip mutation.
    Real enforcement is locked by the live test
    test_apply_raises_on_unresolved_feature_guid (Section D).
    """

    def test_apply_propagates_fp_parameter_error_and_passes_raise_policy(
        self, monkeypatch, pos_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations, FP_ParameterError
        from flexicon.code.Grammar.POSOperations import POSOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            POSOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        bogus_guid = "00000000-0000-0000-0000-0000000000ff"
        records = []
        monkeypatch.setattr(
            POSOperations,
            "_ApplyFeatureStruc",
            _make_apply_spy(records, raise_guid=bogus_guid),
        )

        pos = _FakePos()
        props = {
            "DefaultFeatures": {"TypeGuid": None, "specs": {"f": bogus_guid}},
            "DefaultFeaturesGuid": "11111111-1111-1111-1111-111111111111",
        }

        with pytest.raises(FP_ParameterError, match=bogus_guid):
            pos_ops.ApplySyncableProperties(pos, props)

        assert len(records) == 1
        assert records[0]["on_unresolved"] == "raise", (
            "POSOperations.__ApplyFeatureStrucProp must call "
            "_ApplyFeatureStruc with on_unresolved='raise' "
            "unconditionally (C7) -- this is the assertion that would "
            "fail if that were mutated to 'skip'."
        )


class TestPOSSyncCompareToStructGuidPinning:
    """
    Pre-ruling 4: CompareTo is NOT modified by T7, but its behaviour
    CHANGES as a side effect of GetSyncableProperties now emitting the
    two feature-struct key-pairs -- two POS with identical feature specs
    but DIFFERENT struct GUIDs now report a difference on the
    "<key>Guid" key (previously CompareTo never saw these keys at all).
    This is a documented behaviour change, not a defect; a candidate
    follow-up (comparing by spec content instead of struct identity) is
    noted in the cycle-13 programmer report, not filed as an issue.
    """

    def test_identical_specs_different_struct_guids_reported_as_different(
        self, monkeypatch
    ):
        from flexicon.code.Grammar.POSOperations import POSOperations

        pos_ops = POSOperations(_FakeProject())
        item1 = object()
        item2 = object()
        props_by_item = {
            id(item1): {
                "DefaultFeatures": {"TypeGuid": None, "specs": {"F": "V"}},
                "DefaultFeaturesGuid": "guid-A",
            },
            id(item2): {
                "DefaultFeatures": {"TypeGuid": None, "specs": {"F": "V"}},
                "DefaultFeaturesGuid": "guid-B",
            },
        }

        def _fake_get(self, item):
            return props_by_item[id(item)]

        monkeypatch.setattr(POSOperations, "GetSyncableProperties", _fake_get)

        is_different, differences = pos_ops.CompareTo(item1, item2)

        assert is_different is True
        assert differences == {
            "DefaultFeaturesGuid": ("guid-A", "guid-B"),
        }
        assert "DefaultFeatures" not in differences, (
            "The specs themselves are identical -- only the struct-GUID "
            "sibling key should differ."
        )


# ============================================================================
# Section D: LIVE coverage (target_sandbox -- tempdir copy of Target)
# ============================================================================


@pytest.fixture
def live_pos_factory(target_sandbox):
    """Yields (sandbox,) -- POS creation/cleanup is per-test since each
    test needs its own uniquely-named TEST_ POS."""
    yield target_sandbox


def _make_feature_and_value(infl_ops, feat_name, feat_abbr, val_name, val_abbr):
    feat = infl_ops.Create(feat_name, feat_abbr, type="closed")
    value = infl_ops.CreateValue(feat, val_name, val_abbr)
    return feat, value


@pytest.mark.requires_live_project
class TestPOSSyncLiveResolveObjectCast:
    """
    A DIRECT, mutation-resistant live test of __ResolveObject's C2 cast
    (the item T6b item 1 gated Checkpoint 3b on, replicated here for
    POS). Calls the private resolver DIRECTLY by its mangled name
    (bypassing GetSyncableProperties/_ResolveFeatureStrucOwner entirely)
    and reads a SUBTYPE-ONLY member straight off the returned object --
    DefaultFeaturesOA is declared on IPartOfSpeech and is NOT reachable
    on the bare ICmObject that sandbox.Object(hvo) returns. Without the
    cast, `.DefaultFeaturesOA` raises AttributeError.
    """

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_hvo_path_casts_to_concrete_pos(self, target_sandbox):
        sandbox = target_sandbox
        pos_obj = sandbox.POS.Create("TEST_252_cast_pos", "t252c")
        try:
            hvo = pos_obj.Hvo

            # BINDING: the PRE-cast bare object must LACK the subtype-only
            # member -- otherwise the assertions below only prove the
            # cast is harmless, never that it does anything.
            assert not hasattr(sandbox.Object(hvo), "DefaultFeaturesOA")

            result = sandbox.POS._POSOperations__ResolveObject(hvo)
            assert result.ClassName == "PartOfSpeech"
            # Direct read of a subtype-only member -- AttributeError here
            # (not merely a wrong value) is the cast-removed failure mode.
            assert result.DefaultFeaturesOA is None
            assert result.InherFeatValOA is None
        finally:
            sandbox.POS.Delete(pos_obj)


@pytest.mark.requires_live_project
class TestPOSSyncLiveRoundTrip:
    """
    Real capture -> apply -> RE-READ round trips against a live
    target_sandbox. All read-back assertions re-fetch from a FRESH
    sandbox.Object(hvo) after the write, never from the reference held
    at write time. Per P3, the sandbox carries no pre-existing populated
    POS, so every test CREATES its struct via _ApplyFeatureStruc first.
    """

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_default_features_slot_capture_apply_roundtrip(self, target_sandbox):
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        feat, value = _make_feature_and_value(
            infl_ops, "TEST_252_default_feat", "t2df",
            "TEST_252_default_val", "t2dv",
        )

        src_pos = sandbox.POS.Create("TEST_252_default_src", "t2ds")
        tgt_pos = sandbox.POS.Create("TEST_252_default_tgt", "t2dt")
        try:
            sandbox.POS._ApplyFeatureStruc(
                src_pos, "DefaultFeaturesOA",
                [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
                on_unresolved="raise", label="TEST src POS Default",
            )

            src_bare = sandbox.Object(src_pos.Hvo)
            props = sandbox.POS.GetSyncableProperties(src_bare)
            expected_specs = {str(feat.Guid): str(value.Guid)}
            assert props["DefaultFeatures"]["specs"] == expected_specs
            assert props["DefaultFeaturesGuid"]

            sandbox.POS.ApplySyncableProperties(tgt_pos, props)

            tgt_bare = sandbox.Object(tgt_pos.Hvo)
            reread_props = sandbox.POS.GetSyncableProperties(tgt_bare)
            assert reread_props["DefaultFeatures"]["specs"] == expected_specs
        finally:
            sandbox.POS.Delete(src_pos)
            sandbox.POS.Delete(tgt_pos)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_inher_feat_val_slot_capture_apply_roundtrip(self, target_sandbox):
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        feat, value = _make_feature_and_value(
            infl_ops, "TEST_252_inher_feat", "t2if",
            "TEST_252_inher_val", "t2iv",
        )

        src_pos = sandbox.POS.Create("TEST_252_inher_src", "t2is")
        tgt_pos = sandbox.POS.Create("TEST_252_inher_tgt", "t2it")
        try:
            sandbox.POS._ApplyFeatureStruc(
                src_pos, "InherFeatValOA",
                [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
                on_unresolved="raise", label="TEST src POS InherFeatVal",
            )

            src_bare = sandbox.Object(src_pos.Hvo)
            props = sandbox.POS.GetSyncableProperties(src_bare)
            expected_specs = {str(feat.Guid): str(value.Guid)}
            assert props["InherFeatVal"]["specs"] == expected_specs

            sandbox.POS.ApplySyncableProperties(tgt_pos, props)

            tgt_bare = sandbox.Object(tgt_pos.Hvo)
            reread_props = sandbox.POS.GetSyncableProperties(tgt_bare)
            assert reread_props["InherFeatVal"]["specs"] == expected_specs
        finally:
            sandbox.POS.Delete(src_pos)
            sandbox.POS.Delete(tgt_pos)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_hvo_entry_path_captures_name(self, target_sandbox):
        """
        P1 pin: GetSyncableProperties(hvo) must capture Name (and the
        other three pre-existing scalar/multistring properties) on the
        HVO entry path -- this is the silent-drop bug __ResolveObject's
        new cast fixes, independent of the two new feature-struct keys.
        """
        sandbox = target_sandbox
        pos_obj = sandbox.POS.Create("TEST_252_hvo_name", "t2hn")
        try:
            hvo = pos_obj.Hvo
            props = sandbox.POS.GetSyncableProperties(hvo)
            assert "Name" in props
            assert props["Name"] == sandbox.POS.GetSyncableProperties(pos_obj)["Name"]
        finally:
            sandbox.POS.Delete(pos_obj)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_apply_raises_on_unresolved_feature_guid(self, target_sandbox):
        from flexicon.code.BaseOperations import FP_ParameterError

        sandbox = target_sandbox
        tgt_pos = sandbox.POS.Create("TEST_252_unresolved_tgt", "t2ur")
        try:
            bogus_feat_guid = "00000000-0000-0000-0000-0000000000aa"
            bogus_val_guid = "00000000-0000-0000-0000-0000000000bb"
            props = {
                "DefaultFeatures": {
                    "TypeGuid": None,
                    "specs": {bogus_feat_guid: bogus_val_guid},
                },
                "DefaultFeaturesGuid": "00000000-0000-0000-0000-0000000000cc",
            }

            with pytest.raises(FP_ParameterError, match=bogus_feat_guid):
                sandbox.POS.ApplySyncableProperties(tgt_pos, props)
        finally:
            sandbox.POS.Delete(tgt_pos)


@pytest.mark.requires_live_project
class TestPOSSyncLiveSlotAmbiguityNoSlot:
    """
    C1 ruling, modelled on T14a test 3
    (test_makefeatstruc_c3_live.py::TestMakeFeatStrucAmbiguousOwnerNoSlotLive):
    PartOfSpeech has TWO feature-structure-owning properties, so
    _ResolveFeatureStrucOwner(pos, slot=None) must RAISE FP_ParameterError
    naming both "PartOfSpeech" and "slot" -- never silently guess. Unlike
    MoDerivAffMsa (reachable ambiguously via the public MakeFeatStruc
    surface), POSOperations' own dispatch always passes an explicit slot,
    so this ambiguity is only reachable by calling the inherited
    BaseOperations resolver directly -- exercised here against a REAL
    live POS.
    """

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_ambiguous_owner_without_slot_raises(self, target_sandbox):
        from flexicon.code.BaseOperations import FP_ParameterError

        sandbox = target_sandbox
        pos_obj = sandbox.POS.Create("TEST_252_ambig_pos", "t2ap")
        try:
            hvo = pos_obj.Hvo

            with pytest.raises(FP_ParameterError) as excinfo:
                sandbox.POS._ResolveFeatureStrucOwner(pos_obj)
            assert "PartOfSpeech" in str(excinfo.value)
            assert "slot" in str(excinfo.value)

            # Confirm the raise happened BEFORE anything was attached --
            # a partial/guessed attach would be worse than the raise itself.
            from SIL.LCModel import IPartOfSpeech

            fresh_pos = IPartOfSpeech(sandbox.Object(hvo))
            assert fresh_pos.DefaultFeaturesOA is None
            assert fresh_pos.InherFeatValOA is None
        finally:
            sandbox.POS.Delete(pos_obj)
