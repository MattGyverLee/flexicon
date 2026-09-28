#
#   test_issue572_context_readers_live.py
#
#   Issue #572 US1: live verification for the PhonologicalContext readers
#   (context_name, description, boundary, iteration bounds, sequence members).
#
#   READ-ONLY on `morphboundary` (opened with writeEnabled=False). The only
#   writes are TEST_-prefixed contexts on the `target_project` fixture,
#   removed in a `finally:` with the pool count asserted back to pre-test.
#   Reads are unrestricted per CLAUDE.md.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""Live gate for issue #572 US1 (a context describes itself).

Covers C5, C6, C7 and C10 on PhonologicalContext / ContextCollection:

- every pooled and rule-referenced context in `morphboundary` reports real
  text (never a .NET type name) from `context_name` / `description` (SC-004);
- each `PhSimpleContextBdry` reports `is_boundary_context`, a marker, a
  non-empty `boundary_name` and a working `as_boundary_context()`;
- `ContextCollection.boundary_contexts()` is non-empty over the pool;
- the `PhSequenceContext` reports `is_sequence_context` and non-empty
  `members`;
- the C10 control proves the wrapper (not the raw proxy) does the reading;
- two `PhIterationContext`s built on Target read back `min_count` /
  `max_count` (`None` for unbounded) / `member` (SC-008 iteration half).

Recorded deviation from tasks.md T003: every pre-existing context Name in
`morphboundary` is unset (`StringCount == 0`, BestAnalysis `***`), so
`context_name` is honestly `""` there and no positive
`filter(name_contains=<pre-existing name>)` match exists. The positive
filter proof therefore runs on Target after the TEST_ contexts are built,
and the `morphboundary` filter assertion is the negative one (no
`SIL.LCModel` leak). Sequence members are likewise unnamed pre-existing
data; their positive non-empty-name proof is the TEST_ member on Target.
"""

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_572_US1_"


def _open_read_only(name):
    """Open an installed project read-only. Caller must close it."""
    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    project.OpenProject(name, writeEnabled=False)
    return project


def _wrap_pool_and_rules():
    """Collect (project, phon_data, wrapped_pool, wrapped_rule_ctxs).

    The caller owns the returned project and must close it.
    """
    from flexicon.code.System.context_collection import ContextCollection
    from flexicon.code.System.phonological_context import PhonologicalContext
    from flexicon.code.lcm_casting import cast_to_concrete

    project = _open_read_only("morphboundary")
    phon = project.lp.PhonologicalDataOA
    assert phon is not None, "morphboundary has no PhonologicalDataOA"
    pool = list(phon.ContextsOS)
    assert pool, "morphboundary ContextsOS pool is empty"

    wrapped_pool = ContextCollection([PhonologicalContext(c) for c in pool])

    rule_ctxs = []
    rules = list(phon.PhonRulesOS)
    assert rules, "morphboundary has no phonological rules"
    for raw_rule in rules:
        concrete_rule = cast_to_concrete(raw_rule)
        for rhs in list(concrete_rule.RightHandSidesOS):
            for slot in ("LeftContextOA", "RightContextOA"):
                ctx = getattr(rhs, slot)
                if ctx is not None:
                    rule_ctxs.append(PhonologicalContext(ctx))
    assert rule_ctxs, "no rule-referenced contexts found in morphboundary"
    return project, phon, wrapped_pool, rule_ctxs


class TestMorphboundaryContextReaders:
    """Read-only US1 assertions against `morphboundary` (SC-004)."""

    @pytest.mark.live_phase("PhonologicalContext", "read")
    def test_context_name_and_description_have_no_type_names(
        self, target_sandbox
    ):
        """SC-004: no .NET type name leaks through either string reader."""
        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None
        project, _phon, wrapped_pool, rule_ctxs = _wrap_pool_and_rules()
        try:
            for ctx in list(wrapped_pool) + rule_ctxs:
                name = ctx.context_name
                assert isinstance(name, str), (
                    f"context_name is {type(name).__name__}, not str, "
                    f"for {ctx.class_type}"
                )
                assert "SIL.LCModel" not in name, (
                    f"context_name leaks a type name: {name!r} "
                    f"({ctx.class_type})"
                )
                desc = ctx.description
                assert isinstance(desc, str), (
                    f"description is {type(desc).__name__}, not str, "
                    f"for {ctx.class_type}"
                )
                assert "SIL.LCModel" not in desc, (
                    f"description leaks a type name: {desc!r} "
                    f"({ctx.class_type})"
                )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalContext", "read")
    def test_boundary_contexts_report_marker(self, target_sandbox):
        """Each PhSimpleContextBdry describes its boundary (C7)."""
        assert target_sandbox.writeEnabled is True
        project, _phon, wrapped_pool, rule_ctxs = _wrap_pool_and_rules()
        try:
            boundaries = [
                c
                for c in list(wrapped_pool) + rule_ctxs
                if c.class_type == "PhSimpleContextBdry"
            ]
            assert boundaries, (
                "no PhSimpleContextBdry in morphboundary pool or rules; "
                "expected at least one"
            )
            for ctx in boundaries:
                assert ctx.is_boundary_context is True, (
                    "is_boundary_context is not True for PhSimpleContextBdry"
                )
                assert ctx.boundary_marker is not None, (
                    "boundary_marker is None for a live boundary context"
                )
                assert ctx.boundary_name, (
                    "boundary_name is empty for a live boundary context"
                )
                assert ctx.as_boundary_context() is not None, (
                    "as_boundary_context() is None for a live boundary context"
                )
            selected = wrapped_pool.boundary_contexts()
            assert len(selected) > 0, (
                "ContextCollection.boundary_contexts() is empty over a pool "
                "holding a PhSimpleContextBdry"
            )
            # Negative filter proof: the repaired context_name never carries
            # a type name, so filtering for one matches nothing.
            leaked = wrapped_pool.filter(name_contains="SIL.LCModel")
            assert len(leaked) == 0, (
                "filter(name_contains='SIL.LCModel') matched; "
                "a type name is leaking into context_name"
            )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalContext", "read")
    def test_sequence_context_lists_members(self, target_sandbox):
        """The PhSequenceContext exposes its pool references (C6)."""
        from flexicon.code.System.context_collection import ContextCollection

        assert target_sandbox.writeEnabled is True
        project, _phon, _pool, rule_ctxs = _wrap_pool_and_rules()
        try:
            sequences = [
                c for c in rule_ctxs if c.is_sequence_context
            ]
            assert sequences, (
                "no PhSequenceContext among morphboundary rule environments; "
                "expected at least one"
            )
            for ctx in sequences:
                members = ctx.members
                assert isinstance(members, ContextCollection), (
                    f"members is {type(members).__name__}, "
                    "not ContextCollection"
                )
                assert len(members) > 0, (
                    "sequence context reports no members"
                )
                for member in members:
                    # Deviation from T003 recorded in the module docstring:
                    # pre-existing member Names are unset, so the honest
                    # value is "". What must hold is the type contract.
                    name = member.context_name
                    assert isinstance(name, str), (
                        f"member context_name is {type(name).__name__}"
                    )
                    assert "SIL.LCModel" not in name
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass

    @pytest.mark.live_phase("PhonologicalContext", "read")
    def test_c10_control_wrapper_reads_what_raw_proxy_cannot(
        self, target_sandbox
    ):
        """C10: capability reads go through the cast wrapper (R-5)."""
        from flexicon.code.System.phonological_context import PhonologicalContext

        assert target_sandbox.writeEnabled is True
        project = _open_read_only("morphboundary")
        try:
            phon = project.lp.PhonologicalDataOA
            raw_elements = list(phon.ContextsOS)
            assert raw_elements, "morphboundary ContextsOS pool is empty"
            raw = raw_elements[0]
            # The narrowing trap, measured: the raw element cannot see
            # concrete members until it is cast.
            assert hasattr(raw, "FeatureStructureRA") is False, (
                "precondition failed: raw ContextsOS element exposes "
                "FeatureStructureRA -- the C10 control no longer measures "
                "the narrowing trap"
            )
            wrapped = PhonologicalContext(raw)
            assert wrapped.class_type == "PhSimpleContextSeg", (
                f"expected first pool element to be PhSimpleContextSeg, "
                f"got {wrapped.class_type}"
            )
            assert wrapped.segment is not None, (
                "wrapper still cannot read FeatureStructureRA through "
                "_concrete; the C10 routing has regressed"
            )
        finally:
            try:
                project.CloseProject()
            except Exception:
                pass


class TestIterationContextWritePath:
    """C5 proven on constructed Target data (SC-008 iteration half)."""

    @pytest.mark.live_phase("PhonologicalContext", "write")
    def test_iteration_bounds_and_member(self, target_project):
        """Unbounded reads None; bounded reads the value; member resolves."""
        from SIL.LCModel import (
            IPhIterationContextFactory,
            IPhSimpleContextBdryFactory,
        )
        from SIL.LCModel.Core.Text import TsStringUtils
        from flexicon.code.System.context_collection import ContextCollection
        from flexicon.code.System.phonological_context import PhonologicalContext

        assert target_project.writeEnabled is True
        phon = target_project.lp.PhonologicalDataOA
        assert phon is not None, "Target has no PhonologicalDataOA"
        pool = phon.ContextsOS
        before = pool.Count

        ws_handle = target_project.project.DefaultAnalWs
        locator = target_project.project.ServiceLocator
        bdry_factory = locator.GetService(IPhSimpleContextBdryFactory)
        iter_factory = locator.GetService(IPhIterationContextFactory)
        assert bdry_factory is not None, "IPhSimpleContextBdryFactory missing"
        assert iter_factory is not None, "IPhIterationContextFactory missing"

        bdry_markers = list(list(phon.PhonemeSetsOS)[0].BoundaryMarkersOC)
        assert bdry_markers, "Target has no boundary markers to build on"
        marker = bdry_markers[0]

        ops = target_project.PhonRules
        member_name = f"{TEST_PREFIX}member"
        iter_unbounded_name = f"{TEST_PREFIX}iter_unbounded"
        iter_bounded_name = f"{TEST_PREFIX}iter_bounded"
        created = []
        try:
            with ops._TransactionCM("TEST_572_US1 seed contexts"):
                member = bdry_factory.Create()
                pool.Add(member)
                member.FeatureStructureRA = marker
                member.Name.set_String(
                    ws_handle, TsStringUtils.MakeString(member_name, ws_handle)
                )
                created.append(member)

                iter_unbounded = iter_factory.Create()
                pool.Add(iter_unbounded)
                iter_unbounded.Minimum = 1
                iter_unbounded.Maximum = -1
                iter_unbounded.MemberRA = member
                iter_unbounded.Name.set_String(
                    ws_handle,
                    TsStringUtils.MakeString(iter_unbounded_name, ws_handle),
                )
                created.append(iter_unbounded)

                iter_bounded = iter_factory.Create()
                pool.Add(iter_bounded)
                iter_bounded.Minimum = 0
                iter_bounded.Maximum = 3
                iter_bounded.MemberRA = member
                iter_bounded.Name.set_String(
                    ws_handle,
                    TsStringUtils.MakeString(iter_bounded_name, ws_handle),
                )
                created.append(iter_bounded)

            # Re-query from ContextsOS after the write, never from the
            # objects just built (C12 corollary).
            requeries = [
                PhonologicalContext(c) for c in list(pool)
            ]
            by_name = {c.context_name: c for c in requeries}
            assert iter_unbounded_name in by_name, (
                "unbounded iteration context did not survive the write"
            )
            assert iter_bounded_name in by_name, (
                "bounded iteration context did not survive the write"
            )
            unbounded = by_name[iter_unbounded_name]
            bounded = by_name[iter_bounded_name]
            assert unbounded.is_iteration_context is True
            assert bounded.is_iteration_context is True
            assert unbounded.min_count == 1, (
                f"min_count {unbounded.min_count} != 1"
            )
            assert unbounded.max_count is None, (
                f"max_count {unbounded.max_count!r} is not None for "
                "Maximum == -1 (unbounded)"
            )
            assert bounded.min_count == 0, (
                f"min_count {bounded.min_count} != 0"
            )
            assert bounded.max_count == 3, (
                f"max_count {bounded.max_count!r} != 3"
            )
            assert unbounded.member is not None, "member did not resolve"
            assert unbounded.member.context_name == member_name, (
                f"member.context_name {unbounded.member.context_name!r} "
                f"!= {member_name!r}"
            )

            # Positive filter proof on real names (see module docstring).
            selected = ContextCollection(requeries).filter(
                name_contains=TEST_PREFIX
            )
            assert len(selected) >= 3, (
                f"filter(name_contains={TEST_PREFIX!r}) matched "
                f"{len(selected)}, expected at least 3"
            )
        finally:
            try:
                with ops._TransactionCM("TEST_572_US1 cleanup contexts"):
                    for obj in created:
                        if obj in pool:
                            pool.Remove(obj)
            except Exception:
                pass
            assert pool.Count == before, (
                f"restore failed: pool count {pool.Count} != pre-test {before}"
            )
