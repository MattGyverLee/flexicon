#
#   test_449_wrapper_write_paths_live.py
#
#   Class: (none -- module of pytest test classes)
#          Live WRITE-path verification for issue #449 -- every wrapper
#          item taken from a wrapper-returning GetAll() can be passed
#          straight into a mutating Operations method, and the mutation
#          is confirmed by RE-QUERYING the object from the LCM (a fresh
#          GetAll() or project.Object(hvo)), not by re-asserting on the
#          value that was passed in.
#
#          Companion to test_449_getall_roundtrip_live.py, which is
#          read-only. That file proves every wrapper item resolves
#          without raising; this file proves the actual write reaches
#          the LCM and is observable afterwards.
#
#          target_sandbox and sena3_sandbox are both fresh tempdir
#          copies of their respective .fwbackup fixtures (function-
#          scoped: a new copy per test), so in-place writes here are
#          non-destructive per CLAUDE.md.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.Shared.wrapper_base import LCMObjectWrapper

pytestmark = pytest.mark.requires_live_project


def _compound_rules(project):
    return [r for r in project.MorphRules.GetAll() if r.class_type in ("MoEndoCompound", "MoExoCompound")]


class TestMorphRuleOperationsWrapperWritesLive:
    """SetStratum / SetDisabled / Duplicate / Delete on a compound-rule wrapper."""

    @pytest.mark.live_phase("MorphRuleOperations", "modify")
    def test_set_disabled_via_wrapper_flips_state(self, sena3_sandbox):
        project = sena3_sandbox
        compound = _compound_rules(project)[0]
        assert isinstance(compound, LCMObjectWrapper)
        hvo = compound.lcm_object.Hvo

        pre = project.MorphRules.IsDisabled(compound)
        project.MorphRules.SetDisabled(compound, not pre)

        # Re-query: fresh GetAll(), not the wrapper we mutated with.
        fresh = next(r for r in project.MorphRules.GetAll() if r.lcm_object.Hvo == hvo)
        post = project.MorphRules.IsDisabled(fresh)
        assert post == (not pre), f"Disabled flag did not flip: pre={pre} post={post}"

    @pytest.mark.live_phase("MorphRuleOperations", "modify")
    def test_set_stratum_via_wrapper_reassigns(self, sena3_sandbox):
        project = sena3_sandbox
        compound = _compound_rules(project)[0]
        assert isinstance(compound, LCMObjectWrapper)
        hvo = compound.lcm_object.Hvo

        pre_stratum = project.MorphRules.GetStratum(compound)
        pre_hvo = pre_stratum.Hvo if pre_stratum else None

        new_stratum = project.Strata.Create("TEST_449_stratum")
        project.MorphRules.SetStratum(compound, new_stratum)

        fresh = next(r for r in project.MorphRules.GetAll() if r.lcm_object.Hvo == hvo)
        post_stratum = project.MorphRules.GetStratum(fresh)
        assert post_stratum is not None, "Stratum was not set at all"
        assert post_stratum.Hvo == new_stratum.Hvo
        assert post_stratum.Hvo != pre_hvo

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_duplicate_via_wrapper_creates_new_object(self, sena3_sandbox):
        project = sena3_sandbox
        compound = _compound_rules(project)[0]
        assert isinstance(compound, LCMObjectWrapper)

        before_count = len(_compound_rules(project))
        dup = project.MorphRules.Duplicate(compound)
        assert dup.Hvo != compound.lcm_object.Hvo

        after = _compound_rules(project)
        assert len(after) == before_count + 1, (
            f"Compound rule count did not increase: {before_count} -> {len(after)}"
        )
        assert any(r.lcm_object.Hvo == dup.Hvo for r in after), (
            "Duplicate's Hvo not found in a fresh GetAll() re-query"
        )

    @pytest.mark.live_phase("MorphRuleOperations", "delete")
    def test_delete_via_wrapper_removes_object(self, sena3_sandbox):
        project = sena3_sandbox
        compounds = _compound_rules(project)
        assert len(compounds) >= 2, "Need >=2 compound rules in Sena 3 to delete one safely"
        target = compounds[0]
        assert isinstance(target, LCMObjectWrapper)
        hvo = target.lcm_object.Hvo

        before_count = len(compounds)
        project.MorphRules.Delete(target)

        after = _compound_rules(project)
        assert len(after) == before_count - 1, (
            f"Compound rule count did not decrease: {before_count} -> {len(after)}"
        )
        assert not any(r.lcm_object.Hvo == hvo for r in after), (
            "Deleted rule's Hvo still present in a fresh GetAll() re-query"
        )

    # Formerly xfail: the MoInflAffixTemplate Delete owner bug was fixed
    # by #467 (_GetTypedOwner); this now passes live and guards it.
    @pytest.mark.live_phase("MorphRuleOperations", "delete")
    def test_delete_affix_template_via_wrapper_deletes(self, sena3_sandbox):
        project = sena3_sandbox
        templates = [r for r in project.MorphRules.GetAll() if r.class_type == "MoInflAffixTemplate"]
        assert templates, "Sena 3 sandbox has no affix templates to test."
        target = templates[0]
        assert isinstance(target, LCMObjectWrapper)

        before_count = len(templates)
        project.MorphRules.Delete(target)

        after_templates = [r for r in project.MorphRules.GetAll() if r.class_type == "MoInflAffixTemplate"]
        assert len(after_templates) == before_count - 1, (
            "Expected the affix template to actually be deleted (Delete "
            "silently no-opped on an uncast owner before #467)."
        )


class TestReorderWithWrapperItemsLive:
    """MoveUp / MoveDown / MoveBefore / MoveAfter / Swap on allomorph wrappers."""

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_reorder_family_with_wrapper_items(self, target_sandbox):
        project = target_sandbox
        entry = project.LexEntry.Create("TEST_449_reorder")
        project.Allomorphs.Create(entry, "TEST_449_alt_a")
        project.Allomorphs.Create(entry, "TEST_449_alt_b")
        project.Allomorphs.Create(entry, "TEST_449_alt_c")

        def forms():
            # Re-query directly against the raw LCM sequence, not the
            # wrapper collection, on every call.
            return [project.Allomorphs.GetForm(a) for a in entry.AlternateFormsOS]

        pre = forms()
        assert pre == ["TEST_449_alt_a", "TEST_449_alt_b", "TEST_449_alt_c"], pre

        # index 0 of GetAll(entry) is the lexeme form, not an AlternateFormsOS
        # member -- MoveUp/Down/etc. reorder AlternateFormsOS, so skip it.
        wrappers = list(project.Allomorphs.GetAll(entry))[1:]
        assert len(wrappers) == 3
        for w in wrappers:
            assert isinstance(w, LCMObjectWrapper)

        # --- MoveUp: c up 1 -> [a, c, b] ---
        moved = project.Allomorphs.MoveUp(entry, wrappers[2], 1)
        assert moved == 1
        post = forms()
        assert post == ["TEST_449_alt_a", "TEST_449_alt_c", "TEST_449_alt_b"], post
        assert post != pre

        # --- MoveDown: a (now index 0) down 1 -> [c, a, b] ---
        pre = post
        wrappers = list(project.Allomorphs.GetAll(entry))[1:]
        moved = project.Allomorphs.MoveDown(entry, wrappers[0], 1)
        assert moved == 1
        post = forms()
        assert post == ["TEST_449_alt_c", "TEST_449_alt_a", "TEST_449_alt_b"], post
        assert post != pre

        # --- MoveBefore: b before c -> [b, c, a] ---
        pre = post
        wrappers = list(project.Allomorphs.GetAll(entry))[1:]  # c, a, b
        result = project.Allomorphs.MoveBefore(wrappers[2], wrappers[0])
        assert result is True
        post = forms()
        assert post == ["TEST_449_alt_b", "TEST_449_alt_c", "TEST_449_alt_a"], post
        assert post != pre

        # --- MoveAfter: a after b -> [b, a, c] ---
        pre = post
        wrappers = list(project.Allomorphs.GetAll(entry))[1:]  # b, c, a
        result = project.Allomorphs.MoveAfter(wrappers[2], wrappers[0])
        assert result is True
        post = forms()
        assert post == ["TEST_449_alt_b", "TEST_449_alt_a", "TEST_449_alt_c"], post
        assert post != pre

        # --- Swap: b and c -> [c, a, b] ---
        pre = post
        wrappers = list(project.Allomorphs.GetAll(entry))[1:]  # b, a, c
        result = project.Allomorphs.Swap(wrappers[0], wrappers[2])
        assert result is True
        post = forms()
        assert post == ["TEST_449_alt_c", "TEST_449_alt_a", "TEST_449_alt_b"], post
        assert post != pre


class TestLexSenseSetGrammaticalInfoWrapperWriteLive:
    """SetGrammaticalInfo with a wrapper MSA taken from MSAOperations.GetAll()."""

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_set_grammatical_info_via_wrapper_repoints_sense(self, sena3_sandbox):
        from SIL.LCModel import ILexSense

        project = sena3_sandbox

        # Find an entry owning >=2 distinct MSAs, with a sense currently
        # pointed at one of them -- so we can repoint it to the OTHER.
        target_entry = None
        target_sense = None
        old_msa_hvo = None
        new_msa_wrapper = None

        for entry in project.LexEntry.GetAll():
            msas = list(project.MSA.GetAll(entry))
            if len(msas) < 2:
                continue
            for sense in entry.SensesOS:
                if sense.MorphoSyntaxAnalysisRA is None:
                    continue
                current_hvo = sense.MorphoSyntaxAnalysisRA.Hvo
                other = next((m for m in msas if m.lcm_object.Hvo != current_hvo), None)
                if other is not None:
                    target_entry = entry
                    target_sense = sense
                    old_msa_hvo = current_hvo
                    new_msa_wrapper = other
                    break
            if target_sense is not None:
                break

        assert target_sense is not None, (
            "Sena 3 sandbox has no entry with a sense pointed at one of "
            "2+ distinct MSAs on the same entry; cannot verify repoint."
        )
        assert isinstance(new_msa_wrapper, LCMObjectWrapper)

        sense_hvo = target_sense.Hvo
        project.Senses.SetGrammaticalInfo(target_sense, new_msa_wrapper)

        # Re-query the sense fresh from the LCM.
        fresh_sense = ILexSense(project.Object(sense_hvo))
        assert fresh_sense.MorphoSyntaxAnalysisRA is not None
        assert fresh_sense.MorphoSyntaxAnalysisRA.Hvo == new_msa_wrapper.lcm_object.Hvo
        assert fresh_sense.MorphoSyntaxAnalysisRA.Hvo != old_msa_hvo


class TestWfiMorphBundleWrapperWritesLive:
    """SetMorph / SetMSA on a bundle, passing wrapper allomorph/MSA items."""

    @pytest.mark.live_phase("WfiMorphBundleOperations", "modify")
    def test_set_morph_and_set_msa_via_wrapper_repoint_bundle(self, sena3_sandbox):
        from SIL.LCModel import IWfiMorphBundle, IWfiWordformRepository

        project = sena3_sandbox

        wf_repo = project.project.ServiceLocator.GetService(IWfiWordformRepository)
        bundle = None
        for wf in wf_repo.AllInstances():
            for analysis in wf.AnalysesOC:
                for candidate in analysis.MorphBundlesOS:
                    if candidate.MorphRA is not None and candidate.MsaRA is not None:
                        bundle = candidate
                        break
                if bundle is not None:
                    break
            if bundle is not None:
                break

        assert bundle is not None, (
            "Sena 3 sandbox has no analysed wordform with a fully-populated "
            "morph bundle (MorphRA and MsaRA both set); cannot verify."
        )

        bundle_hvo = bundle.Hvo
        pre_morph_hvo = bundle.MorphRA.Hvo
        pre_msa_hvo = bundle.MsaRA.Hvo

        allomorph_wrapper = next(
            a for a in project.Allomorphs.GetAll() if a.lcm_object.Hvo != pre_morph_hvo
        )
        msa_wrapper = next(
            m for m in project.MSA.GetAll() if m.lcm_object.Hvo != pre_msa_hvo
        )
        assert isinstance(allomorph_wrapper, LCMObjectWrapper)
        assert isinstance(msa_wrapper, LCMObjectWrapper)

        project.WfiMorphBundles.SetMorph(bundle, allomorph_wrapper)
        project.WfiMorphBundles.SetMSA(bundle, msa_wrapper)

        # Re-query the bundle fresh from the LCM (not the `bundle` variable
        # we just mutated through).
        fresh_bundle = IWfiMorphBundle(project.Object(bundle_hvo))
        assert fresh_bundle.MorphRA is not None
        assert fresh_bundle.MorphRA.Hvo == allomorph_wrapper.lcm_object.Hvo
        assert fresh_bundle.MorphRA.Hvo != pre_morph_hvo

        assert fresh_bundle.MsaRA is not None
        assert fresh_bundle.MsaRA.Hvo == msa_wrapper.lcm_object.Hvo
        assert fresh_bundle.MsaRA.Hvo != pre_msa_hvo


class TestMSAChangeAffixVariantWrapperWriteLive:
    """MSAOperations.ChangeAffixVariant with a wrapper MSA from MSA.GetAll()."""

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_change_affix_variant_via_wrapper_converts_and_repoints(self, sena3_sandbox):
        from SIL.LCModel import ILexEntry

        project = sena3_sandbox

        infl_msa = None
        for m in project.MSA.GetAll():
            if m.class_type == "MoInflAffMsa":
                owner = ILexEntry(m.lcm_object.Owner)
                if list(owner.SensesOS):
                    infl_msa = m
                    break

        assert infl_msa is not None, (
            "Sena 3 sandbox has no MoInflAffMsa owned by an entry with "
            "senses; cannot verify ChangeAffixVariant."
        )
        assert isinstance(infl_msa, LCMObjectWrapper)

        old_hvo = infl_msa.lcm_object.Hvo
        entry = ILexEntry(infl_msa.lcm_object.Owner)
        entry_hvo = entry.Hvo

        new_msa = project.MSA.ChangeAffixVariant(infl_msa, "deriv")
        assert new_msa.Hvo != old_hvo
        assert new_msa.ClassName == "MoDerivAffMsa"

        # Re-query the entry's MSA collection fresh from the LCM.
        fresh_entry = ILexEntry(project.Object(entry_hvo))
        fresh_msas = list(project.MSA.GetAll(fresh_entry))
        fresh_hvos = {m.lcm_object.Hvo for m in fresh_msas}

        assert new_msa.Hvo in fresh_hvos, "New MoDerivAffMsa not found on re-query"
        assert any(m.class_type == "MoDerivAffMsa" and m.lcm_object.Hvo == new_msa.Hvo for m in fresh_msas)

        # Old MSA should be gone (no sense references it anymore) unless a
        # morph bundle elsewhere still holds it (ChangeAffixVariant's own
        # documented limitation) -- either way it must no longer be the
        # MSA any sense in this entry points at.
        still_pointed_at = any(
            s.MorphoSyntaxAnalysisRA is not None and s.MorphoSyntaxAnalysisRA.Hvo == old_hvo
            for s in fresh_entry.SensesOS
        )
        assert not still_pointed_at, "A sense in the entry still points at the old (pre-conversion) MSA"


def _sena3_phon_rules_present(project):
    return list(project.PhonRules.GetAll())


class TestPhonologicalRuleWrapperWriteLive:
    """
    Create a TEST_ rule in target_sandbox, then round-trip a setter through
    the GetAll() wrapper. Sena 3 has none (cycle 1 skipped this class).
    """

    @pytest.mark.live_phase("PhonologicalRuleOperations", "add")
    def test_create_then_set_name_via_wrapper(self, target_sandbox):
        project = target_sandbox

        raw_rule = project.PhonRules.Create("TEST_449_phon_rule", "initial description")
        raw_hvo = raw_rule.Hvo

        wrapper = next(
            r for r in project.PhonRules.GetAll() if r.lcm_object.Hvo == raw_hvo
        )
        assert isinstance(wrapper, LCMObjectWrapper)
        assert project.PhonRules.GetName(wrapper) == "TEST_449_phon_rule"

        project.PhonRules.SetName(wrapper, "TEST_449_phon_rule_renamed")

        # Re-query via a fresh GetAll(), not the wrapper we just mutated with.
        fresh = next(
            r for r in project.PhonRules.GetAll() if r.lcm_object.Hvo == raw_hvo
        )
        assert project.PhonRules.GetName(fresh) == "TEST_449_phon_rule_renamed"
        assert project.PhonRules.GetName(fresh) != "TEST_449_phon_rule"

    @pytest.mark.live_phase("PhonologicalRuleOperations", "modify")
    def test_set_direction_via_wrapper(self, target_sandbox):
        # NOTE: SetStratum/GetStratum were tried first here but IPhPhonRule
        # (unlike IMoCompoundRule/IMoInflAffixTemplate) has no StratumRA at
        # all -- hasattr guards make both a true no-op regardless of #449,
        # so Direction (which IS a real IPhSegmentRule field) is used
        # instead to exercise the wrapper-unwrap path on a real setter.
        project = target_sandbox

        raw_rule = project.PhonRules.Create("TEST_449_phon_rule_direction")
        raw_hvo = raw_rule.Hvo

        wrapper = next(
            r for r in project.PhonRules.GetAll() if r.lcm_object.Hvo == raw_hvo
        )
        assert isinstance(wrapper, LCMObjectWrapper)

        pre_direction = project.PhonRules.GetDirection(wrapper)
        new_direction = 1 if pre_direction != 1 else 2
        project.PhonRules.SetDirection(wrapper, new_direction)

        fresh = next(
            r for r in project.PhonRules.GetAll() if r.lcm_object.Hvo == raw_hvo
        )
        post_direction = project.PhonRules.GetDirection(fresh)
        assert post_direction == new_direction
        assert post_direction != pre_direction
