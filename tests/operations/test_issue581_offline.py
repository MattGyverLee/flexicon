#
#   test_issue581_offline.py
#
#   Offline coverage for issue #581:
#     - AllomorphOperations.GetInflectionClasses / AddInflectionClass /
#       RemoveInflectionClass (IMoStemAllomorph.InflectionClassesRC)
#     - AllomorphOperations.GetRequiredFeatures / SetRequiredFeatures
#       (IMoAffixAllomorph.MsEnvFeaturesOA round-trip contract)
#     - MSAOperations.GetOwningEntry (OwnerOfClass climb, None-not-raise)
#     - Shared.feature_struc_utils.c4_to_feat_struc_spec /
#       feat_struc_spec_to_c4 (pure conversion, both directions)
#
#   No live FieldWorks project required: the operations modules are loaded
#   in isolation with stubbed ``flexicon`` / ``SIL`` / ``clr`` modules (the
#   test_issue448 offline pattern), and the shared conversion helpers --
#   pure Python with no imports -- are loaded for real.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

import contextlib
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------------------
# Real exception types (mirrors flexicon.code.FLExProject surface used here)
# ----------------------------------------------------------------------

class FP_ParameterError(Exception):
    pass


class FP_NullParameterError(FP_ParameterError):
    pass


class FP_ReadOnlyError(Exception):
    pass


# ----------------------------------------------------------------------
# Fake LCM layer
# ----------------------------------------------------------------------

class FakeRC(list):
    """FDO reference-collection stand-in: Add/Remove/Count + `in` by Hvo."""

    def Add(self, item):
        if item not in self:
            self.append(item)

    def Remove(self, item):
        for i, member in enumerate(self):
            if member is item or getattr(member, "Hvo", None) == getattr(item, "Hvo", None):
                del self[i]
                return
        raise ValueError("item not in collection")

    @property
    def Count(self):
        return len(self)

    def __contains__(self, item):
        return any(
            member is item or getattr(member, "Hvo", None) == getattr(item, "Hvo", None)
            for member in self
        )


class FakeProject:
    def __init__(self):
        self.writeEnabled = True
        self._by_hvo = {}
        self._by_guid = {}

    def Object(self, hvo_or_guid):
        if isinstance(hvo_or_guid, int):
            return self._by_hvo[hvo_or_guid]
        return self._by_guid[str(hvo_or_guid).lower()]


class FakeBaseOperations:
    """Test seam replacing BaseOperations for the methods under test."""

    def __init__(self, project):
        self.project = project
        self.transaction_labels = []
        self.apply_calls = []
        self.canned_c4 = None
        self.fs_registry = {}
        self.resolve_owner_calls = []

    def _EnsureWriteEnabled(self):
        if not getattr(self.project, "writeEnabled", False):
            raise FP_ReadOnlyError("project is not write enabled")

    def _ValidateParam(self, param, param_name="parameter"):
        if param is None:
            raise FP_NullParameterError(f"{param_name} is None")
        if getattr(param, "IsValidObject", True) is False:
            raise FP_ParameterError(f"{param_name} is a stale object")

    @contextlib.contextmanager
    def _TransactionCM(self, label):
        self.transaction_labels.append(label)
        yield

    def _UnwrapLcm(self, x):
        return x

    def _UnwrapLcmObject(self, x):
        return x

    def _ResolveFeatureStrucOwner(self, owner, slot=None):
        self.resolve_owner_calls.append(owner)
        if getattr(owner, "ClassName", None) == "MoAffixAllomorph":
            return (owner, "MsEnvFeaturesOA")
        raise FP_ParameterError(
            f"unsupported feature-structure owner {getattr(owner, 'ClassName', None)}"
        )

    def _GetFeatureStruc(self, struct, _top_level=True):
        if struct is None:
            return None
        return self.canned_c4

    def _ResolveFsByGuid(self, guid, kind=None):
        return self.fs_registry.get(str(guid).lower())

    def _ApplyFeatureStruc(self, owner, prop_name, spec_dict, struct_guid=None,
                           on_unresolved="raise", label=None):
        # Replace semantics contract: the caller must have cleared the
        # existing struct before applying, so struct_guid is always honored.
        assert getattr(owner, prop_name) is None, (
            "SetRequiredFeatures must clear MsEnvFeaturesOA before applying"
        )
        self.apply_calls.append({
            "owner": owner,
            "prop_name": prop_name,
            "spec_dict": spec_dict,
            "struct_guid": struct_guid,
            "on_unresolved": on_unresolved,
            "label": label,
        })
        new_struct = SimpleNamespace(
            Guid=struct_guid or "minted-struct-guid",
            ClassName="FsFeatStruc",
        )
        setattr(owner, prop_name, new_struct)
        return new_struct


def _make_stem_allomorph(hvo=101, classes=()):
    return SimpleNamespace(
        ClassName="MoStemAllomorph",
        Hvo=hvo,
        InflectionClassesRC=FakeRC(classes),
    )


def _make_affix_allomorph(hvo=201, struct=None):
    return SimpleNamespace(
        ClassName="MoAffixAllomorph",
        Hvo=hvo,
        MsEnvFeaturesOA=struct,
    )


def _make_infl_class(hvo=901, name="Strong Verbs"):
    return SimpleNamespace(ClassName="MoInflClass", Hvo=hvo, Name=name)


def _make_msa(hvo=501, class_name="MoStemMsa", owner_result="no-owner"):
    msa = SimpleNamespace(ClassName=class_name, Hvo=hvo)
    msa.OwnerOfClass = lambda class_id: None if owner_result == "no-owner" else owner_result
    return msa


# ----------------------------------------------------------------------
# Isolated module loading (test_issue448 pattern)
# ----------------------------------------------------------------------

_STUB_PREFIXES = ("flexicon", "SIL", "System", "clr")


def _identity(obj):
    return obj


def _install_stubs():
    for name in ("flexicon", "flexicon.code", "flexicon.code.Lexicon",
                 "flexicon.code.Shared"):
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod

    # --- SIL.LCModel ---
    sil = types.ModuleType("SIL")
    sil.__path__ = []
    sys.modules["SIL"] = sil
    lcm = types.ModuleType("SIL.LCModel")
    sys.modules["SIL.LCModel"] = lcm
    for attr in (
        "IMoStemAllomorph", "IMoAffixAllomorph",
        "IMoStemAllomorphFactory", "IMoAffixAllomorphFactory",
        "ILexEntry", "ILexEntryRepository", "IPartOfSpeech",
        "IPhEnvironment", "PartOfSpeechTags",
        "IMoStemMsa", "IMoStemMsaFactory", "IMoDerivAffMsa",
        "IMoDerivAffMsaFactory", "IMoInflAffMsa", "IMoInflAffMsaFactory",
        "IMoUnclassifiedAffixMsa", "IMoUnclassifiedAffixMsaFactory",
        "ILexSense", "IWfiMorphBundleRepository", "MsaType",
        "SandboxGenericMSA",
    ):
        setattr(lcm, attr, _identity)
    lcm.LexEntryTags = SimpleNamespace(kClassId=1001)

    core = types.ModuleType("SIL.LCModel.Core")
    core.__path__ = []
    sys.modules["SIL.LCModel.Core"] = core
    ki = types.ModuleType("SIL.LCModel.Core.KernelInterfaces")
    ki.ITsString = _identity
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = ki
    txt = types.ModuleType("SIL.LCModel.Core.Text")
    txt.TsStringUtils = SimpleNamespace()
    sys.modules["SIL.LCModel.Core.Text"] = txt
    ds = types.ModuleType("SIL.LCModel.DomainServices")
    ds.SandboxGenericMSA = _identity
    sys.modules["SIL.LCModel.DomainServices"] = ds

    sys.modules["clr"] = types.ModuleType("clr")

    # --- flexicon.code.BaseOperations ---
    base_mod = types.ModuleType("flexicon.code.BaseOperations")
    base_mod.BaseOperations = FakeBaseOperations
    base_mod.OperationsMethod = lambda f: f
    base_mod.wrap_enumerable = lambda f: f
    sys.modules["flexicon.code.BaseOperations"] = base_mod

    # --- flexicon.code.FLExProject ---
    flex_mod = types.ModuleType("flexicon.code.FLExProject")
    flex_mod.FP_ParameterError = FP_ParameterError
    flex_mod.FP_NullParameterError = FP_NullParameterError
    flex_mod.FP_ReadOnlyError = FP_ReadOnlyError
    sys.modules["flexicon.code.FLExProject"] = flex_mod

    # --- Shared helpers ---
    su = types.ModuleType("flexicon.code.Shared.string_utils")
    su.normalize_text = lambda s: s or ""
    sys.modules["flexicon.code.Shared.string_utils"] = su
    mtu = types.ModuleType("flexicon.code.Shared.morph_type_utils")
    mtu.find_morph_type = lambda *a, **k: None
    mtu.is_stem_morph_type = lambda *a, **k: False
    mtu.morph_type_not_found_error = lambda *a, **k: FP_ParameterError("nope")
    sys.modules["flexicon.code.Shared.morph_type_utils"] = mtu
    lc = types.ModuleType("flexicon.code.lcm_casting")
    lc.cast_to_concrete = _identity
    lc.get_pos_from_msa = lambda *a, **k: None
    sys.modules["flexicon.code.lcm_casting"] = lc

    # --- Lexicon siblings ---
    allo_mod = types.ModuleType("flexicon.code.Lexicon.allomorph")
    allo_mod.Allomorph = type("Allomorph", (), {})
    sys.modules["flexicon.code.Lexicon.allomorph"] = allo_mod
    allo_coll = types.ModuleType("flexicon.code.Lexicon.allomorph_collection")
    allo_coll.AllomorphCollection = type("AllomorphCollection", (), {})
    sys.modules["flexicon.code.Lexicon.allomorph_collection"] = allo_coll
    msa_wrap = types.ModuleType("flexicon.code.Lexicon.morphosyntax_analysis")
    msa_wrap.MorphosyntaxAnalysis = type("MorphosyntaxAnalysis", (), {})
    sys.modules["flexicon.code.Lexicon.morphosyntax_analysis"] = msa_wrap
    msa_coll = types.ModuleType("flexicon.code.Lexicon.msa_collection")
    msa_coll.MSACollection = type("MSACollection", (), {})
    sys.modules["flexicon.code.Lexicon.msa_collection"] = msa_coll


def _load_real(modname, relpath):
    path = _REPO_ROOT / relpath
    spec = importlib.util.spec_from_file_location(modname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def _isolated():
    """Install stubs, load the REAL modules under test, then restore."""
    saved = dict(sys.modules)
    try:
        _install_stubs()
        utils = _load_real(
            "flexicon.code.Shared.feature_struc_utils",
            "flexicon/code/Shared/feature_struc_utils.py",
        )
        allo_ops_mod = _load_real(
            "flexicon.code.Lexicon.AllomorphOperations",
            "flexicon/code/Lexicon/AllomorphOperations.py",
        )
        msa_ops_mod = _load_real(
            "flexicon.code.Lexicon.MSAOperations",
            "flexicon/code/Lexicon/MSAOperations.py",
        )
        yield SimpleNamespace(
            utils=utils,
            AllomorphOperations=allo_ops_mod.AllomorphOperations,
            MSAOperations=msa_ops_mod.MSAOperations,
        )
    finally:
        for key in [k for k in sys.modules if k not in saved]:
            del sys.modules[key]
        for key, mod in saved.items():
            if sys.modules.get(key) is not mod:
                sys.modules[key] = mod


def _allomorph_ops(loaded):
    """Fresh (project, AllomorphOperations) pair for one test."""
    project = FakeProject()
    return project, loaded.AllomorphOperations(project)


# ----------------------------------------------------------------------
# Shared conversion helpers (real module, no stubs needed beyond loader)
# ----------------------------------------------------------------------

FEAT_NUMBER = "11111111-1111-1111-1111-111111111111"
VAL_SINGULAR = "22222222-2222-2222-2222-222222222222"
VAL_PLURAL = "33333333-3333-3333-3333-333333333333"
FEAT_AGREEMENT = "44444444-4444-4444-4444-444444444444"
FEAT_CLASS = "66666666-6666-6666-6666-666666666666"
VAL_CLASS_1 = "77777777-7777-7777-7777-777777777777"
STRUCT_GUID = "55555555-5555-5555-5555-555555555555"


def test_c4_to_spec_none():
    with _isolated() as loaded:
        assert loaded.utils.c4_to_feat_struc_spec(None) is None


def test_c4_to_spec_empty():
    with _isolated() as loaded:
        c4 = {"TypeGuid": None, "specs": {}}
        assert loaded.utils.c4_to_feat_struc_spec(c4) == {}


def test_c4_to_spec_recursive():
    with _isolated() as loaded:
        c4 = {
            "TypeGuid": None,
            "specs": {
                FEAT_NUMBER: VAL_SINGULAR,
                FEAT_AGREEMENT: {
                    "TypeGuid": "type-guid-here",
                    "Guid": "nested-struct-guid",
                    "specs": {FEAT_CLASS: VAL_CLASS_1},
                },
            },
        }
        assert loaded.utils.c4_to_feat_struc_spec(c4) == {
            FEAT_NUMBER: VAL_SINGULAR,
            FEAT_AGREEMENT: {FEAT_CLASS: VAL_CLASS_1},
        }


def test_spec_to_c4_envelope():
    with _isolated() as loaded:
        spec = {
            FEAT_NUMBER: VAL_SINGULAR,
            FEAT_AGREEMENT: {FEAT_CLASS: VAL_CLASS_1},
        }
        assert loaded.utils.feat_struc_spec_to_c4(spec) == {
            "TypeGuid": None,
            "specs": {
                FEAT_NUMBER: VAL_SINGULAR,
                FEAT_AGREEMENT: {
                    "TypeGuid": None,
                    "specs": {FEAT_CLASS: VAL_CLASS_1},
                },
            },
        }


def test_spec_c4_roundtrip():
    with _isolated() as loaded:
        spec = {
            FEAT_NUMBER: VAL_PLURAL,
            FEAT_AGREEMENT: {FEAT_CLASS: VAL_CLASS_1},
        }
        c4 = loaded.utils.feat_struc_spec_to_c4(spec)
        assert loaded.utils.c4_to_feat_struc_spec(c4) == spec


# ----------------------------------------------------------------------
# Inflection-class trio
# ----------------------------------------------------------------------

def test_get_infl_classes_stem():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        ic1, ic2 = _make_infl_class(901), _make_infl_class(902)
        allo = _make_stem_allomorph(classes=[ic1, ic2])
        result = ops.GetInflectionClasses(allo)
        assert result == [ic1, ic2]


def test_get_infl_classes_empty():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        assert ops.GetInflectionClasses(_make_stem_allomorph()) == []


def test_get_infl_classes_non_stem():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        # Affix allomorphs have no InflectionClassesRC: [] never raises.
        assert ops.GetInflectionClasses(_make_affix_allomorph()) == []


def test_get_infl_classes_null():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        try:
            ops.GetInflectionClasses(None)
        except FP_NullParameterError:
            pass
        else:
            raise AssertionError("expected FP_NullParameterError")


def test_get_infl_classes_hvo():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        ic = _make_infl_class(901)
        allo = _make_stem_allomorph(hvo=101, classes=[ic])
        project._by_hvo[101] = allo
        assert ops.GetInflectionClasses(101) == [ic]


def test_add_infl_class_object():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        allo = _make_stem_allomorph()
        ic = _make_infl_class(901)
        ops.AddInflectionClass(allo, ic)
        assert list(allo.InflectionClassesRC) == [ic]
        assert ops.transaction_labels == ["Add inflection class"]


def test_add_infl_class_hvo():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        allo = _make_stem_allomorph(hvo=101)
        ic = _make_infl_class(hvo=901)
        project._by_hvo[101] = allo
        project._by_hvo[901] = ic
        ops.AddInflectionClass(101, 901)
        assert list(allo.InflectionClassesRC) == [ic]


def test_add_infl_class_redundant_noop():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        ic = _make_infl_class(901)
        allo = _make_stem_allomorph(classes=[ic])
        ops.AddInflectionClass(allo, ic)
        assert list(allo.InflectionClassesRC) == [ic]
        assert ops.transaction_labels == [], "redundant add must not open an undo entry"


def test_add_infl_class_non_stem():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        try:
            ops.AddInflectionClass(_make_affix_allomorph(), _make_infl_class())
        except FP_ParameterError:
            pass
        else:
            raise AssertionError("expected FP_ParameterError for affix allomorph")


def test_add_infl_class_wrong_class():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        not_a_class = SimpleNamespace(ClassName="MoStemAllomorph", Hvo=999)
        try:
            ops.AddInflectionClass(_make_stem_allomorph(), not_a_class)
        except FP_ParameterError:
            pass
        else:
            raise AssertionError("expected FP_ParameterError for non-IMoInflClass")


def test_remove_infl_class():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        ic1, ic2 = _make_infl_class(901), _make_infl_class(902)
        allo = _make_stem_allomorph(classes=[ic1, ic2])
        ops.RemoveInflectionClass(allo, ic1)
        assert list(allo.InflectionClassesRC) == [ic2]
        assert ops.transaction_labels == ["Remove inflection class"]


def test_remove_infl_class_redundant_noop():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        allo = _make_stem_allomorph(classes=[_make_infl_class(901)])
        ops.RemoveInflectionClass(allo, _make_infl_class(902))
        assert len(allo.InflectionClassesRC) == 1
        assert ops.transaction_labels == [], "redundant remove must not open an undo entry"


def test_remove_infl_class_non_stem():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        try:
            ops.RemoveInflectionClass(_make_affix_allomorph(), _make_infl_class())
        except FP_ParameterError:
            pass
        else:
            raise AssertionError("expected FP_ParameterError for affix allomorph")


# ----------------------------------------------------------------------
# GetRequiredFeatures
# ----------------------------------------------------------------------

def test_get_required_features_unset():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        allo = _make_affix_allomorph(struct=None)
        assert ops.GetRequiredFeatures(allo) is None
        # _GetFeatureStruc(None) -> None -> converter passthrough, no owner read.
        assert ops.resolve_owner_calls == [allo]


def test_get_required_features_empty():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        struct = SimpleNamespace(Guid="s", ClassName="FsFeatStruc")
        ops.canned_c4 = {"TypeGuid": None, "specs": {}}
        assert ops.GetRequiredFeatures(_make_affix_allomorph(struct=struct)) == {}


def test_get_required_features_recursive():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        struct = SimpleNamespace(Guid="s", ClassName="FsFeatStruc")
        ops.canned_c4 = {
            "TypeGuid": None,
            "specs": {
                FEAT_NUMBER: VAL_SINGULAR,
                FEAT_AGREEMENT: {
                    "TypeGuid": "t",
                    "Guid": "nested-guid",
                    "specs": {FEAT_CLASS: VAL_CLASS_1},
                },
            },
        }
        assert ops.GetRequiredFeatures(_make_affix_allomorph(struct=struct)) == {
            FEAT_NUMBER: VAL_SINGULAR,
            FEAT_AGREEMENT: {FEAT_CLASS: VAL_CLASS_1},
        }


def test_get_required_features_wrong_type():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        # Stem allomorph: None, never raises, owner never resolved.
        assert ops.GetRequiredFeatures(_make_stem_allomorph()) is None
        assert ops.resolve_owner_calls == []


def test_get_required_features_null():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        try:
            ops.GetRequiredFeatures(None)
        except FP_NullParameterError:
            pass
        else:
            raise AssertionError("expected FP_NullParameterError")


# ----------------------------------------------------------------------
# SetRequiredFeatures
# ----------------------------------------------------------------------

def _register_fs(ops):
    ops.fs_registry = {
        FEAT_NUMBER.lower(): SimpleNamespace(Guid=FEAT_NUMBER),
        VAL_SINGULAR.lower(): SimpleNamespace(Guid=VAL_SINGULAR),
        VAL_PLURAL.lower(): SimpleNamespace(Guid=VAL_PLURAL),
        FEAT_AGREEMENT.lower(): SimpleNamespace(Guid=FEAT_AGREEMENT),
        FEAT_CLASS.lower(): SimpleNamespace(Guid=FEAT_CLASS),
        VAL_CLASS_1.lower(): SimpleNamespace(Guid=VAL_CLASS_1),
    }


def test_set_required_features_roundtrip():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        _register_fs(ops)
        old_struct = SimpleNamespace(Guid="old-guid", ClassName="FsFeatStruc")
        allo = _make_affix_allomorph(struct=old_struct)
        spec = {
            FEAT_NUMBER: VAL_PLURAL,
            FEAT_AGREEMENT: {FEAT_CLASS: VAL_CLASS_1},
        }
        ops.SetRequiredFeatures(allo, spec, struct_guid=STRUCT_GUID)

        assert len(ops.apply_calls) == 1
        call = ops.apply_calls[0]
        # Public spec re-enveloped into the C4 shape _ApplyFeatureStruc expects.
        assert call["spec_dict"] == {
            "TypeGuid": None,
            "specs": {
                FEAT_NUMBER: VAL_PLURAL,
                FEAT_AGREEMENT: {
                    "TypeGuid": None,
                    "specs": {FEAT_CLASS: VAL_CLASS_1},
                },
            },
        }
        assert call["struct_guid"] == STRUCT_GUID
        assert call["on_unresolved"] == "raise"
        assert call["prop_name"] == "MsEnvFeaturesOA"
        # Replace semantics: the new struct carries the requested GUID.
        assert allo.MsEnvFeaturesOA.Guid == STRUCT_GUID
        assert ops.transaction_labels[0] == "Set required features"


def test_set_required_features_empty_clears():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        _register_fs(ops)
        old_struct = SimpleNamespace(Guid="old-guid", ClassName="FsFeatStruc")
        allo = _make_affix_allomorph(struct=old_struct)
        ops.SetRequiredFeatures(allo, {})
        call = ops.apply_calls[0]
        assert call["spec_dict"] == {"TypeGuid": None, "specs": {}}
        assert call["struct_guid"] is None


def test_set_required_features_non_affix():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        try:
            ops.SetRequiredFeatures(_make_stem_allomorph(), {FEAT_NUMBER: VAL_SINGULAR})
        except FP_ParameterError:
            pass
        else:
            raise AssertionError("expected FP_ParameterError for stem allomorph")
        assert ops.apply_calls == []
        assert ops.transaction_labels == []


def test_set_required_features_bad_shapes():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        _register_fs(ops)
        allo = _make_affix_allomorph()
        bad_specs = [
            "not-a-dict",
            [("a", "b")],
            {123: VAL_SINGULAR},          # non-string key
            {FEAT_NUMBER: 123},           # non-string, non-dict value
        ]
        for bad in bad_specs:
            try:
                ops.SetRequiredFeatures(allo, bad)
            except FP_ParameterError:
                pass
            else:
                raise AssertionError(f"expected FP_ParameterError for {bad!r}")
        try:
            ops.SetRequiredFeatures(allo, None)
        except FP_NullParameterError:
            pass
        else:
            raise AssertionError("expected FP_NullParameterError for None spec")
        try:
            ops.SetRequiredFeatures(allo, {FEAT_NUMBER: VAL_SINGULAR}, struct_guid=123)
        except FP_ParameterError:
            pass
        else:
            raise AssertionError("expected FP_ParameterError for non-string struct_guid")
        assert ops.apply_calls == []
        assert ops.transaction_labels == []
        assert allo.MsEnvFeaturesOA is None


def test_set_required_features_unresolved_guid():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        _register_fs(ops)
        old_struct = SimpleNamespace(Guid="old-guid", ClassName="FsFeatStruc")
        allo = _make_affix_allomorph(struct=old_struct)
        unknown = "99999999-9999-9999-9999-999999999999"
        try:
            ops.SetRequiredFeatures(allo, {FEAT_NUMBER: unknown})
        except FP_ParameterError as exc:
            assert unknown in str(exc)
        else:
            raise AssertionError("expected FP_ParameterError for unknown value GUID")
        # Validate-before-mutate: nothing touched.
        assert ops.apply_calls == []
        assert ops.transaction_labels == []
        assert allo.MsEnvFeaturesOA is old_struct


def test_set_required_features_unresolved_nested():
    with _isolated() as loaded:
        project, ops = _allomorph_ops(loaded)
        _register_fs(ops)
        allo = _make_affix_allomorph()
        unknown_feat = "88888888-8888-8888-8888-888888888888"
        try:
            ops.SetRequiredFeatures(
                allo, {FEAT_AGREEMENT: {unknown_feat: VAL_CLASS_1}}
            )
        except FP_ParameterError as exc:
            assert unknown_feat in str(exc)
        else:
            raise AssertionError("expected FP_ParameterError for unknown nested feature")
        assert ops.apply_calls == []


# ----------------------------------------------------------------------
# MSAOperations.GetOwningEntry
# ----------------------------------------------------------------------

def _msa_ops(loaded):
    """Fresh (project, MSAOperations) pair for one test."""
    project = FakeProject()
    return project, loaded.MSAOperations(project)


def test_msa_get_owning_entry_found():
    with _isolated() as loaded:
        project, ops = _msa_ops(loaded)
        entry = SimpleNamespace(ClassName="LexEntry", Hvo=301)
        msa = _make_msa(owner_result=entry)
        assert ops.GetOwningEntry(msa) is entry


def test_msa_get_owning_entry_none():
    with _isolated() as loaded:
        project, ops = _msa_ops(loaded)
        # No owning entry anywhere up the chain: None, never raises.
        assert ops.GetOwningEntry(_make_msa(owner_result="no-owner")) is None


def test_msa_get_owning_entry_hvo():
    with _isolated() as loaded:
        project, ops = _msa_ops(loaded)
        entry = SimpleNamespace(ClassName="LexEntry", Hvo=301)
        msa = _make_msa(hvo=501, owner_result=entry)
        project._by_hvo[501] = msa
        assert ops.GetOwningEntry(501) is entry


def test_msa_get_owning_entry_guid():
    with _isolated() as loaded:
        project, ops = _msa_ops(loaded)
        guid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        entry = SimpleNamespace(ClassName="LexEntry", Hvo=301)
        msa = _make_msa(owner_result=entry)
        project._by_guid[guid] = msa
        assert ops.GetOwningEntry(guid) is entry


def test_msa_get_owning_entry_null():
    with _isolated() as loaded:
        project, ops = _msa_ops(loaded)
        try:
            ops.GetOwningEntry(None)
        except FP_NullParameterError:
            pass
        else:
            raise AssertionError("expected FP_NullParameterError")
