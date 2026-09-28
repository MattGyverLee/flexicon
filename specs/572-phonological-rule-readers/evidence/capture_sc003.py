#
#   capture_sc003.py
#
#   SC-003 before-state capture for issue #572 (phonological rule readers).
#
#   READ-ONLY. Opens `morphboundary` with writeEnabled=False. No factory is
#   called, no UndoableOperation is started, nothing is written to any FLEx
#   project. The only write is the JSON snapshot next to this script.
#
#   Run: python specs/572-phonological-rule-readers/evidence/capture_sc003.py
#
#   Platform: Python.NET, FieldWorks 9+
#
#   Copyright 2026
#

"""Capture input_contexts / output_specs / metathesis_parts for SC-003."""

import json
import os
import sys

_EVIDENCE_DIR = os.path.dirname(os.path.abspath(__file__))
_OUT_PATH = os.path.join(_EVIDENCE_DIR, "sc003-before.json")


def _guid(obj):
    try:
        return str(obj.Guid)
    except Exception:  # noqa: BLE001 -- a scan records, never raises
        return None


def _ctx_record(wrapped_ctx, index):
    raw = wrapped_ctx.lcm_object
    try:
        cls = raw.ClassName
    except Exception:  # noqa: BLE001
        cls = wrapped_ctx.class_type
    return {
        "index": index,
        "class": cls,
        "guid": _guid(raw),
    }


def serialize_rules(rule_ops):
    """Serialise every rule's structural shape (stable across the C7 fix).

    Only structural identity is recorded -- class names, GUIDs, counts and
    Disabled -- never context_name/description text, which the fix changes
    on purpose. T009 re-runs this function and compares identically.
    """
    records = []
    for rule in rule_ops.GetAll():
        raw = rule.lcm_object
        concrete = rule.concrete
        try:
            disabled = bool(concrete.Disabled)
        except Exception:  # noqa: BLE001
            try:
                disabled = bool(raw.Disabled)
            except Exception:  # noqa: BLE001
                disabled = None
        rec = {
            "name": rule.name,
            "class": rule.class_type,
            "guid": _guid(raw),
            "disabled": disabled,
            "input_contexts": [
                _ctx_record(c, i) for i, c in enumerate(rule.input_contexts)
            ],
            "output_specs": [],
            "metathesis_parts": {"left": [], "right": []},
        }
        if rule.has_output_specs:
            for i, rhs in enumerate(rule.output_specs):
                try:
                    struc = [c.ClassName for c in rhs.StrucChangeOS]
                except Exception:  # noqa: BLE001
                    struc = None
                try:
                    left = rhs.LeftContextOA
                    left_cls = left.ClassName if left is not None else None
                    left_guid = _guid(left) if left is not None else None
                except Exception:  # noqa: BLE001
                    left_cls, left_guid = None, None
                try:
                    right = rhs.RightContextOA
                    right_cls = right.ClassName if right is not None else None
                    right_guid = _guid(right) if right is not None else None
                except Exception:  # noqa: BLE001
                    right_cls, right_guid = None, None
                rec["output_specs"].append(
                    {
                        "index": i,
                        "guid": _guid(rhs),
                        "struc_change_classes": struc,
                        "left_class": left_cls,
                        "left_guid": left_guid,
                        "right_class": right_cls,
                        "right_guid": right_guid,
                    }
                )
        if rule.has_metathesis_parts:
            left, right = rule.metathesis_parts
            rec["metathesis_parts"] = {
                "left": [_ctx_record(c, i) for i, c in enumerate(left)],
                "right": [_ctx_record(c, i) for i, c in enumerate(right)],
            }
        records.append(rec)
    return records


def main():
    import faulthandler

    import clr
    from Microsoft.Win32 import Registry

    _reg_key = r"SOFTWARE\SIL\FieldWorks\9"
    _rkey = Registry.LocalMachine.OpenSubKey(_reg_key)
    if _rkey is None:
        _rkey = Registry.CurrentUser.OpenSubKey(_reg_key)
    if _rkey is not None:
        _fw_dir = _rkey.GetValue("RootCodeDir")
        if _fw_dir and os.path.exists(os.path.join(_fw_dir, "FieldWorks.exe")):
            sys.path.append(_fw_dir)

    clr.AddReference("FwUtils")
    clr.AddReference("SIL.WritingSystems")
    clr.AddReference("SIL.LCModel")
    from SIL.FieldWorks.Common.FwUtils import FwRegistryHelper, FwUtils

    FwRegistryHelper.Initialize()
    _was_enabled = faulthandler.is_enabled()
    try:
        if _was_enabled:
            faulthandler.disable()
        FwUtils.InitializeIcu()
    finally:
        if _was_enabled:
            faulthandler.enable()
    from flexicon.code.FLExInit import FLExInitialize

    FLExInitialize()

    from flexicon.code.FLExProject import FLExProject
    from flexicon.code.Grammar.PhonologicalRuleOperations import (
        PhonologicalRuleOperations,
    )

    project = FLExProject()
    project.OpenProject("morphboundary", writeEnabled=False)
    try:
        rule_ops = PhonologicalRuleOperations(project)
        records = serialize_rules(rule_ops)
    finally:
        try:
            project.CloseProject()
        except Exception:  # noqa: BLE001
            pass
    payload = {"project": "morphboundary", "rules": records}
    with open(_OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
    print(f"[OK] captured {len(records)} rules -> {_OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
