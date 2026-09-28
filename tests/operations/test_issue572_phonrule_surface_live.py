#
#   test_issue572_phonrule_surface_live.py
#
#   Issue #572: LCM surface verification probe for the proposed
#   PhonologicalRule / PhonologicalContext readers (rule environment,
#   required/excluded rule features, input POSes, Disabled, iteration
#   and sequence contexts).
#
#   READ-ONLY. Every project is opened with writeEnabled=False. No
#   factory is called, no UndoableOperation is started, nothing is
#   written anywhere. Reads are unrestricted per CLAUDE.md.
#
#   The probe answers three questions the spec must not guess at:
#     1. Does every property the issue names actually exist on the
#        target LCM interface, and with what type?
#     2. What are the real ClassName strings for the context types?
#     (the issue's evidence recipe dispatches on ClassName)
#     3. Are there populated instances on this machine to read values
#        from, so a later implementation has a non-empty fixture?
#
#   Results land in
#   specs/572-phonological-rule-readers/evidence/live-*.json
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import os

import pytest

pytestmark = pytest.mark.requires_live_project


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EVIDENCE_DIR = os.path.join(
    _REPO_ROOT, "specs", "572-phonological-rule-readers", "evidence"
)

# Installed projects, in scan order. Reads are unrestricted; Target and
# Sena 3 are the sanctioned write targets but this probe only reads.
_TARGETS = ["Target", "Sena 3", "morphboundary", "Resembli", "Mbugwe Lizzie"]

# Types the issue names. Absence is a finding, not a failure.
_SURFACES = [
    "IPhSegRuleRHS",
    "IPhRegularRule",
    "IPhMetathesisRule",
    "IPhIterationContext",
    "IPhSequenceContext",
    "IPhPhonRuleFeat",
    "IPhPhonContext",
    "IPhContextOrVar",
    "IPhSimpleContext",
    "IPhSimpleContextSeg",
    "IPhSimpleContextNC",
    "IPhSimpleContextBdry",
    "IPhBoundaryContext",
    "IPhSegmentRule",
    "IPhPhonRule",
    "IPhPhonRuleFeature",
]

# Concrete ClassNames to confirm or deny.
_CLASSNAMES = [
    "PhRegularRule",
    "PhMetathesisRule",
    "PhSegmentRule",
    "PhPhonRule",
    "PhIterationContext",
    "PhSequenceContext",
    "PhSimpleContextSeg",
    "PhSimpleContextNC",
    "PhSimpleContextBdry",
    "PhBoundaryContext",
    "PhComplexContextSeg",
    "PhComplexContextNC",
    "PhPhonRuleFeat",
]

_MEMBERS_OF_INTEREST = [
    ("IPhSegRuleRHS", "LeftContextOA"),
    ("IPhSegRuleRHS", "RightContextOA"),
    ("IPhSegRuleRHS", "StrucChangeOS"),
    ("IPhSegRuleRHS", "ReqRuleFeatsRC"),
    ("IPhSegRuleRHS", "ExclRuleFeatsRC"),
    ("IPhSegRuleRHS", "InputPOSesRC"),
    ("IPhSegRuleRHS", "OwningRule"),
    ("IPhRegularRule", "Disabled"),
    ("IPhMetathesisRule", "Disabled"),
    ("IPhSegmentRule", "Disabled"),
    ("IPhSegmentRule", "StrucDescOS"),
    ("IPhRegularRule", "RightHandSidesOS"),
    ("IPhRegularRule", "Direction"),
    ("IPhRegularRule", "FeatureConstraints"),
    ("IPhRegularRule", "InitialStratumRA"),
    ("IPhRegularRule", "FinalStratumRA"),
    ("IPhIterationContext", "Minimum"),
    ("IPhIterationContext", "Maximum"),
    ("IPhIterationContext", "MemberRA"),
    ("IPhSequenceContext", "MembersRS"),
    ("IPhPhonRuleFeat", "ItemRA"),
    ("IPhPhonRuleFeat", "FeatureStructureRA"),
    ("IPhSimpleContextSeg", "FeatureStructureRA"),
    ("IPhSimpleContextNC", "PlusConstrRS"),
    ("IPhSimpleContextNC", "MinusConstrRS"),
]


def _write(name, payload):
    os.makedirs(_EVIDENCE_DIR, exist_ok=True)
    path = os.path.join(_EVIDENCE_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    return path


def _open_read_only(name):
    """Open an installed project read-only. Returns (project, error)."""
    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    try:
        project.OpenProject(name, writeEnabled=False)
    except Exception as exc:  # noqa: BLE001 -- a scan records, never asserts
        return None, f"{type(exc).__name__}: {exc}"
    return project, None


def _describe(obj):
    """Describe one live LCM object: class name, class id, hvo, guid."""
    if obj is None:
        return None
    rec = {"class": getattr(obj, "ClassName", None)}
    for attr in ("Hvo", "ClassID", "Id"):
        try:
            rec[attr] = int(getattr(obj, attr))
        except Exception:  # noqa: BLE001
            rec[attr] = None
    return rec


def _describe_context(ctx):
    """Describe a live IPhPhonContext, incl. the pythonnet narrowing trap."""
    rec = _describe(ctx) or {}
    rec["py_type"] = type(ctx).__name__
    for attr in ("FeatureStructureRA", "MemberRA", "MembersRS", "Minimum",
                 "Maximum", "Name", "Type"):
        rec[f"has_{attr}"] = hasattr(ctx, attr)
    for attr in ("Name", "Type", "Minimum", "Maximum"):
        try:
            val = getattr(ctx, attr)
            rec[attr] = str(val) if val is not None else None
        except Exception:  # noqa: BLE001
            rec[attr] = None
    try:
        fs = ctx.FeatureStructureRA
        rec["FeatureStructureRA"] = (
            _describe(fs) if fs is not None else None
        )
    except Exception:  # noqa: BLE001
        rec["FeatureStructureRA"] = None
    try:
        member = ctx.MemberRA
        rec["MemberRA"] = _describe(member) if member is not None else None
    except Exception:  # noqa: BLE001
        rec["MemberRA"] = None
    try:
        members = list(ctx.MembersRS)
        rec["MembersRS"] = [_describe(m) for m in members]
    except Exception:  # noqa: BLE001
        rec["MembersRS"] = None
    return rec


@pytest.mark.live_phase("FLExProject", "read")
def test_issue572_lcm_surface_recorded():
    """Reflect every SIL.LCModel type issue #572 names, off a live runtime."""
    from System.Reflection import BindingFlags

    from flexicon.code.FLExProject import FLExProject  # noqa: F401
    from SIL.LCModel import ICmObject

    # The runtime only exists once a project is open, so bootstrap with
    # the smallest possible open, then take the assembly off a live LCM
    # object rather than Assembly.Load (which fails: pythonnet's load
    # context cannot resolve a bare name).
    project, err = _open_read_only("Target")
    assert project is not None, f"could not open Target read-only: {err}"
    try:
        probe = project.lp
        asm = probe.GetType().Assembly
        flags = (
            BindingFlags.Public | BindingFlags.Instance | BindingFlags.FlattenHierarchy
        )

        results = {"types": {}, "classnames": {}, "members_of_interest": {}}
        for name in _SURFACES:
            t = asm.GetType(f"SIL.LCModel.{name}")
            if t is None:
                results["types"][name] = {"found": False}
                continue
            props = {}
            for p in t.GetProperties(flags):
                props[p.Name] = {
                    "type": p.PropertyType.FullName,
                    "can_read": bool(p.CanRead),
                    "can_write": bool(p.CanWrite),
                }
            results["types"][name] = {
                "found": True,
                "properties": dict(sorted(props.items())),
                "methods": sorted(
                    m.Name for m in t.GetMethods(flags) if m.DeclaringType == t
                ),
                "interfaces": sorted(i.FullName for i in t.GetInterfaces()),
            }

        for cn in _CLASSNAMES:
            results["classnames"][cn] = {
                "found": asm.GetType(f"SIL.LCModel.{cn}") is not None
            }

        for iface, member in _MEMBERS_OF_INTEREST:
            key = f"{iface}.{member}"
            entry = results["types"].get(iface) or {}
            if not entry.get("found"):
                results["members_of_interest"][key] = {"interface_found": False}
            else:
                results["members_of_interest"][key] = {
                    "interface_found": True,
                    "member": entry["properties"].get(member),
                }

        path = _write("live-surface-probe.json", results)

        # The probe must not "pass" on a stub. If SIL.LCModel is not
        # really loaded, nothing reflects and this trips.
        assert results["types"]["IPhSegRuleRHS"]["found"], (
            "IPhSegRuleRHS did not reflect -- SIL.LCModel is not really loaded"
        )
        assert ICmObject is not None
        assert os.path.exists(path)
    finally:
        try:
            project.CloseProject()
        except Exception:
            pass


@pytest.mark.live_phase("PhonologicalRuleOperations", "read")
def test_issue572_instances_recorded():
    """Read real values off every installed project that has phon rules."""
    from flexicon.code.lcm_casting import cast_to_concrete

    report = {"scanned": [], "with_rules": []}

    for name in _TARGETS:
        project, err = _open_read_only(name)
        rec = {"project": name, "opened": project is not None, "error": err}
        if project is None:
            report["scanned"].append(rec)
            continue
        try:
            phon = project.lp.PhonologicalDataOA
            rec["has_phonological_data"] = phon is not None
            if phon is None:
                report["scanned"].append(rec)
                continue
            rules = list(phon.PhonRulesOS)
            rec["rule_count"] = len(rules)

            feats_oa = getattr(phon, "PhonRuleFeatsOA", None)
            rec["phon_rule_feats_oa"] = _describe(feats_oa)
            if feats_oa is not None:
                poss = feats_oa.PossibilitiesOS
                rec["rule_feat_count"] = poss.Count
                rec["rule_feat_names"] = [
                    _possibility_name(poss[i]) for i in range(min(20, poss.Count))
                ]

            contexts_pool = getattr(phon, "ContextsOS", None)
            rec["contexts_pool_count"] = (
                contexts_pool.Count if contexts_pool is not None else None
            )
            if contexts_pool is not None:
                rec["context_pool_classnames"] = sorted(
                    {contexts_pool[i].ClassName for i in range(contexts_pool.Count)}
                )

            rec["rules"] = []
            for rule in rules[:60]:
                entry = {
                    "name": _ms_text(rule, "Name"),
                    "class": rule.ClassName,
                    "has_Disabled": hasattr(rule, "Disabled"),
                    "has_RightHandSidesOS": hasattr(rule, "RightHandSidesOS"),
                    "disabled": _read_bool(rule, "Disabled"),
                    "sd_count": (
                        rule.StrucDescOS.Count if hasattr(rule, "StrucDescOS") else None
                    ),
                    "sd": [
                        _describe_context(c) for c in getattr(rule, "StrucDescOS", [])
                    ],
                }
                concrete = cast_to_concrete(rule)
                entry["concrete_class"] = concrete.ClassName
                entry["concrete_has_RightHandSidesOS"] = hasattr(
                    concrete, "RightHandSidesOS"
                )
                if entry["concrete_has_RightHandSidesOS"]:
                    entry["rhs"] = []
                    for rhs in concrete.RightHandSidesOS:
                        entry["rhs"].append(
                            {
                                "left": _describe_context(rhs.LeftContextOA),
                                "right": _describe_context(rhs.RightContextOA),
                                "struc_change": [
                                    _describe_context(c) for c in rhs.StrucChangeOS
                                ],
                                "req_feats": [
                                    _describe_rule_feat(f) for f in rhs.ReqRuleFeatsRC
                                ],
                                "excl_feats": [
                                    _describe_rule_feat(f) for f in rhs.ExclRuleFeatsRC
                                ],
                                "input_poses": [
                                    _possibility_name(p) for p in rhs.InputPOSesRC
                                ],
                            }
                        )
                rec["rules"].append(entry)

            if rules:
                report["with_rules"].append(name)
        except Exception as exc:  # noqa: BLE001 -- a scan records, never asserts
            rec["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass
        report["scanned"].append(rec)

    path = _write("live-instance-probe.json", report)

    assert any(r["opened"] for r in report["scanned"]), (
        f"no project opened at all: {report['scanned']}"
    )
    assert os.path.exists(path)


def _ms_text(obj, prop):
    """Best-effort analysis text of a MultiString property."""
    try:
        ms = getattr(obj, prop)
        return ms.BestAnalysisAlternative.Text
    except Exception:  # noqa: BLE001
        return None


def _read_bool(obj, prop):
    try:
        return bool(getattr(obj, prop))
    except Exception:  # noqa: BLE001
        return None


def _possibility_name(obj):
    if obj is None:
        return None
    try:
        return obj.Name.BestAnalysisAlternative.Text
    except Exception:  # noqa: BLE001
        return None


def _describe_rule_feat(feat):
    """Describe one IPhPhonRuleFeat: its owner name and its ItemRA link."""
    rec = _describe(feat) or {}
    rec["py_type"] = type(feat).__name__
    rec["has_ItemRA"] = hasattr(feat, "ItemRA")
    rec["has_FeatureStructureRA"] = hasattr(feat, "FeatureStructureRA")
    item = getattr(feat, "ItemRA", None)
    rec["ItemRA"] = _describe(item) if item is not None else None
    rec["ItemRA_name"] = _possibility_name(item) if item is not None else None
    return rec
