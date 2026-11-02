#
#   test_issue802_morphrule_delete_hvo_offline.py
#
#   Offline behaviour tests for issue #802 MorphRuleOperations.Delete:
#   membership is matched by HVO (not Python identity), and no undo bracket
#   is opened when the member is not found.
#
#   Copyright 2026
#

import contextlib
import pathlib

from flexicon.code.Grammar.MorphRuleOperations import MorphRuleOperations

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LIVE_GATE = REPO_ROOT / "tests" / "operations" / "test_issue802_morphrule_delete_hvo_live.py"


class _Obj:
    def __init__(self, hvo, class_name="MoEndoCompound"):
        self.Hvo = hvo
        self.ClassName = class_name


class _Seq(list):
    def Remove(self, item):
        list.remove(self, item)


class _MorphData:
    def __init__(self, rules, prohibs=()):
        self.CompoundRulesOS = _Seq(rules)
        self.AdhocCoProhibitionsOC = _Seq(prohibs)


class _Owner:
    def __init__(self, templates):
        self.AffixTemplatesOS = _Seq(templates)


def _make_ops(morph_data, resolved, owner=None):
    ops = MorphRuleOperations.__new__(MorphRuleOperations)
    ops.project = type(
        "P", (), {"lp": type("LP", (), {"MorphologicalDataOA": morph_data})()}
    )()
    brackets = []

    @contextlib.contextmanager
    def _cm(label):
        brackets.append(label)
        yield

    ops._EnsureWriteEnabled = lambda: None
    ops._ValidateParam = lambda *a, **k: None
    ops._TransactionCM = _cm
    ops._MorphRuleOperations__ResolveObject = lambda _x: resolved
    ops._GetTypedOwner = lambda _r: owner
    return ops, brackets


def test_issue802_delete_removes_member_matched_by_hvo_not_identity():
    keep_a, target_view, keep_b = _Obj(1), _Obj(2), _Obj(3)
    handle = _Obj(2)  # distinct object, same Hvo as target_view
    md = _MorphData([keep_a, target_view, keep_b])
    ops, brackets = _make_ops(md, handle)
    ops.Delete(handle)
    assert md.CompoundRulesOS == [keep_a, keep_b]
    assert brackets == ["Delete compound rule"]


def test_issue802_delete_missing_member_opens_no_bracket_and_removes_nothing():
    members = [_Obj(1), _Obj(3)]
    md = _MorphData(list(members))
    ops, brackets = _make_ops(md, _Obj(99))
    ops.Delete(99)
    assert md.CompoundRulesOS == members
    assert brackets == []


def test_issue802_delete_affix_template_by_hvo():
    other, view = _Obj(5, "MoInflAffixTemplate"), _Obj(6, "MoInflAffixTemplate")
    handle = _Obj(6, "MoInflAffixTemplate")
    owner = _Owner([other, view])
    ops, brackets = _make_ops(_MorphData([]), handle, owner=owner)
    ops.Delete(handle)
    assert owner.AffixTemplatesOS == [other]
    assert brackets == ["Delete affix template"]


def test_issue802_delete_adhoc_prohibition_by_hvo():
    other, view = _Obj(7, "MoAdhocProhibGr"), _Obj(8, "MoAdhocProhibGr")
    handle = _Obj(8, "MoAdhocProhibGr")
    md = _MorphData([], [other, view])
    ops, brackets = _make_ops(md, handle)
    ops.Delete(handle)
    assert md.AdhocCoProhibitionsOC == [other]
    assert brackets == ["Delete ad hoc prohibition"]


def test_issue802_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #802"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
