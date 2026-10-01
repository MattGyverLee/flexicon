#
#   test_issue572_phonrule_construct_live.py
#
#   Issue #572 US2: live write-path verification for the phonological rule
#   readers (rule features, input POSes, Disabled sync key, metathesis
#   silence, DescribeRule totality).
#
#   Writes TEST_-prefixed objects on the `target_project` fixture (see the
#   docstring note below if Target is locked), re-queries every value from
#   the LCM after the write -- never asserts on the value just passed in --
#   and removes every TEST_ object in a `finally:`, asserting the rule,
#   pool, possibility and inflection-class counts back to pre-state.
#   Reads are unrestricted per CLAUDE.md.
#
#   If Target is locked by an open FieldWorks, this module's tests error
#   loudly via the fixture (FLEXLIBS_REQUIRE_LIVE=1); run them on
#   `target_sandbox` instead -- do NOT silently switch fixtures mid-run.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""Live write-path gate for issue #572 US2 (a rule describes itself).

Covers C2-C4, C8-C9 and C11-C12 on PhonologicalRuleOperations, read back
through the new readers after construction on Target (SC-008 rule-feature
half, SC-005 totality, C9 sync key):

- a TEST_ PhRegularRule with two TEST_ IPhPhonRuleFeats (ItemRA on an
  IMoInflClass and on a plain ICmPossibility), one in ReqRuleFeatsRC and
  one in ExclRuleFeatsRC, plus a POS in InputPOSesRC; re-fetched by GUID,
  GetRequiredRuleFeatures / GetExcludedRuleFeatures report .names, .items
  identity and non-empty item_name, and GetInputPOSes contains the POS;
- SetDisabled(rule, True) re-read as True through a fresh lookup, and
  GetSyncableProperties(rule)["Disabled"] is True;
- a TEST_ PhMetathesisRule reports has_environments False, GetLeftContext
  returns None with no warning recorded, and DescribeRule is non-empty;
- DescribeRule is non-empty for a regular rule with its RHS removed;
- DescribeRule renders "*" and not "-1" for an unbounded iteration right
  context.
"""

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_572_US2_"


def _counts(target_project):
    """Snapshot the pool counts asserted back to pre-state."""
    phon = target_project.lp.PhonologicalDataOA
    infl_ops = target_project.InflectionFeatures
    pos_infl = sum(
        len(list(p.InflectionClassesOC))
        for p in list(target_project.POS.GetAll())
    )
    return {
        "rules": phon.PhonRulesOS.Count,
        "pool": phon.ContextsOS.Count,
        "possibilities": phon.PhonRuleFeatsOA.PossibilitiesOS.Count,
        "infl_classes": len(list(infl_ops.InflectionClassGetAll())),
        "pos_infl": pos_infl,
    }


def _assert_counts_restored(target_project, before):
    after = _counts(target_project)
    assert after == before, (
        f"restore failed: counts {after!r} != pre-state {before!r}"
    )


class TestRuleFeaturePOSDisabledRoundTrip:
    """SC-008 rule-feature half + C9, re-queried by GUID."""

    @pytest.mark.live_phase("PhonologicalRule", "write")
    def test_features_poses_and_disabled(self, target_project):
        from SIL.LCModel.Core.Text import TsStringUtils

        assert target_project.writeEnabled is True
        assert getattr(target_project, "project", None) is not None
        phon = target_project.lp.PhonologicalDataOA
        assert phon is not None, "Target has no PhonologicalDataOA"

        ops = target_project.PhonRules
        pos_ops = target_project.POS
        infl_ops = target_project.InflectionFeatures
        before = _counts(target_project)
        ws_handle = target_project.project.DefaultAnalWs
        locator = target_project.project.ServiceLocator

        rule_name = f"{TEST_PREFIX}feat_rule"
        feat_req_name = f"{TEST_PREFIX}req_feat"
        feat_excl_name = f"{TEST_PREFIX}excl_feat"
        infl_name = f"{TEST_PREFIX}infl_class"
        poss_name = f"{TEST_PREFIX}plain_poss"
        pos_name = f"{TEST_PREFIX}pos"

        created_pos = None
        created_infl = None
        created = {"rules": [], "feats": [], "poss": []}
        try:
            # POS: reuse an existing one; create a TEST_ one if Target
            # has none.
            existing_poses = list(pos_ops.GetAll())
            pos = existing_poses[0] if existing_poses else None
            if pos is None:
                pos = pos_ops.Create(pos_name, "TST")
                created_pos = pos
            pos_hvo = pos.Hvo

            # IMoInflClass ItemRA target: inflection classes are owned by
            # their POS (pos.InflectionClassesOC --
            # HCLoaderTests.cs:322-329), not by
            # ProdRestrictOA.PossibilitiesOS, so InflectionClassCreate
            # (which adds there and raises TypeError on this LCM build)
            # cannot build one. Reuse a POS-owned class; else create a
            # TEST_ one under the POS.
            from SIL.LCModel import IMoInflClassFactory

            infl_factory = locator.GetService(IMoInflClassFactory)
            assert infl_factory is not None, (
                "IMoInflClassFactory missing on this LCM build"
            )
            infl_class = None
            for candidate_pos in list(pos_ops.GetAll()):
                for candidate in list(candidate_pos.InflectionClassesOC):
                    infl_class = candidate
                    break
                if infl_class is not None:
                    break
            if infl_class is None:
                with ops._TransactionCM("TEST_572_US2 seed infl class"):
                    infl_class = infl_factory.Create()
                    pos.InflectionClassesOC.Add(infl_class)
                    infl_class.Name.set_String(
                        ws_handle,
                        TsStringUtils.MakeString(infl_name, ws_handle),
                    )
                    infl_class.Abbreviation.set_String(
                        ws_handle,
                        TsStringUtils.MakeString(infl_name, ws_handle),
                    )
                created_infl = (pos, infl_class)
            infl_hvo = infl_class.Hvo

            # IPhPhonRuleFeat factory, resolved through the ServiceLocator
            # (tolerates builds where the factory is not bindable: the
            # lookup below fails loudly instead of silently building the
            # wrong class).
            from SIL.LCModel import IPhPhonRuleFeatFactory

            feat_factory = locator.GetService(IPhPhonRuleFeatFactory)
            assert feat_factory is not None, (
                "IPhPhonRuleFeatFactory missing on this LCM build"
            )
            from SIL.LCModel import ICmPossibilityFactory

            poss_factory = locator.GetService(ICmPossibilityFactory)
            assert poss_factory is not None, (
                "ICmPossibilityFactory missing on this LCM build"
            )

            rule = ops.Create(rule_name)
            created["rules"].append(rule)
            ops.WireRule(rule)
            rhs = rule.RightHandSidesOS[0]
            feats_owner = phon.PhonRuleFeatsOA.PossibilitiesOS

            with ops._TransactionCM("TEST_572_US2 seed rule features"):
                plain_poss = poss_factory.Create()
                feats_owner.Add(plain_poss)
                plain_poss.Name.set_String(
                    ws_handle, TsStringUtils.MakeString(poss_name, ws_handle)
                )
                created["poss"].append(plain_poss)

                req_feat = feat_factory.Create()
                feats_owner.Add(req_feat)
                req_feat.Name.set_String(
                    ws_handle,
                    TsStringUtils.MakeString(feat_req_name, ws_handle),
                )
                req_feat.ItemRA = infl_class
                created["feats"].append(req_feat)

                excl_feat = feat_factory.Create()
                feats_owner.Add(excl_feat)
                excl_feat.Name.set_String(
                    ws_handle,
                    TsStringUtils.MakeString(feat_excl_name, ws_handle),
                )
                excl_feat.ItemRA = plain_poss
                created["feats"].append(excl_feat)

                rhs.ReqRuleFeatsRC.Add(req_feat)
                rhs.ExclRuleFeatsRC.Add(excl_feat)
                rhs.InputPOSesRC.Add(pos)

            # Re-fetch the rule by GUID -- never assert on the objects
            # just built (C12 corollary).
            guid_str = str(rule.Guid)
            refetched = target_project.Object(guid_str)
            assert refetched is not None, (
                "rule did not survive the write (GUID lookup failed)"
            )

            req_coll = ops.GetRequiredRuleFeatures(refetched)
            excl_coll = ops.GetExcludedRuleFeatures(refetched)
            assert feat_req_name in req_coll.names, (
                f"required .names {req_coll.names!r} missing {feat_req_name!r}"
            )
            assert feat_excl_name in excl_coll.names, (
                f"excluded .names {excl_coll.names!r} missing {feat_excl_name!r}"
            )
            req_items = req_coll.items
            excl_items = excl_coll.items
            assert any(i.Hvo == infl_hvo for i in req_items), (
                "required .items identity mismatch: IMoInflClass not found"
            )
            assert any(i.Hvo == plain_poss.Hvo for i in excl_items), (
                "excluded .items identity mismatch: plain possibility "
                "not found"
            )
            for feat in list(req_coll) + list(excl_coll):
                assert feat.item_name, (
                    "item_name is empty for a feature with an ItemRA target"
                )
            poses = ops.GetInputPOSes(refetched)
            assert isinstance(poses, list), (
                f"GetInputPOSes returned {type(poses).__name__}, not list"
            )
            assert any(p.Hvo == pos_hvo for p in poses), (
                "GetInputPOSes does not contain the wired POS"
            )

            # Disabled round-trip through a fresh lookup (C8/C9).
            ops.SetDisabled(refetched, True)
            reread = target_project.Object(guid_str)
            assert ops.IsDisabled(reread) is True, (
                "SetDisabled(rule, True) did not re-read as True"
            )
            sync_props = ops.GetSyncableProperties(reread)
            assert sync_props["Disabled"] is True, (
                "GetSyncableProperties(rule)['Disabled'] is not True"
            )
        finally:
            try:
                with ops._TransactionCM("TEST_572_US2 cleanup features"):
                    for obj in created["rules"]:
                        if obj in phon.PhonRulesOS:
                            phon.PhonRulesOS.Remove(obj)
                    for obj in created["feats"] + created["poss"]:
                        owner = phon.PhonRuleFeatsOA.PossibilitiesOS
                        if obj in owner:
                            owner.Remove(obj)
                    if created_infl is not None:
                        owner_pos, obj = created_infl
                        if obj in owner_pos.InflectionClassesOC:
                            owner_pos.InflectionClassesOC.Remove(obj)
                    if created_pos is not None:
                        try:
                            pos_ops.Delete(created_pos)
                        except Exception:
                            pass
            except Exception:
                pass
            _assert_counts_restored(target_project, before)


class TestMetathesisSilence:
    """C2: a metathesis rule has no environment and says so silently."""

    @pytest.mark.live_phase("PhonologicalRule", "write")
    def test_metathesis_reports_no_environment(
        self, target_project, recwarn
    ):
        from flexicon.code.Grammar.phonological_rule import PhonologicalRule
        from flexicon.code.lcm_casting import _get_factory_for_class

        assert target_project.writeEnabled is True
        phon = target_project.lp.PhonologicalDataOA
        assert phon is not None, "Target has no PhonologicalDataOA"

        ops = target_project.PhonRules
        before = _counts(target_project)
        met_name = f"{TEST_PREFIX}metathesis"
        met_rule = None
        try:
            factory = _get_factory_for_class(
                "PhMetathesisRule", target_project.project
            )
            assert factory is not None, (
                "PhMetathesisRule factory missing on this LCM build"
            )
            with ops._TransactionCM("TEST_572_US2 seed metathesis rule"):
                met_rule = factory.Create()
                phon.PhonRulesOS.Add(met_rule)

            wrapped = PhonologicalRule(met_rule)
            assert wrapped.has_environments is False, (
                "has_environments is not False for a PhMetathesisRule"
            )
            assert ops.GetLeftContext(met_rule) is None, (
                "GetLeftContext did not return None for a metathesis rule"
            )
            assert ops.GetRightContext(met_rule) is None, (
                "GetRightContext did not return None for a metathesis rule"
            )
            assert len(recwarn.list) == 0, (
                f"metathesis silence broken: "
                f"{len(recwarn.list)} warnings recorded"
            )
            text = ops.DescribeRule(met_rule)
            assert isinstance(text, str) and text, (
                "DescribeRule is empty for a metathesis rule"
            )
        finally:
            try:
                with ops._TransactionCM("TEST_572_US2 cleanup metathesis"):
                    if met_rule is not None and met_rule in phon.PhonRulesOS:
                        phon.PhonRulesOS.Remove(met_rule)
            except Exception:
                pass
            _assert_counts_restored(target_project, before)


class TestDescribeRuleTotality:
    """SC-005 write-path half: DescribeRule never raises, never leaks."""

    @pytest.mark.live_phase("PhonologicalRule", "write")
    def test_describe_rule_without_rhs(self, target_project):
        assert target_project.writeEnabled is True
        phon = target_project.lp.PhonologicalDataOA
        assert phon is not None, "Target has no PhonologicalDataOA"

        ops = target_project.PhonRules
        before = _counts(target_project)
        rule_name = f"{TEST_PREFIX}no_rhs_rule"
        rule = None
        try:
            rule = ops.Create(rule_name)
            ops.WireRule(rule)
            with ops._TransactionCM("TEST_572_US2 remove RHS"):
                rhs_list = rule.RightHandSidesOS
                for rhs in list(rhs_list):
                    rhs_list.Remove(rhs)
            assert rule.RightHandSidesOS.Count == 0, (
                "precondition failed: RHS was not removed"
            )
            text = ops.DescribeRule(rule)
            assert isinstance(text, str) and text, (
                "DescribeRule is empty for a regular rule with no RHS"
            )
        finally:
            try:
                with ops._TransactionCM("TEST_572_US2 cleanup no-RHS rule"):
                    if rule is not None and rule in phon.PhonRulesOS:
                        phon.PhonRulesOS.Remove(rule)
            except Exception:
                pass
            _assert_counts_restored(target_project, before)

    @pytest.mark.live_phase("PhonologicalRule", "write")
    def test_describe_rule_unbounded_iteration(self, target_project):
        from SIL.LCModel import (
            IPhIterationContextFactory,
            IPhSimpleContextBdryFactory,
        )
        from SIL.LCModel.Core.Text import TsStringUtils

        assert target_project.writeEnabled is True
        phon = target_project.lp.PhonologicalDataOA
        assert phon is not None, "Target has no PhonologicalDataOA"

        ops = target_project.PhonRules
        before = _counts(target_project)
        ws_handle = target_project.project.DefaultAnalWs
        locator = target_project.project.ServiceLocator

        rule_name = f"{TEST_PREFIX}unbounded_rule"
        member_name = f"{TEST_PREFIX}unbounded_member"
        iter_name = f"{TEST_PREFIX}unbounded_iter"
        rule = None
        created_ctxs = []
        try:
            bdry_factory = locator.GetService(IPhSimpleContextBdryFactory)
            iter_factory = locator.GetService(IPhIterationContextFactory)
            assert bdry_factory is not None, (
                "IPhSimpleContextBdryFactory missing"
            )
            assert iter_factory is not None, (
                "IPhIterationContextFactory missing"
            )
            markers = list(list(phon.PhonemeSetsOS)[0].BoundaryMarkersOC)
            assert markers, "Target has no boundary markers to build on"

            rule = ops.Create(rule_name)
            ops.WireRule(rule)
            rhs = rule.RightHandSidesOS[0]
            pool = phon.ContextsOS

            with ops._TransactionCM("TEST_572_US2 seed unbounded ctx"):
                member = bdry_factory.Create()
                pool.Add(member)
                member.FeatureStructureRA = markers[0]
                member.Name.set_String(
                    ws_handle, TsStringUtils.MakeString(member_name, ws_handle)
                )
                created_ctxs.append(member)

                iter_ctx = iter_factory.Create()
                pool.Add(iter_ctx)
                iter_ctx.Minimum = 1
                iter_ctx.Maximum = -1
                iter_ctx.MemberRA = member
                iter_ctx.Name.set_String(
                    ws_handle, TsStringUtils.MakeString(iter_name, ws_handle)
                )
                created_ctxs.append(iter_ctx)

                rhs.RightContextOA = iter_ctx

            text = ops.DescribeRule(rule)
            assert isinstance(text, str) and text, (
                "DescribeRule is empty for a rule with an iteration context"
            )
            assert "*" in text, (
                f"DescribeRule does not render unbounded as '*': {text!r}"
            )
            assert "-1" not in text, (
                f"DescribeRule leaks the raw -1 sentinel: {text!r}"
            )
        finally:
            try:
                with ops._TransactionCM("TEST_572_US2 cleanup unbounded"):
                    if rule is not None and rule in phon.PhonRulesOS:
                        phon.PhonRulesOS.Remove(rule)
                    pool = phon.ContextsOS
                    for obj in created_ctxs:
                        if obj in pool:
                            pool.Remove(obj)
            except Exception:
                pass
            _assert_counts_restored(target_project, before)
