#
#   test_issue251_252_256_feature_struct_probe.py
#
#   READ-ONLY / SANDBOX-ONLY live LCM probe establishing ground truth for
#   the 3-issue cluster before any code is written:
#     #251 MSAOperations has no Get/ApplySyncableProperties
#     #252 POSOperations.GetSyncableProperties never captures
#          IPartOfSpeech.DefaultFeaturesOA / InherFeatValOA
#     #256 InflectionFeatureOperations.MakeFeatStruc hard-codes
#          owner.FeaturesOA and cannot express nesting
#
#   Never writes to the real Target project. Read-only probes run
#   against "Ngoreme FLEx" (writeEnabled=False); write-path probes run
#   only against target_sandbox (tempdir copy of the Target .fwbackup).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest

pytestmark = pytest.mark.requires_live_project

_NGOREME_PROJECT_NAME = "Ngoreme FLEx"


@pytest.fixture(scope="module")
def ngoreme_readonly():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception as exc:
        pytest.skip(f"Could not import FLExProject: {exc}")

    project = FLExProject()
    try:
        project.OpenProject(_NGOREME_PROJECT_NAME, writeEnabled=False)
    except Exception as exc:
        pytest.skip(f"Could not open {_NGOREME_PROJECT_NAME!r} read-only: {exc}")

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Item 1 + 2: hasattr under base-interface view (a) vs factory-fresh (b),
# and the wrong-cast failure mode.
# ---------------------------------------------------------------------------

@pytest.mark.live_phase("MSAOperations", "read")
def test_item1_2_msa_hasattr_base_vs_concrete_and_wrong_cast(
    ngoreme_readonly, target_sandbox, capsys
):
    from SIL.LCModel import (
        ILexEntryRepository,
        IMoStemMsa,
        IMoInflAffMsa,
        IMoDerivAffMsa,
    )

    print("\n[ITEM 1] === base-interface view (a): Ngoreme FLEx, via "
          "entry.MorphoSyntaxAnalysesOC (NOT explicitly cast) ===")

    project = ngoreme_readonly
    entries = list(project.ObjectsIn(ILexEntryRepository))

    counts = {}
    hasattr_results = {}
    for entry in entries:
        for msa in entry.MorphoSyntaxAnalysesOC:
            cn = msa.ClassName
            counts[cn] = counts.get(cn, 0) + 1
            if cn == "MoStemMsa":
                key = ("MoStemMsa", "MsFeaturesOA")
                hasattr_results.setdefault(key, []).append(
                    hasattr(msa, "MsFeaturesOA")
                )
            elif cn == "MoInflAffMsa":
                key = ("MoInflAffMsa", "InflFeatsOA")
                hasattr_results.setdefault(key, []).append(
                    hasattr(msa, "InflFeatsOA")
                )
            elif cn == "MoDerivAffMsa":
                for prop in ("FromMsFeaturesOA", "ToMsFeaturesOA"):
                    key = ("MoDerivAffMsa", prop)
                    hasattr_results.setdefault(key, []).append(
                        hasattr(msa, prop)
                    )

    print(f"[ITEM 1] MSA ClassName counts in Ngoreme FLEx: {counts}")
    for key, results in hasattr_results.items():
        n_true = sum(1 for r in results if r)
        n_false = sum(1 for r in results if not r)
        print(f"[ITEM 1] (a) hasattr{key}: True={n_true} False={n_false} total={len(results)}")

    print("\n[ITEM 1] === factory-fresh concrete-typed view (b): target_sandbox ===")

    sandbox = target_sandbox
    entries_ops = sandbox.LexEntry
    created_entry = entries_ops.Create(lexeme_form="TEST_probe1949")
    try:
        sense = list(created_entry.SensesOS)
        if not sense:
            from SIL.LCModel import ILexSenseFactory
            factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
            new_sense = factory.Create()
            created_entry.SensesOS.Add(new_sense)
            sense = [new_sense]
        sense_obj = sense[0]

        pos_list = list(sandbox.POS.GetAll())
        pos_obj = pos_list[0] if pos_list else None

        stem = sandbox.MSA.CreateStem(sense_obj, pos_obj)
        print(f"[ITEM 1] (b) IMoStemMsa.ClassName={stem.ClassName!r} hasattr(stem, MsFeaturesOA)={hasattr(stem, 'MsFeaturesOA')}")
        assert stem.ClassName == "MoStemMsa"

        base_view = sense_obj.MorphoSyntaxAnalysisRA
        print(f"[ITEM 1] (b prime) re-fetched via sense.MorphoSyntaxAnalysisRA (base view): ClassName={base_view.ClassName!r} hasattr={hasattr(base_view, 'MsFeaturesOA')}")

        via_cast = IMoStemMsa(base_view).MsFeaturesOA
        print(f"[ITEM 2] IMoStemMsa(base_view).MsFeaturesOA = {via_cast!r} (cast route works)")

        try:
            wrong = IMoInflAffMsa(stem)
            wrong_result = f"NO EXCEPTION RAISED at cast, returned {wrong!r}"
            try:
                access = wrong.InflFeatsOA
                wrong_result += f"; .InflFeatsOA access = {access!r}"
            except Exception as inner_exc:
                wrong_result = f"cast OK, access raised {type(inner_exc).__name__}: {inner_exc}"
        except Exception as exc:
            wrong_result = f"cast raised {type(exc).__name__}: {exc}"
        print(f"[ITEM 2] WRONG cast IMoInflAffMsa(a_stem_msa) result: {wrong_result}")
    finally:
        entries_ops.Delete(created_entry)


# ---------------------------------------------------------------------------
# Item 3: IPartOfSpeech.DefaultFeaturesOA / InherFeatValOA existence + type,
# and whether POSOperations.GetAll() already returns concrete-typed POS.
# ---------------------------------------------------------------------------

@pytest.mark.live_phase("POSOperations", "read")
def test_item3_pos_defaultfeatures_inherfeatval(ngoreme_readonly, capsys):
    from SIL.LCModel import IPartOfSpeech
    import clr

    project = ngoreme_readonly
    pos_list = list(project.POS.GetAll())
    print(f"\n[ITEM 3] Total POS in Ngoreme FLEx: {len(pos_list)}")

    n_default_feat = 0
    n_inher_feat_val = 0
    n_hasattr_default = 0
    n_hasattr_inher = 0
    for pos in pos_list:
        if hasattr(pos, "DefaultFeaturesOA"):
            n_hasattr_default += 1
            if pos.DefaultFeaturesOA is not None:
                n_default_feat += 1
        if hasattr(pos, "InherFeatValOA"):
            n_hasattr_inher += 1
            if pos.InherFeatValOA is not None:
                n_inher_feat_val += 1

    print(f"[ITEM 3] hasattr(pos, DefaultFeaturesOA) True for {n_hasattr_default}/{len(pos_list)}; non-null for {n_default_feat}/{len(pos_list)}")
    print(f"[ITEM 3] hasattr(pos, InherFeatValOA) True for {n_hasattr_inher}/{len(pos_list)}; non-null for {n_inher_feat_val}/{len(pos_list)}")

    net_type = clr.GetClrType(IPartOfSpeech)
    default_prop = net_type.GetProperty("DefaultFeaturesOA")
    inher_prop = net_type.GetProperty("InherFeatValOA")
    default_type_str = str(default_prop.PropertyType) if default_prop else "NOT FOUND"
    inher_type_str = str(inher_prop.PropertyType) if inher_prop else "NOT FOUND"
    print(f"[ITEM 3] IPartOfSpeech.DefaultFeaturesOA declared CLR type: {default_type_str}")
    print(f"[ITEM 3] IPartOfSpeech.InherFeatValOA declared CLR type: {inher_type_str}")

    is_instance = isinstance(pos_list[0], IPartOfSpeech)
    print(f"[ITEM 3] pos_list[0] python type: {type(pos_list[0])}; isinstance(pos_list[0], IPartOfSpeech) == {is_instance}")


# ---------------------------------------------------------------------------
# Item 4: adjacent MSA-family candidates -- existence + type of relevant
# properties.
# ---------------------------------------------------------------------------

def test_item4_adjacent_msa_candidates_existence(capsys):
    pytest.importorskip("SIL.LCModel")
    import clr
    import SIL.LCModel as lcm

    report = {}

    def _probe(iface_name, props):
        iface = getattr(lcm, iface_name, None)
        if iface is None:
            report[iface_name] = "IMPORT FAILED: attribute not found on SIL.LCModel"
            return
        net_type = clr.GetClrType(iface)
        prop_types = {}
        for prop in props:
            p = net_type.GetProperty(prop)
            prop_types[prop] = str(p.PropertyType) if p else "PROPERTY NOT FOUND"
        report[iface_name] = prop_types

    _probe("IMoDerivStepMsa", ["MsFeaturesOA", "InflFeatsOA"])
    _probe("IMoUnclassifiedAffixMsa", ["MsFeaturesOA", "InflFeatsOA"])
    _probe("IMoAffixAllomorph", ["MsEnvFeaturesOA"])
    _probe("ILexEntryInflType", ["InflFeatsOA"])

    print("\n[ITEM 4] Adjacent MSA-family candidate probe:")
    for iface_name, result in report.items():
        print(f"[ITEM 4] {iface_name}: {result}")


# ---------------------------------------------------------------------------
# Item 5 + 6: nested shape + counts in Ngoreme FLEx.
# ---------------------------------------------------------------------------

@pytest.mark.live_phase("InflectionFeatureOperations", "read")
def test_item5_6_nested_shape_and_counts_ngoreme(ngoreme_readonly, capsys):
    from SIL.LCModel import (
        ILexEntryRepository,
        IFsComplexValue,
        IFsClosedValue,
        IFsFeatStruc,
        IMoStemMsa,
        IMoInflAffMsa,
        IMoDerivAffMsa,
    )

    project = ngoreme_readonly

    def _classify_spec(spec):
        try:
            cv = IFsComplexValue(spec)
            if cv.ClassName == "FsComplexValue":
                return "complex", cv
        except Exception:
            pass
        try:
            clv = IFsClosedValue(spec)
            if clv.ClassName == "FsClosedValue":
                return "closed", clv
        except Exception:
            pass
        return "unknown", spec

    def _dump_featstruc(fs, depth, out):
        indent = "  " * depth
        # Item 5 finding: a nested struct reached via
        # IFsComplexValue.ValueOA comes back typed as the BASE
        # IFsAbstractStructure (hasattr(fs, "TypeRA") is False) -- the
        # exact same pythonnet static-wrapper-type pattern documented for
        # MSAs (item 1/2), just one level deeper. Must cast explicitly.
        out.append(f"{indent}[probe] hasattr(raw_value_from_ValueOA, 'TypeRA') BEFORE cast = {hasattr(fs, 'TypeRA')}")
        fs = IFsFeatStruc(fs)
        type_ra = fs.TypeRA
        try:
            long_name = fs.LongName
        except Exception as exc:
            long_name = f"EXC:{exc}"
        type_ra_str = "NULL" if type_ra is None else str(type_ra)
        out.append(f"{indent}IFsFeatStruc Guid={fs.Guid} TypeRA={type_ra_str} LongName={long_name!r} FeatureSpecsOC.Count={fs.FeatureSpecsOC.Count}")
        for spec in fs.FeatureSpecsOC:
            kind, concrete = _classify_spec(spec)
            if kind == "complex":
                try:
                    feat_name = concrete.FeatureRA.Name.BestAnalysisAlternative.Text if concrete.FeatureRA else None
                except Exception as exc:
                    feat_name = f"EXC:{exc}"
                out.append(f"{indent}  IFsComplexValue FeatureRA.Name={feat_name!r} Guid={concrete.Guid}")
                if concrete.ValueOA is not None:
                    _dump_featstruc(concrete.ValueOA, depth + 2, out)
                else:
                    out.append(f"{indent}    ValueOA=NULL")
            elif kind == "closed":
                try:
                    feat_name = concrete.FeatureRA.Name.BestAnalysisAlternative.Text if concrete.FeatureRA else None
                except Exception as exc:
                    feat_name = f"EXC:{exc}"
                try:
                    val_name = concrete.ValueRA.Name.BestAnalysisAlternative.Text if concrete.ValueRA else None
                except Exception as exc:
                    val_name = f"EXC:{exc}"
                out.append(f"{indent}  IFsClosedValue Guid={concrete.Guid} FeatureRA.Name={feat_name!r} ValueRA.Name={val_name!r}")
            else:
                out.append(f"{indent}  UNKNOWN spec ClassName={spec.ClassName}")
        return out

    entries = list(project.ObjectsIn(ILexEntryRepository))
    msa_counts = {"MoStemMsa": 0, "MoInflAffMsa": 0, "MoDerivAffMsa": 0}
    msa_nonnull_feats = {"MoStemMsa": 0, "MoInflAffMsa": 0, "MoDerivAffMsa": 0}
    all_featstrucs_seen = []

    for entry in entries:
        for msa in entry.MorphoSyntaxAnalysesOC:
            cn = msa.ClassName
            if cn == "MoStemMsa":
                msa_counts["MoStemMsa"] += 1
                concrete = IMoStemMsa(msa)
                if concrete.MsFeaturesOA is not None:
                    msa_nonnull_feats["MoStemMsa"] += 1
                    all_featstrucs_seen.append(("MoStemMsa", concrete.MsFeaturesOA))
            elif cn == "MoInflAffMsa":
                msa_counts["MoInflAffMsa"] += 1
                concrete = IMoInflAffMsa(msa)
                if concrete.InflFeatsOA is not None:
                    msa_nonnull_feats["MoInflAffMsa"] += 1
                    all_featstrucs_seen.append(("MoInflAffMsa", concrete.InflFeatsOA))
            elif cn == "MoDerivAffMsa":
                msa_counts["MoDerivAffMsa"] += 1
                concrete = IMoDerivAffMsa(msa)
                had_any = False
                if concrete.FromMsFeaturesOA is not None:
                    had_any = True
                    all_featstrucs_seen.append(("MoDerivAffMsa.From", concrete.FromMsFeaturesOA))
                if concrete.ToMsFeaturesOA is not None:
                    had_any = True
                    all_featstrucs_seen.append(("MoDerivAffMsa.To", concrete.ToMsFeaturesOA))
                if had_any:
                    msa_nonnull_feats["MoDerivAffMsa"] += 1

    print(f"\n[ITEM 6] MSA counts in Ngoreme FLEx: {msa_counts}")
    print(f"[ITEM 6] MSA counts with non-null feature structure: {msa_nonnull_feats}")
    print(f"[ITEM 6] Total MSAs: {sum(msa_counts.values())}")

    pos_list = list(project.POS.GetAll())
    n_pos_default = sum(1 for p in pos_list if p.DefaultFeaturesOA is not None)
    n_pos_inher = sum(1 for p in pos_list if p.InherFeatValOA is not None)
    print(f"[ITEM 6] POS count: {len(pos_list)}; with non-null DefaultFeaturesOA: {n_pos_default}; with non-null InherFeatValOA: {n_pos_inher}")

    n_nested = 0
    n_flat = 0
    for owner_desc, fs in all_featstrucs_seen:
        is_nested = False
        for spec in fs.FeatureSpecsOC:
            kind, _ = _classify_spec(spec)
            if kind == "complex":
                is_nested = True
                break
        if is_nested:
            n_nested += 1
        else:
            n_flat += 1
    print(f"[ITEM 6] Of {len(all_featstrucs_seen)} non-null MSA feature structs: nested(contains IFsComplexValue)={n_nested} flat={n_flat}")

    nested_example = None
    for owner_desc, fs in all_featstrucs_seen:
        for spec in fs.FeatureSpecsOC:
            kind, _ = _classify_spec(spec)
            if kind == "complex":
                nested_example = (owner_desc, fs)
                break
        if nested_example:
            break

    print("\n[ITEM 5] Nested feature structure example:")
    if nested_example is None:
        print("[ITEM 5] NO nested (IFsComplexValue-containing) feature structure found among MSA feature structs in Ngoreme FLEx.")
    else:
        owner_desc, fs = nested_example
        print(f"[ITEM 5] owner={owner_desc}")
        lines = []
        _dump_featstruc(fs, 0, lines)
        for line in lines:
            print(f"[ITEM 5] {line}")


# ---------------------------------------------------------------------------
# Item 7: reproduce #256 -- MakeFeatStruc with owner=<an MSA> in
# target_sandbox.
# ---------------------------------------------------------------------------

@pytest.mark.live_phase("InflectionFeatureOperations", "modify")
def test_item7_reproduce_256_makefeatstruc_on_msa_owner(target_sandbox, capsys):
    sandbox = target_sandbox

    created_entry = sandbox.LexEntry.Create(lexeme_form="TEST_probe256")
    try:
        sense = list(created_entry.SensesOS)
        if not sense:
            from SIL.LCModel import ILexSenseFactory
            factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
            new_sense = factory.Create()
            created_entry.SensesOS.Add(new_sense)
            sense = [new_sense]
        sense_obj = sense[0]

        pos_list = list(sandbox.POS.GetAll())
        pos_obj = pos_list[0] if pos_list else None

        stem = sandbox.MSA.CreateStem(sense_obj, pos_obj)
        print(f"\n[ITEM 7] Created IMoStemMsa ClassName={stem.ClassName!r}")
        print(f"[ITEM 7] hasattr(stem, FeaturesOA) = {hasattr(stem, 'FeaturesOA')}")
        print(f"[ITEM 7] hasattr(stem, MsFeaturesOA) = {hasattr(stem, 'MsFeaturesOA')}")

        infl_ops = sandbox.InflectionFeatures

        raised_empty = None
        try:
            result = infl_ops.MakeFeatStruc([], owner=stem)
            raised_empty = f"NO EXCEPTION -- returned {result!r}"
        except Exception as exc:
            raised_empty = f"{type(exc).__name__}: {exc}"
        print(f"[ITEM 7] MakeFeatStruc([], owner=stem) result: {raised_empty}")
    finally:
        sandbox.LexEntry.Delete(created_entry)


# ---------------------------------------------------------------------------
# Item 8: does IFsFeatStrucFactory / IFsComplexValueFactory /
# IFsClosedValueFactory expose a Create(Guid) overload?
# ---------------------------------------------------------------------------

def test_item8_factory_create_guid_overloads(capsys):
    pytest.importorskip("SIL.LCModel")
    import clr
    from SIL.LCModel import (
        IFsFeatStrucFactory,
        IFsComplexValueFactory,
        IFsClosedValueFactory,
    )

    def _describe_create_overloads(iface):
        """
        Walk the interface's OWN GetMethods() plus every interface it
        implements (net_type.GetInterfaces()). .NET reflection's
        Type.GetMethods() on an INTERFACE type returns only members
        DECLARED directly on that interface, not members inherited from
        base interfaces it extends -- unlike classes, where GetMethods()
        already flattens the hierarchy. LCM's factory interfaces (e.g.
        IFsFeatStrucFactory) declare no members of their own; Create()/
        Create(Guid) live on the generic base ILcmFactory<T> they extend.
        A naive net_type.GetMethods() on the factory interface itself
        therefore returns an empty list and wrongly suggests no Create
        overload exists at all -- this walks GetInterfaces() too so the
        inherited overloads are actually seen.
        """
        net_type = clr.GetClrType(iface)
        types_to_scan = [net_type] + list(net_type.GetInterfaces())
        descs = []
        for t in types_to_scan:
            for m in t.GetMethods():
                if m.Name == "Create":
                    param_types = [str(p.ParameterType) for p in m.GetParameters()]
                    descs.append(f"{t}.Create({', '.join(param_types)})")
        return descs

    for iface_name, iface in (
        ("IFsFeatStrucFactory", IFsFeatStrucFactory),
        ("IFsComplexValueFactory", IFsComplexValueFactory),
        ("IFsClosedValueFactory", IFsClosedValueFactory),
    ):
        net_type = clr.GetClrType(iface)
        direct_only = [m.Name for m in net_type.GetMethods() if m.Name == "Create"]
        overloads = _describe_create_overloads(iface)
        has_guid_overload = any("Guid" in o for o in overloads)
        print()
        print(f"[ITEM 8] {iface_name} direct-only GetMethods() Create hits (misleading if empty): {direct_only}")
        print(f"[ITEM 8] {iface_name} Create overloads (incl. inherited via GetInterfaces()): {overloads}")
        print(f"[ITEM 8] {iface_name} has a Guid-accepting Create overload: {has_guid_overload}")


# ---------------------------------------------------------------------------
# Item 9: ownership-first rule -- populate FeatureSpecsOC on a
# free-floating (unattached) IFsFeatStruc must fail; attached-first must
# succeed. target_sandbox only.
# ---------------------------------------------------------------------------

@pytest.mark.live_phase("InflectionFeatureOperations", "modify")
def test_item9_ownership_first_rule(target_sandbox, capsys):
    from SIL.LCModel import (
        IFsFeatStrucFactory,
        IFsClosedValueFactory,
    )

    sandbox = target_sandbox

    with sandbox._TransactionCM("probe item9 free-floating"):
        fs_factory = sandbox.project.ServiceLocator.GetService(IFsFeatStrucFactory)
        free_struct = fs_factory.Create()

        cv_factory = sandbox.project.ServiceLocator.GetService(IFsClosedValueFactory)
        closed_value = cv_factory.Create()

        try:
            free_struct.FeatureSpecsOC.Add(closed_value)
            free_floating_result = "NO EXCEPTION -- Add succeeded on free-floating struct"
        except Exception as exc:
            free_floating_result = f"{type(exc).__name__}: {exc}"

    print(f"\n[ITEM 9] Free-floating (unattached) IFsFeatStruc.FeatureSpecsOC.Add(...) result: {free_floating_result}")

    created_entry = sandbox.LexEntry.Create(lexeme_form="TEST_probe9")
    try:
        sense = list(created_entry.SensesOS)
        if not sense:
            from SIL.LCModel import ILexSenseFactory
            factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
            new_sense = factory.Create()
            created_entry.SensesOS.Add(new_sense)
            sense = [new_sense]
        sense_obj = sense[0]

        pos_list = list(sandbox.POS.GetAll())
        pos_obj = pos_list[0] if pos_list else None
        stem = sandbox.MSA.CreateStem(sense_obj, pos_obj)

        with sandbox._TransactionCM("probe item9 attached-first"):
            fs_factory2 = sandbox.project.ServiceLocator.GetService(IFsFeatStrucFactory)
            attached_struct = fs_factory2.Create()
            stem.MsFeaturesOA = attached_struct
            attached_struct = stem.MsFeaturesOA

            cv_factory2 = sandbox.project.ServiceLocator.GetService(IFsClosedValueFactory)
            closed_value2 = cv_factory2.Create()
            try:
                attached_struct.FeatureSpecsOC.Add(closed_value2)
                attached_result = f"SUCCESS -- FeatureSpecsOC.Count={attached_struct.FeatureSpecsOC.Count}"
            except Exception as exc:
                attached_result = f"{type(exc).__name__}: {exc}"

        print(f"[ITEM 9] Attached-first (owner.MsFeaturesOA = struct, THEN populate) result: {attached_result}")
    finally:
        sandbox.LexEntry.Delete(created_entry)


# ---------------------------------------------------------------------------
# Item 8b: functional confirmation -- BaseOperations._CreateWithGuid
# actually round-trips a caller-supplied GUID through IFsFeatStrucFactory,
# in target_sandbox (attached immediately to an MSA to satisfy the
# ownership-first rule, item 9).
# ---------------------------------------------------------------------------

@pytest.mark.live_phase("InflectionFeatureOperations", "modify")
def test_item8b_createwithguid_roundtrips_guid_for_featstruc(target_sandbox, capsys):
    from SIL.LCModel import IFsFeatStrucFactory

    sandbox = target_sandbox
    infl_ops = sandbox.InflectionFeatures

    created_entry = sandbox.LexEntry.Create(lexeme_form="TEST_probe8b")
    try:
        sense = list(created_entry.SensesOS)
        if not sense:
            from SIL.LCModel import ILexSenseFactory
            factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
            new_sense = factory.Create()
            created_entry.SensesOS.Add(new_sense)
            sense = [new_sense]
        sense_obj = sense[0]

        pos_list = list(sandbox.POS.GetAll())
        pos_obj = pos_list[0] if pos_list else None
        stem = sandbox.MSA.CreateStem(sense_obj, pos_obj)

        requested_guid = "12345678-1234-5678-1234-567812345678"
        with sandbox._TransactionCM("probe item8b _CreateWithGuid roundtrip"):
            fs_factory = sandbox.project.ServiceLocator.GetService(IFsFeatStrucFactory)
            created = infl_ops._CreateWithGuid(fs_factory, guid=requested_guid, kind="IFsFeatStruc probe")
            stem.MsFeaturesOA = created

        actual_guid = str(stem.MsFeaturesOA.Guid)
        print("\n[ITEM 8b] requested GUID:", requested_guid)
        print("[ITEM 8b] actual GUID on created+attached IFsFeatStruc:", actual_guid)
        print("[ITEM 8b] GUID preserved:", actual_guid.lower() == requested_guid.lower())
        assert actual_guid.lower() == requested_guid.lower(), (
            "_CreateWithGuid did not preserve the requested GUID for "
            "IFsFeatStrucFactory -- contradicts the reflection finding "
            "that Create(Guid) exists on the inherited ILcmFactory<T>."
        )
    finally:
        sandbox.LexEntry.Delete(created_entry)
