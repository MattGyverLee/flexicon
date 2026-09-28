#
#   test_issue572_phonrule_readers_live.py
#
#   Issue #572 US2: live verification for the PhonologicalRule readers
#   (GetLeftContext, GetRightContext, IsDisabled, DescribeRule,
#   GetInputPOSes, GetRequiredRuleFeatures, GetExcludedRuleFeatures).
#
#   READ-ONLY on `morphboundary` (opened with writeEnabled=False). Nothing
#   is written to any FLEx project by any test in this file. The SC-003
#   serialisation mirrors evidence/capture_sc003.py exactly.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""Live gate for issue #572 US2 read path (a rule describes itself).

Covers C1-C3, C8 and C10-C11 on PhonologicalRule /
PhonologicalRuleOperations, read-only against `morphboundary`:

- every rule reports `has_environments is True`, and left/right contexts
  match quickstart.md section 2a (`t deletion` left is `None`, returned
  rather than raised);
- the C10 control proves the wrapper (not the raw proxy) does the reading;
- `IsDisabled` matches the `Disabled` values in `sc003-before.json`;
- `GetInputPOSes` returns a `list`; the rule-feature readers return an
  empty `RuleFeatureCollection`, never `None`;
- `rhs_index=99` raises `IndexError`;
- SC-003: `input_contexts` / `output_specs` / `metathesis_parts` serialise
  identically to `sc003-before.json`;
- SC-005: `DescribeRule` is non-empty for all four rules with no .NET
  type name and no object repr;
- SC-001: one test prints every rule with all seven parts using flexicon
  alone (no wrapper-external interface import, no concrete-type dispatch,
  no manual concretion helper).
"""

import importlib.util
import json
import os

import pytest

pytestmark = pytest.mark.requires_live_project

_EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "specs",
    "572-phonological-rule-readers",
    "evidence",
    "sc003-before.json",
)

_CAPTURE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "specs",
    "572-phonological-rule-readers",
    "evidence",
    "capture_sc003.py",
)

# Expected environment per rule GUID, from quickstart.md section 2a and
# the SC-003 capture. `None` means the context slot is empty.
_EXPECTED_ENVIRONMENTS = {
    # t deletion: no left context; right is a segment context.
    "b86737fe-cd3e-4bed-a319-694cd45013a6": (None, "PhSimpleContextSeg"),
    # a insertion: boundary left; sequence right.
    "da557554-f8c3-4251-9c93-bcd305a8871d": (
        "PhSimpleContextBdry",
        "PhSequenceContext",
    ),
    # n insertion (first): segment left; sequence right.
    "e81c1d4d-bcca-4bb3-9498-c4c942270da1": (
        "PhSimpleContextSeg",
        "PhSequenceContext",
    ),
    # n insertion (second): sequence left; segment right.
    "492f00d9-cf5d-4ebb-969a-267ec6c62067": (
        "PhSequenceContext",
        "PhSimpleContextSeg",
    ),
}


def _open_read_only(name):
    """Open an installed project read-only. Caller must close it."""
    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    project.OpenProject(name, writeEnabled=False)
    return project


def _open_rule_ops():
    """Open morphboundary read-only; return (project, rule_ops, rules).

    The caller owns the returned project and must close it.
    """
    from flexicon.code.Grammar.PhonologicalRuleOperations import (
        PhonologicalRuleOperations,
    )

    project = _open_read_only("morphboundary")
    rule_ops = PhonologicalRuleOperations(project)
    rules = list(rule_ops.GetAll())
    assert len(rules) == 4, (
        f"expected 4 phonological rules in morphboundary, got {len(rules)}"
    )
    return project, rule_ops, rules


def _rule_guid(rule):
    """Return the lowercase GUID string of a rule wrapper."""
    return str(rule.lcm_object.Guid).lower()


def _load_expected():
    """Return the rules list recorded in sc003-before.json."""
    with open(_EVIDENCE_PATH, encoding="utf-8") as fh:
        payload = json.load(fh)
    assert payload["project"] == "morphboundary"
    return payload["rules"]


def _serialize_current(rule_ops):
    """Serialise input/output/metathesis shape via capture_sc003.py.

    Imports `serialize_rules` from the evidence capture script so the
    comparison runs the exact same logic that produced sc003-before.json
    (SC-003): only structural identity is recorded, never
    context_name/description text.
    """
    spec = importlib.util.spec_from_file_location(
        "capture_sc003", os.path.abspath(_CAPTURE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.serialize_rules(rule_ops)


def _context_summary(ctx):
    """One-line summary of a context wrapper (or None slot)."""
    if ctx is None:
        return "-"
    return f"{ctx.context_name!r} [{ctx.class_type}]"


class TestMorphboundaryRuleEnvironments:
    """Quickstart section 2a: every rule's environment reads back (C1-C2)."""

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_has_environments_true_for_all_four(self):
        """All four morphboundary rules are regular rules with an RHS."""
        project, _rule_ops, rules = _open_rule_ops()
        try:
            for rule in rules:
                assert rule.has_environments is True, (
                    f"has_environments is not True for {rule.name!r}"
                )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_left_right_contexts_match_quickstart_2a(self):
        """Left/right contexts match the section 2a table, by GUID."""
        project, rule_ops, rules = _open_rule_ops()
        try:
            by_guid = {_rule_guid(r): r for r in rules}
            assert set(by_guid) == set(_EXPECTED_ENVIRONMENTS), (
                "rule GUIDs do not match sc003-before.json; "
                f"got {sorted(by_guid)}"
            )
            for guid, (left_cls, right_cls) in (
                _EXPECTED_ENVIRONMENTS.items()
            ):
                rule = by_guid[guid]
                left = rule_ops.GetLeftContext(rule)
                right = rule_ops.GetRightContext(rule)
                if left_cls is None:
                    # t deletion: the absence is returned, not raised.
                    assert left is None, (
                        f"left of {rule.name!r} should be None, "
                        f"got {left!r}"
                    )
                else:
                    assert left is not None, (
                        f"left of {rule.name!r} is None, "
                        f"expected {left_cls}"
                    )
                    assert left.class_type == left_cls, (
                        f"left of {rule.name!r} is {left.class_type}, "
                        f"expected {left_cls}"
                    )
                assert right is not None, (
                    f"right of {rule.name!r} is None, expected {right_cls}"
                )
                assert right.class_type == right_cls, (
                    f"right of {rule.name!r} is {right.class_type}, "
                    f"expected {right_cls}"
                )
            # The boundary left on `a insertion` describes itself.
            a_insertion = by_guid[
                "da557554-f8c3-4251-9c93-bcd305a8871d"
            ]
            boundary = rule_ops.GetLeftContext(a_insertion)
            assert boundary.is_boundary_context is True
            assert boundary.boundary_name, (
                "boundary_name is empty for the live boundary context"
            )
            # Every sequence context lists its members.
            for rule in rules:
                for ctx in (
                    rule_ops.GetLeftContext(rule),
                    rule_ops.GetRightContext(rule),
                ):
                    if ctx is not None and ctx.is_sequence_context:
                        members = ctx.members
                        assert len(members) > 0, (
                            "sequence context reports no members"
                        )
                        for member in members:
                            assert isinstance(
                                member.context_name, str
                            )
                            assert "SIL.LCModel" not in member.context_name
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_c10_control_wrapper_reads_what_raw_proxy_cannot(self):
        """C10: environment reads go through the concretised wrapper."""
        project = _open_read_only("morphboundary")
        try:
            from flexicon.code.Grammar.PhonologicalRuleOperations import (
                PhonologicalRuleOperations,
            )

            phon = project.lp.PhonologicalDataOA
            raw_rules = list(phon.PhonRulesOS)
            assert raw_rules, "morphboundary has no phonological rules"
            raw = raw_rules[0]
            # The narrowing trap, measured: the raw element cannot see
            # concrete members until it is concretised.
            assert hasattr(raw, "RightHandSidesOS") is False, (
                "precondition failed: raw PhonRulesOS element exposes "
                "RightHandSidesOS -- the C10 control no longer measures "
                "the narrowing trap"
            )
            rule_ops = PhonologicalRuleOperations(project)
            wrapped = list(rule_ops.GetAll())[0]
            assert wrapped.has_environments is True, (
                "wrapper still cannot see RightHandSidesOS through "
                "its concrete object; the C10 routing has regressed"
            )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_rhs_index_out_of_range_raises_index_error(self):
        """An out-of-range rhs_index raises IndexError, not None (C1)."""
        project, rule_ops, rules = _open_rule_ops()
        try:
            for rule in rules:
                with pytest.raises(IndexError):
                    rule_ops.GetLeftContext(rule, rhs_index=99)
                with pytest.raises(IndexError):
                    rule_ops.GetRightContext(rule, rhs_index=99)
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass


class TestMorphboundaryRuleReaders:
    """Disabled state, POSes and rule features (C3-C4, C8-C9)."""

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_is_disabled_matches_sc003_before(self):
        """IsDisabled matches the Disabled recorded in sc003-before.json."""
        expected = {r["guid"].lower(): r for r in _load_expected()}
        project, rule_ops, rules = _open_rule_ops()
        try:
            for rule in rules:
                guid = _rule_guid(rule)
                assert guid in expected, (
                    f"rule {rule.name!r} ({guid}) not in sc003-before.json"
                )
                assert rule_ops.IsDisabled(rule) is expected[guid][
                    "disabled"
                ], (
                    f"IsDisabled({rule.name!r}) is "
                    f"{rule_ops.IsDisabled(rule)!r}, expected "
                    f"{expected[guid]['disabled']!r}"
                )
            # The capture holds exactly one disabled rule: t deletion.
            disabled = [
                r["name"] for r in expected.values() if r["disabled"] is True
            ]
            assert disabled == ["t deletion"], (
                f"expected only 't deletion' disabled, got {disabled}"
            )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_get_input_poses_returns_list(self):
        """GetInputPOSes returns a list for every rule (C3)."""
        project, rule_ops, rules = _open_rule_ops()
        try:
            for rule in rules:
                poses = rule_ops.GetInputPOSes(rule)
                assert isinstance(poses, list), (
                    f"GetInputPOSes({rule.name!r}) is "
                    f"{type(poses).__name__}, not list"
                )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_rule_features_return_empty_collection_not_none(self):
        """No rule features exist here: empty collection, never None (C4)."""
        project, rule_ops, rules = _open_rule_ops()
        try:
            for rule in rules:
                required = rule_ops.GetRequiredRuleFeatures(rule)
                excluded = rule_ops.GetExcludedRuleFeatures(rule)
                for coll, label in (
                    (required, "GetRequiredRuleFeatures"),
                    (excluded, "GetExcludedRuleFeatures"),
                ):
                    assert coll is not None, (
                        f"{label}({rule.name!r}) is None; "
                        "expected an empty collection"
                    )
                    assert type(coll).__name__ == "RuleFeatureCollection", (
                        f"{label}({rule.name!r}) is "
                        f"{type(coll).__name__}, "
                        "not RuleFeatureCollection"
                    )
                    assert len(coll) == 0, (
                        f"{label}({rule.name!r}) holds "
                        f"{len(coll)} items; morphboundary has no "
                        "rule features, expected empty"
                    )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass


class TestMorphboundaryRuleRegression:
    """SC-003 and SC-005: existing members unchanged, rule text renders."""

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_sc003_serialisation_matches_before_capture(self):
        """input/output/metathesis shape is identical to sc003-before."""
        expected = _load_expected()
        project, rule_ops, _rules = _open_rule_ops()
        try:
            current = _serialize_current(rule_ops)
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass
        assert current == expected, (
            "SC-003 regression: live serialisation differs from "
            "sc003-before.json"
        )

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_describe_rule_nonempty_without_leaks(self):
        """SC-005: every rule renders non-empty text, never raising."""
        project, rule_ops, rules = _open_rule_ops()
        try:
            for rule in rules:
                text = rule_ops.DescribeRule(rule)
                assert isinstance(text, str), (
                    f"DescribeRule({rule.name!r}) is "
                    f"{type(text).__name__}, not str"
                )
                assert text, (
                    f"DescribeRule({rule.name!r}) returned an empty string"
                )
                assert "SIL.LCModel" not in text, (
                    f"DescribeRule({rule.name!r}) leaks a type name: {text!r}"
                )
                assert " object at 0x" not in text, (
                    f"DescribeRule({rule.name!r}) leaks a repr: {text!r}"
                )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass


class TestSc001RuleDescribesItself:
    """SC-001: print every rule with all seven parts, flexicon alone."""

    @pytest.mark.live_phase("PhonologicalRule", "read")
    def test_print_every_rule_with_all_seven_parts(self, capsys):
        """The issue's acceptance shape: input, output, environment,
        required/excluded features, input POSes and disabled state."""
        from flexicon.code.Shared.string_utils import best_analysis_text

        project = _open_read_only("morphboundary")
        try:
            rule_ops = project.PhonRules
            rules = list(rule_ops.GetAll())
            assert len(rules) == 4
            for rule in rules:
                left = rule_ops.GetLeftContext(rule)
                right = rule_ops.GetRightContext(rule)
                required = rule_ops.GetRequiredRuleFeatures(rule)
                excluded = rule_ops.GetExcludedRuleFeatures(rule)
                poses = rule_ops.GetInputPOSes(rule)
                print(f"rule: {rule.name}")
                print(
                    "input: "
                    + ", ".join(
                        _context_summary(c)
                        for c in rule.input_contexts
                    )
                )
                print(f"output: {rule_ops.DescribeRule(rule)}")
                print(f"left: {_context_summary(left)}")
                print(f"right: {_context_summary(right)}")
                print(f"required: {list(required.names)}")
                print(f"excluded: {list(excluded.names)}")
                print(
                    "input POSes: "
                    + ", ".join(best_analysis_text(p.Name) for p in poses)
                )
                print(f"disabled: {rule_ops.IsDisabled(rule)}")
            out = capsys.readouterr().out
            for rule in rules:
                assert rule.name in out, (
                    f"rule {rule.name!r} was not printed"
                )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass
