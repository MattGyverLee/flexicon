#
#   test_t8_allomorph_feature_sync.py
#
#   Class: TestAllomorphSyncStatic / TestAllomorphSyncCapture /
#          TestAllomorphSyncApply* / TestT8Live*
#          Coverage for AllomorphOperations.GetSyncableProperties /
#          ApplySyncableProperties -- spec feature-structure-sync-gap,
#          task T8 (spec.md:655). T8 is an UNFILED P0: there is NO GitHub
#          issue and filing one is an outstanding USER decision. This
#          file (and the CHANGELOG entry accompanying it) reference "T8,
#          spec.md:655" only -- never an issue number.
#
#   Context: AllomorphOperations previously had ZERO capture/apply of
#   MsEnvFeaturesOA (the frozen C1 "MoAffixAllomorph" row in
#   FEATURE_STRUC_OWNER_TABLE, Shared/lcm_constants.py -- ONE row,
#   slot=None; MoStemAllomorph has NO row and carries no MsEnvFeaturesOA
#   property at all). It ALSO had two independent, pre-existing defects
#   on the shared HVO-resolution path (same shape as #251/#252):
#     (i) GetSyncableProperties used `item` raw instead of routing
#         through __GetAllomorphObject -- an HVO int made every hasattr
#         gate False and silently returned {"Form": {}, "MorphTypeRA":
#         None} with no raise.
#     (ii) __GetAllomorphObject (11 call sites) returned a bare, uncast
#          ICmObject on the HVO path.
#   Both are fixed alongside the new feature-struct sync since
#   __GetAllomorphObject is the single choke point all three routes
#   through.
#
#   Sections A-C are entirely OFFLINE (no live FLEx project). Section D
#   (bottom of file, `requires_live_project`) is the LIVE coverage
#   against a `target_sandbox` (tempdir copy of Target). See
#   specs/feature-structure-sync-gap/evidence/live-T8.md for the
#   run_mode/pass-fail record and
#   specs/feature-structure-sync-gap/evidence/live-T8-predictions.md for
#   the five pre-committed predictions this file (and that evidence
#   file) adjudicate.
#
#   Patterns copied from test_issue251_msa_feature_sync.py /
#   test_issue252_pos_feature_sync.py AS AMENDED BY T6b (direct
#   mutation-resistant cast test, real on_unresolved propagation
#   assertion, falsy-but-present presence-gate value from the start,
#   hasattr allowlisting) -- never T6's pre-T6b shapes.
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
    AllomorphOperations has module-level `from SIL.LCModel import ...`
    statements. On a machine without FieldWorks installed, that import
    ERRORs rather than skipping cleanly -- so skip explicitly instead.
    Nothing in Sections A-C opens a live project.
    """
    pytest.importorskip("SIL.LCModel")


def _method_source(method_name):
    from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

    obj = AllomorphOperations.__dict__[method_name]

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
    '_AllomorphOperations__GetAllomorphObject')."""
    from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

    obj = AllomorphOperations.__dict__[mangled_name]
    return inspect.getsource(obj)


def _hasattr_second_args(src):
    """
    Walk the full AST of a function's source (docstring included -- a
    plain string literal in the docstring never produces an ast.Call
    node, so it cannot false-positive here) and return the second-
    argument string literal of every `hasattr(...)` call found anywhere
    in the body. All of AllomorphOperations' hasattr calls are literal
    (unlike POSOperations' loop-variable shape), so no loop-resolution
    is needed here.
    """
    dedented = textwrap.dedent(src)
    tree = ast.parse(dedented)
    names = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hasattr"
        ):
            arg = node.args[1]
            assert isinstance(arg, ast.Constant) and isinstance(arg.value, str), (
                f"hasattr() call with a non-literal second argument: "
                f"{ast.dump(node)}"
            )
            names.append(arg.value)
    return names


def _body_only(src):
    """
    Strip the docstring (and decorator) out of a method's source so
    source-pattern assertions test CODE, not prose -- this file's
    docstrings deliberately use words like 'hasattr' and 'slot='
    descriptively, which would otherwise produce false matches.
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


class TestAllomorphSyncStatic:
    """Locks the shape of the T8 fix without exercising any LCM object."""

    # Lead ruling R16-2: GetSyncableProperties keeps its PRE-EXISTING
    # hasattr gates on Form/IsAbstract/MorphTypeRA -- once
    # __GetAllomorphObject casts, they are redundant but safe. This is an
    # explicit ALLOWLIST, not a zero-hasattr rule: a hasattr probe on the
    # feature-struct property (MsEnvFeaturesOA) would still be forbidden
    # -- discrimination for it lives entirely in
    # __CaptureFeatureStrucProp/__ApplyFeatureStrucProp via
    # _ResolveFeatureStrucOwner, never via hasattr.
    _ALLOWED_HASATTR_ATTRS_IN_GETSYNCABLE = frozenset(
        {"Form", "IsAbstract", "MorphTypeRA"}
    )

    def test_get_syncable_properties_hasattr_calls_are_allowlisted(self):
        src = _body_only(_method_source("GetSyncableProperties"))
        names = _hasattr_second_args(src)
        assert names, (
            "expected the three pre-existing hasattr gates in "
            "GetSyncableProperties (lead ruling R16-2 keeps them)."
        )
        for attr in names:
            assert attr in self._ALLOWED_HASATTR_ATTRS_IN_GETSYNCABLE, (
                f"GetSyncableProperties calls hasattr(x, {attr!r}) -- only "
                f"{sorted(self._ALLOWED_HASATTR_ATTRS_IN_GETSYNCABLE)} are "
                f"permitted. The feature-struct property (MsEnvFeaturesOA) "
                f"must be discriminated via ClassName + "
                f"_ResolveFeatureStrucOwner, never hasattr (D5)."
            )

    def test_zero_hasattr_in_apply_and_feature_helpers_and_resolver(self):
        """
        The functions where T8's discrimination actually lives must
        contain ZERO hasattr calls: ApplySyncableProperties (the
        base-loop pop + the feature-struct dispatch), the two new
        private feature-struct helpers, and __GetAllomorphObject itself
        (the C2 cast site -- discriminates on .ClassName via getattr,
        never hasattr).
        """
        src = _body_only(_method_source("ApplySyncableProperties"))
        assert "hasattr" not in src, (
            "AllomorphOperations.ApplySyncableProperties must not gate "
            "on hasattr for a feature-struct property (D5)."
        )
        for mangled in (
            "_AllomorphOperations__CaptureFeatureStrucProp",
            "_AllomorphOperations__ApplyFeatureStrucProp",
            "_AllomorphOperations__GetAllomorphObject",
        ):
            src = _body_only(_private_method_source(mangled))
            assert "hasattr" not in src, (
                f"AllomorphOperations.{mangled} must not contain a "
                f"hasattr call (D5 / C2 -- discrimination is via "
                f".ClassName + explicit cast, not hasattr)."
            )

    def test_get_allomorph_object_casts_on_classname_and_never_raises(self):
        """
        C2 (T8 defect ii): self.project.Object(hvo) returns a bare
        ICmObject. __GetAllomorphObject must cast to IMoStemAllomorph /
        IMoAffixAllomorph by ClassName, and must never raise on any
        other input (mirrors MSAOperations.__GetMsaObject /
        POSOperations.__ResolveObject -- lead ruling R16-4(ii)). This
        differs from Duplicate, which DOES raise on an unrecognized
        ClassName -- that raise is local to Duplicate; this SHARED
        resolver must stay permissive since 11 other call sites depend
        on it.
        """
        src = _body_only(
            _private_method_source("_AllomorphOperations__GetAllomorphObject")
        )
        assert "self.project.Object(allomorph_or_hvo)" in src
        assert 'class_name == "MoStemAllomorph"' in src
        assert 'class_name == "MoAffixAllomorph"' in src
        assert "IMoStemAllomorph(obj)" in src
        assert "IMoAffixAllomorph(obj)" in src
        assert "raise" not in src, (
            "__GetAllomorphObject must never raise -- a ClassName miss "
            "is returned UNCHANGED."
        )

    def test_pop_before_super_source_shape(self):
        """
        C6: the feature-struct key pair must be filtered OUT of the dict
        passed to super().ApplySyncableProperties -- confirmed
        behaviourally in TestAllomorphSyncApplyPopBeforeSuper below;
        this pins the source shape too.
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
            _private_method_source("_AllomorphOperations__ApplyFeatureStrucProp")
        )
        assert "in props" in src, (
            "__ApplyFeatureStrucProp must gate on key PRESENCE ('in "
            "props'), never on the value's truthiness (C6)."
        )
        assert "props.get(key) or {}" in src, (
            "A present-but-empty spec must default to {} (an empty but "
            "attached struct), not be treated as absent."
        )

    def test_no_non_none_slot_literal_anywhere_in_feature_struct_calls(self):
        """
        P3 (T8 predictions): MoAffixAllomorph has exactly ONE row in the
        C1 table (slot=None) -- there is no slot ambiguity for the
        allomorph family, unlike MoDerivAffMsa/PartOfSpeech. No T8
        production line may pass a non-None slot= literal.
        """
        for name in ("GetSyncableProperties", "ApplySyncableProperties"):
            src = _body_only(_method_source(name))
            assert 'slot="' not in src and "slot='" not in src, (
                f"AllomorphOperations.{name} passes a non-None slot= "
                f"literal -- MoAffixAllomorph has only one C1 row "
                f"(P3)."
            )
        for mangled in (
            "_AllomorphOperations__CaptureFeatureStrucProp",
            "_AllomorphOperations__ApplyFeatureStrucProp",
        ):
            src = _body_only(_private_method_source(mangled))
            assert 'slot="' not in src and "slot='" not in src
            assert "slot=None" in src or "slot=slot" in src


class TestAllomorphSyncResolveObjectStringOutOfScope:
    """
    __GetAllomorphObject only special-cases `int` (HVO); a GUID string
    (or any other non-LCM input) falls through the `isinstance(...,
    int)` check, has no `.ClassName`, and is returned unchanged. Pins
    CURRENT behaviour so any future GUID-string support is a deliberate,
    reviewed change.
    """

    def test_string_input_falls_through_unchanged(self):
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        class _FakeProj:
            writeEnabled = True

        allo_ops = AllomorphOperations(_FakeProj())
        guid_str = "11111111-1111-1111-1111-111111111111"
        result = allo_ops._AllomorphOperations__GetAllomorphObject(guid_str)
        assert result == guid_str


class TestGetSyncablePropertiesRealResolverGuard:
    """
    P2 (T8 predictions), condition coverage using the REAL resolver
    (never a spy that raises unconditionally -- that was T6b defect 2,
    generalised here to condition coverage): confirms
    BaseOperations._ResolveFeatureStrucOwner itself raises
    FP_ParameterError naming "MoStemAllomorph" when asked to resolve a
    MoStemAllomorph owner. Combined with
    TestAllomorphSyncCapture::test_capture_stem_allomorph_* (which shows
    the unmutated dispatch never reaches this call), this pair is what
    mutation M-T8-2 (deleting the `if class_name ==
    "MoAffixAllomorph"` guard so the resolver runs unconditionally)
    would trip: the guard-removed GetSyncableProperties would call this
    REAL resolver on a MoStemAllomorph and it would raise for real, not
    because a stub says so.
    """

    def test_real_resolver_raises_naming_mostemallomorph(self):
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations
        from flexicon.code.BaseOperations import FP_ParameterError

        class _FakeProj:
            writeEnabled = True

        class _FakeAllomorphNoAttrs:
            ClassName = "MoStemAllomorph"

        allo_ops = AllomorphOperations(_FakeProj())

        with pytest.raises(FP_ParameterError, match="MoStemAllomorph"):
            allo_ops._ResolveFeatureStrucOwner(_FakeAllomorphNoAttrs(), slot=None)


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


class _FakeAllomorph:
    """Stand-in for an LCM allomorph object: just a ClassName plus
    whatever feature-struct-owning attributes the test wants populated.
    hasattr(allo, "Form") etc. correctly returns False for these --
    GetSyncableProperties' three pre-existing keys are out of scope for
    these tests (untouched by T8)."""

    def __init__(self, class_name, **attrs):
        self.ClassName = class_name
        for k, v in attrs.items():
            setattr(self, k, v)


class _FakeWritingSystems:
    def GetAll(self):
        return []


class _FakeProject:
    """Minimal stand-in -- every test in this file monkeypatches away the
    three feature-struct seams and __GetAllomorphObject, so
    AllomorphOperations never actually touches self.project beyond
    WritingSystems.GetAll()."""

    writeEnabled = True
    WritingSystems = _FakeWritingSystems()


def _make_fake_resolver(calls):
    def _fake(self, owner, slot=None):
        calls.append((owner, slot))
        return owner, "MsEnvFeaturesOA"

    return _fake


def _resolver_must_not_be_called(self, owner, slot=None):
    raise AssertionError(
        "R16-1/R16-4: _ResolveFeatureStrucOwner must NOT be called for "
        "this ClassName -- discrimination must happen before the "
        "resolver."
    )


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
def allo_ops(monkeypatch):
    """AllomorphOperations instance with __GetAllomorphObject stubbed to
    identity, so tests can hand it a plain _FakeAllomorph directly
    without needing a real SIL.LCModel cast."""
    from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

    monkeypatch.setattr(
        AllomorphOperations,
        "_AllomorphOperations__GetAllomorphObject",
        lambda self, x: x,
    )
    return AllomorphOperations(_FakeProject())


class TestAllomorphSyncCapture:
    """GetSyncableProperties dispatch, per ClassName (C1)."""

    def test_capture_affix_allomorph(self, monkeypatch, allo_ops):
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        calls = []
        monkeypatch.setattr(
            AllomorphOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls),
        )
        monkeypatch.setattr(
            AllomorphOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        guid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        allo = _FakeAllomorph("MoAffixAllomorph", MsEnvFeaturesOA=_FakeFeatStruct(guid))

        props = allo_ops.GetSyncableProperties(allo)

        assert calls == [(allo, None)]
        assert props["MsEnvFeaturesGuid"] == guid
        assert props["MsEnvFeatures"]["specs"] == {"FAKE-FEAT-GUID": "FAKE-VAL-GUID"}
        assert props["Form"] == {}
        assert props["MorphTypeRA"] is None

    def test_capture_affix_allomorph_null_struct_emits_no_feature_keys(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        monkeypatch.setattr(
            AllomorphOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        allo = _FakeAllomorph("MoAffixAllomorph", MsEnvFeaturesOA=None)
        props = allo_ops.GetSyncableProperties(allo)
        assert "MsEnvFeatures" not in props
        assert "MsEnvFeaturesGuid" not in props

    def test_capture_stem_allomorph_returns_no_feature_keys_and_never_calls_resolver(
        self, monkeypatch, allo_ops
    ):
        """R16-1: MoStemAllomorph has NO row in FEATURE_STRUC_OWNER_TABLE
        and carries no MsEnvFeaturesOA -- the resolver must never be
        consulted for it."""
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            AllomorphOperations,
            "_ResolveFeatureStrucOwner",
            _resolver_must_not_be_called,
        )

        allo = _FakeAllomorph("MoStemAllomorph")
        props = allo_ops.GetSyncableProperties(allo)
        assert "MsEnvFeatures" not in props
        assert "MsEnvFeaturesGuid" not in props

    def test_capture_unknown_class_name_returns_no_feature_keys_and_never_calls_resolver(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            AllomorphOperations,
            "_ResolveFeatureStrucOwner",
            _resolver_must_not_be_called,
        )

        allo = _FakeAllomorph("SomeOtherClassName")
        props = allo_ops.GetSyncableProperties(allo)
        assert "MsEnvFeatures" not in props
        assert "MsEnvFeaturesGuid" not in props


class TestAllomorphSyncApplyGuards:
    """Top-of-method guards, fire before touching item/resolver at all."""

    def test_none_item_raises_fp_parameter_error(self, allo_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="item is None"):
            allo_ops.ApplySyncableProperties(None, {})

    def test_non_dict_props_raises_fp_parameter_error(self, allo_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        allo = _FakeAllomorph("MoAffixAllomorph")
        with pytest.raises(FP_ParameterError, match="props must be a dict"):
            allo_ops.ApplySyncableProperties(allo, ["not", "a", "dict"])


class TestAllomorphSyncApplyPopBeforeSuper:
    """C6, explicit behavioural test (not just the static source lock
    above): the feature-struct key pair must never reach
    BaseOperations.ApplySyncableProperties / _apply_props_loop, which
    would route a C4 dict into the multistring branch and drop it."""

    def test_apply_pops_feature_keys_before_super(self, monkeypatch, allo_ops):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        super_calls = []
        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy(super_calls)
        )
        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            AllomorphOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        allo = _FakeAllomorph("MoAffixAllomorph")
        props = {
            "Form": {"en": "run"},
            "MsEnvFeatures": {"TypeGuid": None, "specs": {}},
            "MsEnvFeaturesGuid": "guid-x",
        }

        allo_ops.ApplySyncableProperties(allo, props)

        assert len(super_calls) == 1
        assert "MsEnvFeatures" not in super_calls[0]["props"]
        assert "MsEnvFeaturesGuid" not in super_calls[0]["props"]
        assert super_calls[0]["props"] == {"Form": {"en": "run"}}


class TestAllomorphSyncApplyPresenceGate:
    """
    C6: gate on key PRESENCE, never truthiness. T6b lesson applied FROM
    THE START (never introduced as a truthy-only fixture then amended):
    every fixture below carries a FALSY-BUT-PRESENT value so presence
    and truthiness come apart immediately.
    """

    def test_falsy_but_present_feature_struct_key_still_triggers_apply(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            AllomorphOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        allo = _FakeAllomorph("MoAffixAllomorph")
        # Both the struct key AND its guid sibling are PRESENT but FALSY.
        props = {"MsEnvFeatures": {}, "MsEnvFeaturesGuid": ""}

        allo_ops.ApplySyncableProperties(allo, props)

        assert len(apply_calls) == 1, (
            "A present-but-falsy MsEnvFeatures/MsEnvFeaturesGuid pair "
            "must still trigger _ApplyFeatureStruc (C6 presence gate, "
            "not truthiness)."
        )
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == ""

    def test_falsy_but_present_guid_only_key_still_triggers_apply(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            AllomorphOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        allo = _FakeAllomorph("MoAffixAllomorph")
        props = {"MsEnvFeaturesGuid": ""}

        allo_ops.ApplySyncableProperties(allo, props)

        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == ""

    def test_guid_only_present_still_triggers_apply_with_empty_spec(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            AllomorphOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        allo = _FakeAllomorph("MoAffixAllomorph")
        guid = "12121212-1212-1212-1212-121212121212"
        # "MsEnvFeatures" key intentionally ABSENT -- a present-but-empty
        # source struct emits only its Guid sibling (C4/C6).
        props = {"MsEnvFeaturesGuid": guid}

        allo_ops.ApplySyncableProperties(allo, props)

        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == guid

    def test_neither_key_present_never_calls_apply_feature_struc(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            AllomorphOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        allo = _FakeAllomorph("MoAffixAllomorph")
        allo_ops.ApplySyncableProperties(allo, {})

        assert apply_calls == []


class TestAllomorphSyncApplyStemAllomorphNoRaise:
    """
    R16-1/R16-4: MoStemAllomorph MUST NOT RAISE, even if a (careless)
    caller's props dict carries the MsEnvFeatures* keys it should never
    have -- discrimination happens before the resolver is ever
    consulted.
    """

    def test_apply_never_calls_resolver_and_does_not_raise(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            AllomorphOperations,
            "_ResolveFeatureStrucOwner",
            _resolver_must_not_be_called,
        )

        allo = _FakeAllomorph("MoStemAllomorph")
        props = {
            "MsEnvFeatures": {"specs": {}},
            "MsEnvFeaturesGuid": "should-be-ignored",
        }

        # Must not raise -- AssertionError from the resolver stub above
        # would surface here if the resolver were wrongly consulted.
        allo_ops.ApplySyncableProperties(allo, props)


class TestAllomorphSyncApplyRaisePropagationThroughPublicSurface:
    """
    C7 raise-PROPAGATION coverage only -- NOT enforcement coverage (T6b
    item 2's lesson applied from the start). The test double raises
    unconditionally and never reads on_unresolved; the assertion that
    actually locks C7 is that the recorded call carried
    on_unresolved == "raise", which DOES die under a raise->skip
    mutation. Real enforcement is locked by the live test
    test_apply_raises_on_unresolved_feature_guid (Section D).
    """

    def test_apply_propagates_fp_parameter_error_and_passes_raise_policy(
        self, monkeypatch, allo_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations, FP_ParameterError
        from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            AllomorphOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        bogus_guid = "00000000-0000-0000-0000-0000000000ff"
        records = []
        monkeypatch.setattr(
            AllomorphOperations,
            "_ApplyFeatureStruc",
            _make_apply_spy(records, raise_guid=bogus_guid),
        )

        allo = _FakeAllomorph("MoAffixAllomorph")
        props = {
            "MsEnvFeatures": {"TypeGuid": None, "specs": {"f": bogus_guid}},
            "MsEnvFeaturesGuid": "11111111-1111-1111-1111-111111111111",
        }

        with pytest.raises(FP_ParameterError, match=bogus_guid):
            allo_ops.ApplySyncableProperties(allo, props)

        assert len(records) == 1
        assert records[0]["on_unresolved"] == "raise", (
            "AllomorphOperations.__ApplyFeatureStrucProp must call "
            "_ApplyFeatureStruc with on_unresolved='raise' "
            "unconditionally (C7) -- this is the assertion that would "
            "fail if that were mutated to 'skip'."
        )


# ============================================================================
# Section D: LIVE coverage (target_sandbox -- tempdir copy of Target)
# ============================================================================

TEST_PREFIX = "TEST_"


def _make_entry(sandbox, tag):
    """Create a TEST_-prefixed entry on the live Target sandbox."""
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


@pytest.mark.requires_live_project
class TestT8LiveHasattrTrap:
    """
    STEP 1 of the T8 dispatch: measure the hasattr truth table for a
    BARE `sandbox.Object(hvo)` view of a real MoAffixAllomorph BEFORE
    trusting any gate -- committed here as a DURABLE regression test
    (never deleted after one run). At cycle 13 a deleted probe file cost
    P1 its provenance for T7; this file does not repeat that.
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_bare_moaffixallomorph_hasattr_all_four_false(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8_hasattr")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}suf", morphType="suffix"
            )
            bare = sandbox.Object(allo.Hvo)
            assert bare.ClassName == "MoAffixAllomorph"
            assert not hasattr(bare, "Form"), (
                "P1 falsified: Form reachable on a bare ICmObject."
            )
            assert not hasattr(bare, "IsAbstract"), (
                "P1 falsified: IsAbstract reachable on a bare ICmObject."
            )
            assert not hasattr(bare, "MorphTypeRA"), (
                "P1 falsified: MorphTypeRA reachable on a bare ICmObject."
            )
            assert not hasattr(bare, "MsEnvFeaturesOA"), (
                "P1 falsified: MsEnvFeaturesOA reachable on a bare "
                "ICmObject."
            )
        finally:
            sandbox.LexEntry.Delete(entry)


@pytest.mark.requires_live_project
class TestT8LiveDirectCast:
    """
    A DIRECT, mutation-resistant live test of __GetAllomorphObject's C2
    cast (the item T6b item 1 gated Checkpoint 3b on, replicated here).
    Reads a SUBTYPE-ONLY member (MsEnvFeaturesOA, declared on
    IMoAffixAllomorph) straight off the returned object -- unreachable
    on the bare ICmObject sandbox.Object(hvo) returns.
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_hvo_path_casts_to_concrete_affix_allomorph(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8_cast")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}cast", morphType="suffix"
            )
            hvo = allo.Hvo

            assert not hasattr(sandbox.Object(hvo), "MsEnvFeaturesOA")

            result = sandbox.Allomorphs._AllomorphOperations__GetAllomorphObject(hvo)
            assert result.ClassName == "MoAffixAllomorph"
            assert result.MsEnvFeaturesOA is None
        finally:
            sandbox.LexEntry.Delete(entry)


@pytest.mark.requires_live_project
class TestT8LiveRoundTrip:
    """
    Real capture -> apply -> RE-READ round trip against a live
    target_sandbox. All read-back assertions re-fetch from a FRESH
    sandbox.Object(hvo) after the write, never from the reference held
    at write time.
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_ms_env_features_capture_apply_roundtrip(self, target_sandbox):
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_t8_feat", "t8f", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_t8_val", "t8v")

        src_entry = _make_entry(sandbox, "t8_src")
        tgt_entry = _make_entry(sandbox, "t8_tgt")
        try:
            src_allo = sandbox.Allomorphs.Create(
                src_entry, f"{TEST_PREFIX}src", morphType="suffix"
            )
            tgt_allo = sandbox.Allomorphs.Create(
                tgt_entry, f"{TEST_PREFIX}tgt", morphType="suffix"
            )

            sandbox.Allomorphs._ApplyFeatureStruc(
                src_allo, "MsEnvFeaturesOA",
                [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
                on_unresolved="raise", label="TEST src Allomorph MsEnvFeatures",
            )

            src_bare = sandbox.Object(src_allo.Hvo)
            props = sandbox.Allomorphs.GetSyncableProperties(src_bare)
            expected_specs = {str(feat.Guid): str(value.Guid)}
            assert props["MsEnvFeatures"]["specs"] == expected_specs
            assert props["MsEnvFeaturesGuid"]

            sandbox.Allomorphs.ApplySyncableProperties(tgt_allo, props)

            tgt_bare = sandbox.Object(tgt_allo.Hvo)
            reread_props = sandbox.Allomorphs.GetSyncableProperties(tgt_bare)
            assert reread_props["MsEnvFeatures"]["specs"] == expected_specs
        finally:
            sandbox.LexEntry.Delete(src_entry)
            sandbox.LexEntry.Delete(tgt_entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_hvo_entry_path_captures_form(self, target_sandbox):
        """
        P1 pin: GetSyncableProperties(hvo) must capture Form on the HVO
        entry path -- this is the silent-drop bug (defect i/ii) fixed
        together, independent of the new MsEnvFeatures key.
        """
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8_hvo_form")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}hvoform", morphType="suffix"
            )
            hvo = allo.Hvo
            props_by_hvo = sandbox.Allomorphs.GetSyncableProperties(hvo)
            props_by_obj = sandbox.Allomorphs.GetSyncableProperties(allo)
            assert props_by_hvo["Form"], (
                "Defects (i)/(ii): HVO entry path silently dropped Form."
            )
            assert props_by_hvo["Form"] == props_by_obj["Form"]
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_apply_raises_on_unresolved_feature_guid(self, target_sandbox):
        from flexicon.code.BaseOperations import FP_ParameterError

        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8_unresolved")
        try:
            tgt_allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}unres", morphType="suffix"
            )
            bogus_feat_guid = "00000000-0000-0000-0000-0000000000aa"
            bogus_val_guid = "00000000-0000-0000-0000-0000000000bb"
            props = {
                "MsEnvFeatures": {
                    "TypeGuid": None,
                    "specs": {bogus_feat_guid: bogus_val_guid},
                },
                "MsEnvFeaturesGuid": "00000000-0000-0000-0000-0000000000cc",
            }

            with pytest.raises(FP_ParameterError, match=bogus_feat_guid):
                sandbox.Allomorphs.ApplySyncableProperties(tgt_allo, props)
        finally:
            sandbox.LexEntry.Delete(entry)


@pytest.mark.requires_live_project
class TestT8LiveStemAllomorphNoFeatureKeys:
    """
    P2 live half: a REAL MoStemAllomorph's capture must not raise and
    must emit neither MsEnvFeatures nor MsEnvFeaturesGuid. Mutation
    M-T8-2 (deleting the `if class_name == "MoAffixAllomorph"` guard so
    the resolver runs unconditionally) is expected to make this test
    FAIL with FP_ParameterError naming "MoStemAllomorph".
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_real_live_stem_allomorph_capture_emits_no_feature_keys_and_does_not_raise(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8_stem")
        try:
            stem_allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}stem", morphType="stem"
            )
            assert stem_allo.ClassName == "MoStemAllomorph"

            props = sandbox.Allomorphs.GetSyncableProperties(stem_allo)
            assert "MsEnvFeatures" not in props
            assert "MsEnvFeaturesGuid" not in props
        finally:
            sandbox.LexEntry.Delete(entry)
