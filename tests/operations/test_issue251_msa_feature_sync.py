#
#   test_issue251_msa_feature_sync.py
#
#   Class: TestMSASyncStatic / TestMSASyncCapture / TestMSASyncApply*
#          Coverage for MSAOperations.GetSyncableProperties /
#          ApplySyncableProperties -- spec feature-structure-sync-gap,
#          task T6, closes issue #251.
#
#   Context: MSAOperations previously had ZERO sync methods, so every MSA
#   (MoStemMsa / MoInflAffMsa / MoDerivAffMsa) synced across projects with
#   a correct ClassName/POS but a permanently null feature structure
#   (MsFeaturesOA / InflFeatsOA / From+ToMsFeaturesOA). The frozen C1 table
#   (spec.md section 4) resolves each ClassName's owning property by
#   ClassName + explicit slot= (MoDerivAffMsa is ambiguous: "From"/"To").
#
#   Sections A-C are entirely OFFLINE (no live FLEx project): Section A
#   locks the source SHAPE (zero hasattr gates, pop-before-super,
#   presence-not-truthiness gating, MoUnclassifiedAffixMsa discriminated
#   before the resolver). Sections B/C drive the real
#   GetSyncableProperties/ApplySyncableProperties dispatch against
#   pure-Python fake MSA objects, monkeypatching the three BaseOperations
#   feature-struct seams (_ResolveFeatureStrucOwner / _GetFeatureStruc /
#   _ApplyFeatureStruc) and MSAOperations' own HVO/GUID resolver
#   (__GetMsaObject) so no real SIL.LCModel cast or live project is
#   required.
#
#   Section D (bottom of file, `requires_live_project`) is the LIVE
#   coverage: real IFsFeatStruc capture/apply round-trips against a
#   `target_sandbox` (tempdir copy of Target), the C2 HVO/GUID-path cast,
#   the MoUnclassifiedAffixMsa no-raise guarantee against a REAL LCM
#   object, and the C7 unresolved-GUID raise. See
#   specs/feature-structure-sync-gap/evidence/live-T6.md for the
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
    MSAOperations has module-level `from SIL.LCModel import ...` statements.
    On a machine without FieldWorks installed, that import ERRORs rather
    than skipping cleanly -- so skip explicitly instead. Nothing in this
    file opens a live project.
    """
    pytest.importorskip("SIL.LCModel")


def _method_source(method_name):
    from flexicon.code.Lexicon.MSAOperations import MSAOperations

    obj = MSAOperations.__dict__[method_name]

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
    '_MSAOperations__GetMsaObject')."""
    from flexicon.code.Lexicon.MSAOperations import MSAOperations

    obj = MSAOperations.__dict__[mangled_name]
    return inspect.getsource(obj)


def _hasattr_second_args(src):
    """
    Walk the full AST of a function's source (docstring included -- a
    plain string literal in the docstring never produces an ast.Call
    node, so it cannot false-positive here) and return the second-
    argument string literal of every top-level-or-nested `hasattr(...)`
    call found anywhere in the body.

    T6b item 4: this is STRICTLY STRONGER than the old `"hasattr" not
    in src` substring check -- it would catch a hasattr probe added
    anywhere in the body (nested in an `if`, a comprehension, etc.),
    not just literal-text presence, and it lets a caller allowlist
    *which* attribute names are legitimate rather than banning the
    token outright.
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
    source-pattern assertions test CODE, not prose -- several of this
    file's docstrings deliberately use words like 'hasattr' and
    '_ResolveFeatureStrucOwner' descriptively, which would otherwise
    produce false matches/orderings against the assertions below.
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


class TestMSASyncStatic:
    """Locks the shape of the #251 fix without exercising any LCM object."""

    def test_zero_hasattr_gates_on_feature_struct_props(self):
        """
        R2/D5: the whole point of this fix is that a hasattr gate on a
        feature-struct property is dead code (0/2088 True under
        pythonnet). None of the new sync surface may contain 'hasattr'
        at all -- dispatch is entirely .ClassName-driven.
        """
        for name in (
            "GetSyncableProperties",
            "ApplySyncableProperties",
        ):
            src = _body_only(_method_source(name))
            assert "hasattr" not in src, (
                f"MSAOperations.{name} must not gate on hasattr for a "
                f"feature-struct property (dead code under pythonnet, "
                f"D5)."
            )
        for mangled in (
            "_MSAOperations__CaptureFeatureStrucProp",
            "_MSAOperations__ApplyFeatureStrucProp",
        ):
            src = _body_only(_private_method_source(mangled))
            assert "hasattr" not in src, (
                f"MSAOperations.{mangled} must not gate on hasattr for a "
                f"feature-struct property (dead code under pythonnet, "
                f"D5)."
            )

    def test_unclassified_affix_discriminated_before_resolver_in_capture(self):
        """
        R2: MoUnclassifiedAffixMsa must be checked BEFORE any branch that
        can reach the resolver (via __CaptureFeatureStrucProp), so
        capturing one (routinely created by CreateUnclassifiedAffix)
        never raises.
        """
        src = _body_only(_method_source("GetSyncableProperties"))
        unclass_idx = src.index('"MoUnclassifiedAffixMsa"')
        first_dispatch_idx = src.index('"MoStemMsa"')
        assert unclass_idx < first_dispatch_idx, (
            "GetSyncableProperties must discriminate MoUnclassifiedAffixMsa "
            "BEFORE dispatching to any resolver-calling branch (R2)."
        )

    def test_unclassified_affix_discriminated_before_resolver_in_apply(self):
        src = _body_only(_method_source("ApplySyncableProperties"))
        unclass_idx = src.index('"MoUnclassifiedAffixMsa"')
        # The apply-side ApplySyncableProperties method body itself never
        # names _ResolveFeatureStrucOwner directly (it delegates to the
        # private helper) -- confirm the ClassName check appears before
        # any of the three dispatching class_name branches that DO reach
        # the resolver (via __ApplyFeatureStrucProp).
        first_dispatch_idx = src.index('"MoStemMsa"')
        assert unclass_idx < first_dispatch_idx, (
            "ApplySyncableProperties must discriminate MoUnclassifiedAffixMsa "
            "BEFORE dispatching to any resolver-calling branch (R2)."
        )

    def test_pop_before_super_source_shape(self):
        """
        C6: the eight feature-struct keys must be filtered OUT of the
        dict passed to super().ApplySyncableProperties -- confirmed
        behaviourally in TestMSASyncApplyPopBeforeSuper below; this pins
        the source shape too (filter must appear before the super() call
        textually, matching NaturalClassOperations' precedent).
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
            _private_method_source("_MSAOperations__ApplyFeatureStrucProp")
        )
        assert "in props" in src, (
            "__ApplyFeatureStrucProp must gate on key PRESENCE ('in "
            "props'), never on the value's truthiness (C6)."
        )
        assert "props.get(key) or {}" in src, (
            "A present-but-empty spec must default to {} (an empty but "
            "attached struct), not be treated as absent."
        )

    def test_get_msa_object_casts_on_hvo_and_guid_path(self):
        """
        C2: FLExProject.Object(hvo_or_guid) returns a bare ICmObject;
        __GetMsaObject must cast to the concrete MSA interface before
        returning, for both the HVO (int) and GUID (str) entry paths.
        """
        src = _body_only(_private_method_source("_MSAOperations__GetMsaObject"))
        assert "self.project.Object(msa_or_hvo)" in src
        assert "IMoStemMsa" in src and "IMoInflAffMsa" in src
        assert "IMoDerivAffMsa" in src and "IMoUnclassifiedAffixMsa" in src

    # T6b item 4: the zero-hasattr rule above (test_zero_hasattr_gates_on_
    # feature_struct_props) is correct for GetSyncableProperties/
    # ApplySyncableProperties/__CaptureFeatureStrucProp/
    # __ApplyFeatureStrucProp -- those four have NO legitimate reason to
    # call hasattr on anything. __GetMsaObject is different: it has ONE
    # hasattr call (`hasattr(msa_or_hvo, "_obj")`, MSAOperations.py:1144)
    # that is a Python-level wrapper-unwrap, not a probe for a subtype-
    # declared LCM member -- a blanket ban would force deleting working
    # code. The rule this test encodes instead (per lead ruling 1):
    # hasattr() on a SUBTYPE-DECLARED LCM member (e.g. MsFeaturesOA,
    # InflFeatsOA) is forbidden; hasattr() on "_obj", "ClassName", "Hvo"
    # -- all present regardless of concrete ClassName -- is permitted.
    _ALLOWED_HASATTR_ATTRS = frozenset({"_obj", "ClassName", "Hvo"})

    def test_get_msa_object_hasattr_calls_are_allowlisted(self):
        """
        D5 / T6b item 4: every hasattr() call inside __GetMsaObject must
        target only "_obj" / "ClassName" / "Hvo" -- never a subtype-
        declared member. MSAOperations.py:1144's
        `hasattr(msa_or_hvo, "_obj")` is confirmed legitimate (wrapper
        unwrap); this test would fail loudly if a future edit added a
        hasattr probe on something like "MsFeaturesOA" instead of the
        ClassName-driven cast table that follows it.
        """
        src = _private_method_source("_MSAOperations__GetMsaObject")
        names = _hasattr_second_args(src)
        assert names, (
            "expected at least one hasattr() call in __GetMsaObject "
            "(the _obj wrapper-unwrap at :1144) -- if this is empty the "
            "method changed shape and this test's premise needs "
            "re-examining, not deleting."
        )
        for attr in names:
            assert attr in self._ALLOWED_HASATTR_ATTRS, (
                f"__GetMsaObject calls hasattr(x, {attr!r}) -- only "
                f"{sorted(self._ALLOWED_HASATTR_ATTRS)} are permitted. "
                f"A subtype-declared LCM member must be discriminated "
                f"via .ClassName + explicit cast, never hasattr (D5)."
            )

    def test_resolve_feature_struc_owner_hasattr_calls_are_allowlisted(self):
        """
        Same allowlisted rule as above, applied to
        BaseOperations._ResolveFeatureStrucOwner (def at
        BaseOperations.py:1717) -- NOTE this reaches outside
        MSAOperations into the shared BaseOperations class; it is
        included here (rather than left as a stated boundary) because
        the rule and the allowlist are identical and lead ruling 1
        already confirmed all three of that method's hasattr calls
        (":obj" at :1819/:1821, "ClassName" at :1824) are legitimate.
        """
        from flexicon.code.BaseOperations import BaseOperations

        src = inspect.getsource(
            BaseOperations.__dict__["_ResolveFeatureStrucOwner"]
        )
        names = _hasattr_second_args(src)
        assert names, "expected hasattr() calls in _ResolveFeatureStrucOwner"
        for attr in names:
            assert attr in self._ALLOWED_HASATTR_ATTRS, (
                f"_ResolveFeatureStrucOwner calls hasattr(x, {attr!r}) -- "
                f"only {sorted(self._ALLOWED_HASATTR_ATTRS)} are "
                f"permitted (D5)."
            )


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


class _FakeMsa:
    """Stand-in for an LCM MSA object: just a ClassName plus whatever
    feature-struct-owning attributes the test wants populated."""

    def __init__(self, class_name, **attrs):
        self.ClassName = class_name
        for k, v in attrs.items():
            setattr(self, k, v)


class _FakeProject:
    """Minimal stand-in -- every test in this file monkeypatches away the
    three feature-struct seams and __GetMsaObject, so MSAOperations never
    actually touches self.project."""

    writeEnabled = True


# The MSA subset of the frozen C1 table (spec.md section 4), used only to
# drive the fake resolver below -- NOT a second copy of
# FEATURE_STRUC_OWNER_TABLE (that single copy lives in
# Shared/lcm_constants.py and is exercised for real by the live tests).
_MSA_PROP_BY_CLASS_AND_SLOT = {
    ("MoStemMsa", None): "MsFeaturesOA",
    ("MoInflAffMsa", None): "InflFeatsOA",
    ("MoDerivAffMsa", "From"): "FromMsFeaturesOA",
    ("MoDerivAffMsa", "To"): "ToMsFeaturesOA",
}


def _make_fake_resolver(calls):
    def _fake(self, owner, slot=None):
        calls.append((owner, slot))
        prop_name = _MSA_PROP_BY_CLASS_AND_SLOT[(owner.ClassName, slot)]
        return owner, prop_name

    return _fake


def _resolver_must_not_be_called(self, owner, slot=None):
    raise AssertionError(
        "R2: _ResolveFeatureStrucOwner must NOT be called for this "
        "ClassName -- discrimination must happen before the resolver."
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
def msa_ops(monkeypatch):
    """MSAOperations instance with __GetMsaObject stubbed to identity, so
    tests can hand it a plain _FakeMsa directly without needing a real
    SIL.LCModel cast."""
    from flexicon.code.Lexicon.MSAOperations import MSAOperations

    monkeypatch.setattr(
        MSAOperations, "_MSAOperations__GetMsaObject", lambda self, x: x
    )
    return MSAOperations(_FakeProject())


class TestMSASyncCapture:
    """GetSyncableProperties dispatch, per ClassName (C1)."""

    def test_capture_stem_msa(self, monkeypatch, msa_ops):
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        calls = []
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver(calls)
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        guid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        msa = _FakeMsa("MoStemMsa", MsFeaturesOA=_FakeFeatStruct(guid))

        props = msa_ops.GetSyncableProperties(msa)

        assert calls == [(msa, None)]
        assert props["MsFeaturesGuid"] == guid
        assert props["MsFeatures"]["specs"] == {"FAKE-FEAT-GUID": "FAKE-VAL-GUID"}
        assert set(props.keys()) == {"MsFeatures", "MsFeaturesGuid"}

    def test_capture_stem_msa_null_struct_emits_no_keys(self, monkeypatch, msa_ops):
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        msa = _FakeMsa("MoStemMsa", MsFeaturesOA=None)
        props = msa_ops.GetSyncableProperties(msa)
        assert props == {}

    def test_capture_infl_aff_msa(self, monkeypatch, msa_ops):
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        calls = []
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver(calls)
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        guid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        msa = _FakeMsa("MoInflAffMsa", InflFeatsOA=_FakeFeatStruct(guid))

        props = msa_ops.GetSyncableProperties(msa)

        assert calls == [(msa, None)]
        assert props["InflFeatsGuid"] == guid
        assert set(props.keys()) == {"InflFeats", "InflFeatsGuid"}

    def test_capture_deriv_aff_msa_both_slots_populated(self, monkeypatch, msa_ops):
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        calls = []
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver(calls)
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        from_guid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        to_guid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        msa = _FakeMsa(
            "MoDerivAffMsa",
            FromMsFeaturesOA=_FakeFeatStruct(from_guid),
            ToMsFeaturesOA=_FakeFeatStruct(to_guid),
        )

        props = msa_ops.GetSyncableProperties(msa)

        assert calls == [(msa, "From"), (msa, "To")]
        assert props["FromMsFeaturesGuid"] == from_guid
        assert props["ToMsFeaturesGuid"] == to_guid
        assert set(props.keys()) == {
            "FromMsFeatures", "FromMsFeaturesGuid",
            "ToMsFeatures", "ToMsFeaturesGuid",
        }

    def test_capture_deriv_aff_msa_only_one_slot_populated(
        self, monkeypatch, msa_ops
    ):
        """Presence gate on the CAPTURE side too: an unpopulated slot
        emits neither of its keys, even though the resolver is still
        consulted for it (only ClassName gates the resolver call)."""
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        calls = []
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver(calls)
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc
        )

        to_guid = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        msa = _FakeMsa(
            "MoDerivAffMsa", FromMsFeaturesOA=None, ToMsFeaturesOA=_FakeFeatStruct(to_guid)
        )

        props = msa_ops.GetSyncableProperties(msa)

        assert calls == [(msa, "From"), (msa, "To")]
        assert set(props.keys()) == {"ToMsFeatures", "ToMsFeaturesGuid"}

    def test_capture_unclassified_affix_returns_empty_and_never_calls_resolver(
        self, monkeypatch, msa_ops
    ):
        """R2: must not raise, and must never reach the resolver."""
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _resolver_must_not_be_called
        )

        msa = _FakeMsa("MoUnclassifiedAffixMsa")
        props = msa_ops.GetSyncableProperties(msa)
        assert props == {}

    def test_capture_unknown_class_name_returns_empty_and_never_calls_resolver(
        self, monkeypatch, msa_ops
    ):
        """
        A ClassName outside the C1 table's four in-scope MSA rows (e.g.
        MoDerivStepMsa, explicitly excluded per spec.md section 4) must
        not raise via this capture path either -- the resolver is simply
        never consulted for it.
        """
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _resolver_must_not_be_called
        )

        msa = _FakeMsa("MoDerivStepMsa")
        props = msa_ops.GetSyncableProperties(msa)
        assert props == {}


class TestMSASyncApplyGuards:
    """Top-of-method guards, fire before touching msa/resolver at all."""

    def test_none_item_raises_fp_parameter_error(self, msa_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="item is None"):
            msa_ops.ApplySyncableProperties(None, {})

    def test_non_dict_props_raises_fp_parameter_error(self, msa_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        msa = _FakeMsa("MoStemMsa")
        with pytest.raises(FP_ParameterError, match="props must be a dict"):
            msa_ops.ApplySyncableProperties(msa, ["not", "a", "dict"])


class TestMSASyncApplyPopBeforeSuper:
    """C6, explicit behavioural test (not just the static source lock
    above): the eight feature-struct keys must never reach
    BaseOperations.ApplySyncableProperties / _apply_props_loop, which
    would route a C4 dict into the multistring branch and drop it."""

    def test_apply_pops_all_eight_feature_keys_before_super(
        self, monkeypatch, msa_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        super_calls = []
        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy(super_calls)
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            MSAOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        msa = _FakeMsa("MoStemMsa")
        props = {
            "MsFeatures": {"TypeGuid": None, "specs": {}},
            "MsFeaturesGuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "SomeOtherPlainProp": "value",
        }

        msa_ops.ApplySyncableProperties(msa, props)

        assert len(super_calls) == 1
        received = super_calls[0]["props"]
        for key in (
            "MsFeatures", "MsFeaturesGuid",
            "InflFeats", "InflFeatsGuid",
            "FromMsFeatures", "FromMsFeaturesGuid",
            "ToMsFeatures", "ToMsFeaturesGuid",
        ):
            assert key not in received, (
                f"{key!r} must be popped out of props before "
                f"super().ApplySyncableProperties is called (C6) -- "
                f"BaseOperations._apply_props_loop would route this dict "
                f"into the multistring path and silently drop it."
            )
        assert received == {"SomeOtherPlainProp": "value"}
        # The C4 dict itself must still reach _ApplyFeatureStruc, not be
        # dropped outright.
        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] == {"TypeGuid": None, "specs": {}}


class TestMSASyncApplyPresenceGate:
    """
    C6: gate on key PRESENCE, never truthiness.

    Cycle-10 mutation finding: the two tests below this docstring
    (pre-existing) cannot actually separate a presence gate from a
    truthiness gate, because the fixture's Guid value
    ("12121212-...") is truthy in both cases where it is exercised --
    mutating `__ApplyFeatureStrucProp`'s `if key in props or guid_key
    in props:` to `if props.get(key) or props.get(guid_key):` left both
    green, since a truthy guid_key still passes a truthiness check. The
    two FALSY-BUT-PRESENT tests added below make presence and
    truthiness come apart on purpose: `{}` and `""` are both PRESENT
    but FALSY, so a truthiness-gated implementation would (wrongly)
    treat them as absent and skip `_ApplyFeatureStruc` -- offline-
    mutation-verified, see specs/feature-structure-sync-gap/evidence/
    live-T6b.md.
    """

    def test_falsy_but_present_feature_struct_key_still_triggers_apply(
        self, monkeypatch, msa_ops
    ):
        """
        The "MsFeatures" key present with a FALSY value ({}) must still
        trigger _ApplyFeatureStruc -- `if key in props` is True even
        though `props[key]` itself is falsy. A truthiness-gated
        `if props.get(key) or props.get(guid_key):` would (wrongly)
        treat an all-falsy props dict as "nothing to apply" and skip.
        """
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            MSAOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        msa = _FakeMsa("MoStemMsa")
        # Both the struct key AND its guid sibling are PRESENT but FALSY.
        props = {"MsFeatures": {}, "MsFeaturesGuid": ""}

        msa_ops.ApplySyncableProperties(msa, props)

        assert len(apply_calls) == 1, (
            "A present-but-falsy MsFeatures/MsFeaturesGuid pair must "
            "still trigger _ApplyFeatureStruc (C6 presence gate, not "
            "truthiness)."
        )
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == ""

    def test_falsy_but_present_guid_only_key_still_triggers_apply(
        self, monkeypatch, msa_ops
    ):
        """
        Same as above but only the Guid sibling is present -- and it
        too is falsy ("", not merely absent). Distinguishes this from
        test_guid_only_present_still_triggers_apply_with_empty_spec
        below, whose Guid value is truthy.
        """
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            MSAOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        msa = _FakeMsa("MoStemMsa")
        props = {"MsFeaturesGuid": ""}

        msa_ops.ApplySyncableProperties(msa, props)

        assert len(apply_calls) == 1, (
            "A present-but-falsy MsFeaturesGuid (with MsFeatures "
            "absent) must still trigger _ApplyFeatureStruc."
        )
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == ""

    def test_guid_only_present_still_triggers_apply_with_empty_spec(
        self, monkeypatch, msa_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            MSAOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        msa = _FakeMsa("MoStemMsa")
        guid = "12121212-1212-1212-1212-121212121212"
        # "MsFeatures" key intentionally ABSENT -- a present-but-empty
        # source struct emits only its Guid sibling (C4/C6).
        props = {"MsFeaturesGuid": guid}

        msa_ops.ApplySyncableProperties(msa, props)

        assert len(apply_calls) == 1, (
            "A present MsFeaturesGuid with no MsFeatures key must still "
            "trigger _ApplyFeatureStruc -- gating on truthiness of "
            "props.get('MsFeatures') alone would wrongly skip this "
            "present-but-empty case (C6)."
        )
        assert apply_calls[0]["spec_dict"] == {}
        assert apply_calls[0]["struct_guid"] == guid

    def test_neither_key_present_never_calls_apply_feature_struc(
        self, monkeypatch, msa_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        apply_calls = []
        monkeypatch.setattr(
            MSAOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        msa = _FakeMsa("MoStemMsa")
        msa_ops.ApplySyncableProperties(msa, {})

        assert apply_calls == []


class TestMSASyncApplyDerivAffBothSlots:
    def test_apply_dispatches_both_slots_with_correct_prop_names(
        self, monkeypatch, msa_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        resolver_calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(resolver_calls),
        )
        apply_calls = []
        monkeypatch.setattr(
            MSAOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        msa = _FakeMsa("MoDerivAffMsa")
        props = {
            "FromMsFeatures": {"TypeGuid": None, "specs": {}},
            "FromMsFeaturesGuid": "from-guid",
            "ToMsFeatures": {"TypeGuid": None, "specs": {}},
            "ToMsFeaturesGuid": "to-guid",
        }

        msa_ops.ApplySyncableProperties(msa, props)

        assert resolver_calls == [(msa, "From"), (msa, "To")]
        assert [c["prop_name"] for c in apply_calls] == [
            "FromMsFeaturesOA", "ToMsFeaturesOA",
        ]
        assert apply_calls[0]["struct_guid"] == "from-guid"
        assert apply_calls[1]["struct_guid"] == "to-guid"


class TestMSASyncApplyUnclassifiedAffixNoRaise:
    """
    R2: MoUnclassifiedAffixMsa MUST NOT RAISE, even if a (careless)
    caller's props dict carries feature-struct keys it should never have
    -- discrimination happens before the resolver is ever consulted.

    T6b item 5 (NO NEW TEST -- this is a scope note, not a new
    assertion): cycle-10 mutation testing found this class's
    behavioural coverage is STRUCTURALLY IMPOSSIBLE to make
    mutation-resistant. `ApplySyncableProperties`'s if/elif dispatch
    (MSAOperations.py:1003 area) EXCLUDES MoUnclassifiedAffixMsa from
    every branch that reaches the resolver -- so removing BOTH the
    "MoUnclassifiedAffixMsa: return early" short-circuit AND the
    `_resolver_must_not_be_called` stub's reason for existing left this
    no-raise test green regardless, because there is simply no code
    path left that COULD raise for this ClassName even without the
    short-circuit (the else-branch below the if/elif is a silent no-op,
    not a fallthrough into the stem/infl/deriv branches). The real lock
    on R2's discrimination-BEFORE-resolver ordering is the two static
    AST tests test_unclassified_affix_discriminated_before_resolver_in_
    capture and ..._in_apply (TestMSASyncStatic, Section A) -- do not
    chase a behavioural test here that cannot exist.
    """

    def test_apply_never_calls_resolver_and_does_not_raise(
        self, monkeypatch, msa_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _resolver_must_not_be_called
        )

        msa = _FakeMsa("MoUnclassifiedAffixMsa")
        props = {
            "MsFeatures": {"specs": {}},
            "MsFeaturesGuid": "should-be-ignored",
        }

        # Must not raise -- AssertionError from the resolver stub above
        # would surface here if the resolver were wrongly consulted.
        msa_ops.ApplySyncableProperties(msa, props)


class TestMSASyncApplyRaisePropagationThroughPublicSurface:
    """
    C7 raise-PROPAGATION coverage only -- NOT enforcement coverage.

    Renamed from TestMSASyncApplyRaisesOnUnresolvedGuid (T6b item 2).
    Cycle-10 mutation finding: this class's test double
    (_make_apply_spy) raises unconditionally whenever `raise_guid` is
    passed, and never reads the `on_unresolved` argument it receives --
    so mutating MSAOperations.__ApplyFeatureStrucProp's hardcoded
    `on_unresolved="raise"` to `"skip"` left this test green (the spy
    doesn't care what policy string arrived, it raises regardless).
    That means this class was never actually locking C7's real
    enforcement -- only that *when* _ApplyFeatureStruc happens to
    raise, MSAOperations.ApplySyncableProperties propagates rather than
    swallows it. Per lead ruling 2, the fix is NOT to make the spy
    branch on on_unresolved (that would re-implement production policy
    inside the test double, and the test would then pass by agreeing
    with itself) -- it is to (a) keep the propagation coverage, and
    (b) additionally assert the recorded call actually carried
    on_unresolved == "raise", which DOES die under the raise->skip
    mutation. C7's real enforcement lock remains the live test
    test_apply_raises_on_unresolved_feature_guid (:897 area below,
    against a REAL unresolved GUID with no mocked _ApplyFeatureStruc).
    """

    def test_apply_propagates_fp_parameter_error_and_passes_raise_policy(
        self, monkeypatch, msa_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations, FP_ParameterError
        from flexicon.code.Lexicon.MSAOperations import MSAOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _make_fake_resolver([])
        )
        bogus_guid = "00000000-0000-0000-0000-0000000000ff"
        records = []
        monkeypatch.setattr(
            MSAOperations,
            "_ApplyFeatureStruc",
            _make_apply_spy(records, raise_guid=bogus_guid),
        )

        msa = _FakeMsa("MoStemMsa")
        props = {
            "MsFeatures": {"TypeGuid": None, "specs": {"f": bogus_guid}},
            "MsFeaturesGuid": "11111111-1111-1111-1111-111111111111",
        }

        with pytest.raises(FP_ParameterError, match=bogus_guid):
            msa_ops.ApplySyncableProperties(msa, props)

        # Dies under the raise->skip mutation the spy itself cannot
        # catch: confirms MSAOperations actually asked for "raise"
        # policy on this call, not merely that the spy (which raises
        # unconditionally regardless of the value passed) was invoked.
        assert len(records) == 1
        assert records[0]["on_unresolved"] == "raise", (
            "MSAOperations.__ApplyFeatureStrucProp must call "
            "_ApplyFeatureStruc with on_unresolved='raise' "
            "unconditionally (C7) -- this is the one assertion in this "
            "class that would fail if that were mutated to 'skip'."
        )


# ============================================================================
# Section D: LIVE coverage (target_sandbox -- tempdir copy of Target)
# ============================================================================


@pytest.fixture
def live_msa_factory(target_sandbox):
    """
    A live entry + POS, plus a `_new_sense()` helper (each MSA type needs
    its own sense to attach to -- one sense holds exactly one
    MorphoSyntaxAnalysisRA). Yields (sandbox, entry, new_sense, pos_obj).
    """
    from SIL.LCModel import ILexSenseFactory

    sandbox = target_sandbox
    entry = sandbox.LexEntry.Create(lexeme_form="TEST_msa251")
    pos_obj = sandbox.POS.Create("TEST_msa251_pos", "t25p")

    def _new_sense():
        factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
        new_sense = factory.Create()
        entry.SensesOS.Add(new_sense)
        return new_sense

    yield sandbox, entry, _new_sense, pos_obj

    try:
        sandbox.LexEntry.Delete(entry)
    except Exception:
        pass
    try:
        sandbox.POS.Delete(pos_obj)
    except Exception:
        pass


@pytest.mark.requires_live_project
class TestMSASyncLiveGetMsaObjectCast:
    """
    T6b item 1 (the item Checkpoint 3b gates on): a DIRECT,
    mutation-resistant live test of __GetMsaObject's C2 cast.

    Cycle-10 mutation testing removed the cast (made __GetMsaObject
    return `obj` unconditionally) and all 6 pre-existing live tests in
    this file stayed green:
      - test_get_msa_object_casts_on_hvo_and_guid_path (Section A,
        TestMSASyncStatic) is a STATIC source-pattern check -- it reads
        the method's source text, so it cannot observe a removed cast
        at runtime at all.
      - test_hvo_and_guid_entry_paths_capture_feature_keys (below, in
        TestMSASyncLiveRoundTrip) goes through
        GetSyncableProperties -> _ResolveFeatureStrucOwner, which casts
        to the concrete interface INDEPENDENTLY of __GetMsaObject's own
        cast -- so it is insensitive to whether __GetMsaObject's cast
        exists.

    This class instead calls the private resolver DIRECTLY by its
    mangled name (bypassing GetSyncableProperties and
    _ResolveFeatureStrucOwner entirely) and reads a SUBTYPE-ONLY member
    straight off the returned object -- MsFeaturesOA / InflFeatsOA are
    declared on IMoStemMsa / IMoInflAffMsa respectively, and are NOT
    reachable on the bare ICmObject that self.project.Object(hvo_or_guid)
    returns. Without the cast, `.MsFeaturesOA` raises AttributeError;
    that is exactly the failure mode this class is designed to surface.
    Verified by mutation in a disposable git worktree (removing the
    cast) -- see specs/feature-structure-sync-gap/evidence/live-T6b.md
    for the exact failure message.
    """

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_hvo_and_guid_path_cast_to_concrete_stem_msa(self, live_msa_factory):
        sandbox, entry, new_sense, pos_obj = live_msa_factory
        stem = sandbox.MSA.CreateStem(new_sense(), pos_obj)
        hvo = stem.Hvo
        guid_str = str(stem.Guid)

        # BINDING (lead ruling 3): the PRE-cast bare object fetched via
        # sandbox.Object(hvo) must LACK the subtype-only member --
        # without this, the assertions below would only prove the cast
        # is harmless, never that it does anything (the exact claim
        # cycle 10 withdrew). If this assertion goes RED, STOP AND
        # REPORT rather than deleting it: it would mean the
        # 0-true/2088-false hasattr premise this whole campaign rests
        # on no longer holds.
        assert not hasattr(sandbox.Object(hvo), "MsFeaturesOA")

        result_hvo = sandbox.MSA._MSAOperations__GetMsaObject(hvo)
        assert result_hvo.ClassName == "MoStemMsa"
        # Direct read of a subtype-only member -- AttributeError here
        # (not merely a wrong value) is the cast-removed failure mode.
        assert result_hvo.MsFeaturesOA is None

        result_guid = sandbox.MSA._MSAOperations__GetMsaObject(guid_str)
        assert result_guid.ClassName == "MoStemMsa"
        assert result_guid.MsFeaturesOA is None

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_hvo_and_guid_path_cast_to_concrete_infl_aff_msa(
        self, live_msa_factory
    ):
        sandbox, entry, new_sense, pos_obj = live_msa_factory
        infl = sandbox.MSA.CreateInflAff(new_sense(), pos_obj)
        hvo = infl.Hvo
        guid_str = str(infl.Guid)

        assert not hasattr(sandbox.Object(hvo), "InflFeatsOA")

        result_hvo = sandbox.MSA._MSAOperations__GetMsaObject(hvo)
        assert result_hvo.ClassName == "MoInflAffMsa"
        assert result_hvo.InflFeatsOA is None

        result_guid = sandbox.MSA._MSAOperations__GetMsaObject(guid_str)
        assert result_guid.ClassName == "MoInflAffMsa"
        assert result_guid.InflFeatsOA is None


@pytest.mark.requires_live_project
class TestMSASyncLiveRoundTrip:
    """
    Real capture -> apply -> RE-READ round trips against a live
    target_sandbox, driven entirely through the public
    GetSyncableProperties/ApplySyncableProperties surface (the shared
    _ApplyFeatureStruc/_GetFeatureStruc algorithm itself is already
    covered live by test_apply_feature_struc.py -- T4). All read-back
    assertions re-fetch from a FRESH sandbox.Object(hvo) after the write,
    never from the reference held at write time.
    """

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_stem_msa_capture_apply_roundtrip(self, live_msa_factory):
        sandbox, entry, new_sense, pos_obj = live_msa_factory
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_msa251_stem_feat", "t2sf", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_msa251_stem_val", "t2sv")

        src_stem = sandbox.MSA.CreateStem(new_sense(), pos_obj)
        sandbox.MSA._ApplyFeatureStruc(
            src_stem, "MsFeaturesOA",
            [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
            on_unresolved="raise", label="TEST src stem",
        )

        src_bare = sandbox.Object(src_stem.Hvo)
        props = sandbox.MSA.GetSyncableProperties(src_bare)
        assert props["MsFeaturesGuid"]
        expected_specs = {str(feat.Guid): str(value.Guid)}
        assert props["MsFeatures"]["specs"] == expected_specs

        tgt_stem = sandbox.MSA.CreateStem(new_sense(), pos_obj)
        sandbox.MSA.ApplySyncableProperties(tgt_stem, props)

        tgt_bare = sandbox.Object(tgt_stem.Hvo)
        reread_props = sandbox.MSA.GetSyncableProperties(tgt_bare)
        assert reread_props["MsFeatures"]["specs"] == expected_specs

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_infl_aff_msa_capture_apply_roundtrip(self, live_msa_factory):
        sandbox, entry, new_sense, pos_obj = live_msa_factory
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_msa251_infl_feat", "t2if", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_msa251_infl_val", "t2iv")

        src_infl = sandbox.MSA.CreateInflAff(new_sense(), pos_obj)
        sandbox.MSA._ApplyFeatureStruc(
            src_infl, "InflFeatsOA",
            [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
            on_unresolved="raise", label="TEST src infl aff",
        )

        src_bare = sandbox.Object(src_infl.Hvo)
        props = sandbox.MSA.GetSyncableProperties(src_bare)
        expected_specs = {str(feat.Guid): str(value.Guid)}
        assert props["InflFeats"]["specs"] == expected_specs

        tgt_infl = sandbox.MSA.CreateInflAff(new_sense(), pos_obj)
        sandbox.MSA.ApplySyncableProperties(tgt_infl, props)

        tgt_bare = sandbox.Object(tgt_infl.Hvo)
        reread_props = sandbox.MSA.GetSyncableProperties(tgt_bare)
        assert reread_props["InflFeats"]["specs"] == expected_specs

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_deriv_aff_msa_both_slots_roundtrip(self, live_msa_factory):
        sandbox, entry, new_sense, pos_obj = live_msa_factory
        infl_ops = sandbox.InflectionFeatures

        from_feat = infl_ops.Create("TEST_msa251_from_feat", "t2ff", type="closed")
        from_value = infl_ops.CreateValue(from_feat, "TEST_msa251_from_val", "t2fv")
        to_feat = infl_ops.Create("TEST_msa251_to_feat", "t2tf", type="closed")
        to_value = infl_ops.CreateValue(to_feat, "TEST_msa251_to_val", "t2tv")

        src_deriv = sandbox.MSA.CreateDerivAff(
            new_sense(), from_pos=pos_obj, to_pos=pos_obj
        )
        sandbox.MSA._ApplyFeatureStruc(
            src_deriv, "FromMsFeaturesOA",
            [{"FeatureGuid": str(from_feat.Guid), "ValueGuid": str(from_value.Guid)}],
            on_unresolved="raise", label="TEST src deriv From",
        )
        sandbox.MSA._ApplyFeatureStruc(
            src_deriv, "ToMsFeaturesOA",
            [{"FeatureGuid": str(to_feat.Guid), "ValueGuid": str(to_value.Guid)}],
            on_unresolved="raise", label="TEST src deriv To",
        )

        src_bare = sandbox.Object(src_deriv.Hvo)
        props = sandbox.MSA.GetSyncableProperties(src_bare)
        assert props["FromMsFeatures"]["specs"] == {
            str(from_feat.Guid): str(from_value.Guid)
        }
        assert props["ToMsFeatures"]["specs"] == {
            str(to_feat.Guid): str(to_value.Guid)
        }

        tgt_deriv = sandbox.MSA.CreateDerivAff(
            new_sense(), from_pos=pos_obj, to_pos=pos_obj
        )
        sandbox.MSA.ApplySyncableProperties(tgt_deriv, props)

        tgt_bare = sandbox.Object(tgt_deriv.Hvo)
        reread_props = sandbox.MSA.GetSyncableProperties(tgt_bare)
        assert reread_props["FromMsFeatures"]["specs"] == {
            str(from_feat.Guid): str(from_value.Guid)
        }
        assert reread_props["ToMsFeatures"]["specs"] == {
            str(to_feat.Guid): str(to_value.Guid)
        }

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_unclassified_affix_msa_capture_and_apply_do_not_raise(
        self, live_msa_factory
    ):
        """
        R2, against a REAL MoUnclassifiedAffixMsa (not a fake).

        T6b item 5 scope note: like its offline sibling
        (TestMSASyncApplyUnclassifiedAffixNoRaise), this test's
        behavioural coverage cannot be made mutation-resistant --
        MoUnclassifiedAffixMsa is excluded from the if/elif dispatch
        regardless of whether the explicit early-return short-circuit
        is present, so this test stays green either way and cannot
        distinguish presence from absence of that short-circuit. The
        real lock is the two static AST tests in TestMSASyncStatic:
        test_unclassified_affix_discriminated_before_resolver_in_capture
        and ..._in_apply.
        """
        sandbox, entry, new_sense, pos_obj = live_msa_factory

        unclass = sandbox.MSA.CreateUnclassifiedAffix(new_sense(), pos_obj)

        props = sandbox.MSA.GetSyncableProperties(unclass)
        assert props == {}

        # Must not raise even when applied (with an empty props dict, the
        # realistic case since GetSyncableProperties never emits feature
        # keys for this ClassName).
        sandbox.MSA.ApplySyncableProperties(unclass, {})

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_apply_raises_on_unresolved_feature_guid(self, live_msa_factory):
        from flexicon.code.BaseOperations import FP_ParameterError

        sandbox, entry, new_sense, pos_obj = live_msa_factory
        stem = sandbox.MSA.CreateStem(new_sense(), pos_obj)

        bogus_feat_guid = "00000000-0000-0000-0000-0000000000aa"
        bogus_val_guid = "00000000-0000-0000-0000-0000000000bb"
        props = {
            "MsFeatures": {
                "TypeGuid": None,
                "specs": {bogus_feat_guid: bogus_val_guid},
            },
            "MsFeaturesGuid": "00000000-0000-0000-0000-0000000000cc",
        }

        with pytest.raises(FP_ParameterError, match=bogus_feat_guid):
            sandbox.MSA.ApplySyncableProperties(stem, props)

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_hvo_and_guid_entry_paths_capture_feature_keys(self, live_msa_factory):
        """
        C2: FLExProject.Object(hvo_or_guid) returns a bare ICmObject.
        GetSyncableProperties(hvo) and GetSyncableProperties(guid_str)
        must both still capture the feature-struct keys -- not just
        GetSyncableProperties(already-typed-object).
        """
        sandbox, entry, new_sense, pos_obj = live_msa_factory
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_msa251_hvo_feat", "t2hf", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_msa251_hvo_val", "t2hv")

        stem = sandbox.MSA.CreateStem(new_sense(), pos_obj)
        sandbox.MSA._ApplyFeatureStruc(
            stem, "MsFeaturesOA",
            [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
            on_unresolved="raise", label="TEST hvo-path stem",
        )

        hvo = stem.Hvo
        guid_str = str(stem.Guid)

        props_via_hvo = sandbox.MSA.GetSyncableProperties(hvo)
        props_via_guid = sandbox.MSA.GetSyncableProperties(guid_str)

        expected_specs = {str(feat.Guid): str(value.Guid)}
        assert props_via_hvo["MsFeatures"]["specs"] == expected_specs
        assert props_via_guid["MsFeatures"]["specs"] == expected_specs
