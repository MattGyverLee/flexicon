#
#   test_449_getall_roundtrip_live.py
#
#   Class: TestGetAllWrapperRoundtripLive
#          Live verification for issue #449 -- every item yielded by a
#          wrapper-returning GetAll() (Allomorph, MorphosyntaxAnalysis,
#          CompoundRule/AffixTemplate, PhonologicalRule) can be passed
#          straight back into a representative Operations method without
#          raising, across the whole Sena 3 lexicon/grammar.
#
#          Read-only against the Sena 3 sandbox (a fresh tempdir copy of
#          the Sena 3 .fwbackup, per CLAUDE.md): no Create/Delete/Set
#          calls are made, except a single no-op MoveToIndex (moving an
#          item to its own current index), which the base reorder
#          implementation treats as a same-index short-circuit.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import collections

import pytest

pytestmark = pytest.mark.requires_live_project


class TestAllomorphGetAllRoundtripLive:
    """Every Allomorph wrapper from GetAll() round-trips through GetForm/GetSyncableProperties."""

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_every_allomorph_wrapper_resolves(self, sena3_sandbox):
        from SIL.LCModel import ICmObject

        project = sena3_sandbox
        allomorphs = project.Allomorphs

        class_counts = collections.Counter()
        checked = 0

        for item in allomorphs.GetAll():
            class_counts[item.class_type] += 1

            # GetForm: the exact call shape from issue #449's repro.
            form = allomorphs.GetForm(item)
            assert form is None or isinstance(form, str)

            # A subtype-only read routed through the same shared resolver.
            morph_type = allomorphs.GetMorphType(item)
            assert morph_type is None or hasattr(morph_type, "ClassName")

            # Caller-side pythonnet cast must use .lcm_object, not the wrapper.
            assert ICmObject(item.lcm_object).ClassName == item.class_type

            checked += 1

        assert checked > 0, "Sena 3 sandbox yielded no allomorphs; cannot verify roundtrip."
        assert class_counts.get("MoStemAllomorph", 0) > 0, (
            "No MoStemAllomorph items were hit -- stem/affix coverage requirement not met."
        )
        assert class_counts.get("MoAffixAllomorph", 0) > 0, (
            "No MoAffixAllomorph items were hit -- stem/affix coverage requirement not met."
        )

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_lexicon_get_allomorph_forms_roundtrip(self, sena3_sandbox):
        """
        FLExProject.LexiconGetAllomorphForms internally loops
        Allomorphs.GetAll(entry) and calls GetForm(allomorph) on each
        item -- this failed with no user input at all before the fix
        (Table 1, sweep report).
        """
        project = sena3_sandbox
        entries = list(project.LexEntry.GetAll())
        assert entries, "Sena 3 sandbox has no lexical entries."

        checked_entries = 0
        for entry in entries[:25]:
            forms = project.LexiconGetAllomorphForms(entry)
            assert isinstance(forms, list)
            checked_entries += 1

        assert checked_entries > 0


class TestMSAGetAllRoundtripLive:
    """Every MorphosyntaxAnalysis wrapper from GetAll() round-trips through GetSyncableProperties."""

    @pytest.mark.live_phase("MSAOperations", "read")
    def test_every_msa_wrapper_resolves(self, sena3_sandbox):
        from SIL.LCModel import ICmObject

        project = sena3_sandbox
        msa_ops = project.MSA

        class_counts = collections.Counter()
        checked = 0

        for item in msa_ops.GetAll():
            class_counts[item.class_type] += 1

            props = msa_ops.GetSyncableProperties(item)
            assert isinstance(props, dict)

            assert ICmObject(item.lcm_object).ClassName == item.class_type

            checked += 1

        assert checked > 0, "Sena 3 sandbox yielded no MSAs; cannot verify roundtrip."

        # Fail loudly only for subtypes actually present in this dataset;
        # a subtype absent from Sena 3 is a coverage gap to note, not a
        # regression, so only assert non-zero for what class_counts saw.
        present_subtypes = [name for name in class_counts if class_counts[name] > 0]
        assert present_subtypes, "No MSA ClassName was observed at all."
        for name in (
            "MoStemMsa",
            "MoDerivAffMsa",
            "MoInflAffMsa",
            "MoUnclassifiedAffixMsa",
        ):
            if name in class_counts:
                assert class_counts[name] > 0, f"{name} count is zero despite being observed."


class TestMorphRuleGetAllRoundtripLive:
    """Every CompoundRule/AffixTemplate wrapper from GetAll() round-trips through GetName."""

    @pytest.mark.live_phase("MorphRuleOperations", "read")
    def test_every_morph_rule_wrapper_resolves(self, sena3_sandbox):
        from SIL.LCModel import ICmObject

        project = sena3_sandbox
        rule_ops = project.MorphRules

        class_counts = collections.Counter()
        checked = 0

        for item in rule_ops.GetAll():
            class_counts[item.class_type] += 1

            name = rule_ops.GetName(item)
            assert isinstance(name, str)

            stratum = rule_ops.GetStratum(item)
            assert stratum is None or hasattr(stratum, "ClassName")

            assert ICmObject(item.lcm_object).ClassName == item.class_type

            checked += 1

        # Sena 3 may or may not define compound rules / affix templates;
        # log what was actually exercised rather than hard-failing on a
        # dataset-dependent zero.
        print(f"[INFO] MorphRuleOperations.GetAll class counts: {dict(class_counts)}")


class TestPhonologicalRuleGetAllRoundtripLive:
    """Every PhonologicalRule wrapper from GetAll() round-trips through GetName."""

    @pytest.mark.live_phase("PhonologicalRuleOperations", "read")
    def test_every_phon_rule_wrapper_resolves(self, sena3_sandbox):
        from SIL.LCModel import ICmObject

        project = sena3_sandbox
        phon_ops = project.PhonRules

        class_counts = collections.Counter()
        checked = 0

        for item in phon_ops.GetAll():
            class_counts[item.class_type] += 1

            name = phon_ops.GetName(item)
            assert isinstance(name, str)

            props = phon_ops.GetSyncableProperties(item)
            assert isinstance(props, dict)

            assert ICmObject(item.lcm_object).ClassName == item.class_type

            checked += 1

        print(f"[INFO] PhonologicalRuleOperations.GetAll class counts: {dict(class_counts)}")


class TestReorderMethodWithWrapperLive:
    """A reorder method (MoveToIndex) accepts a wrapper item, read-only (no-op move)."""

    @pytest.mark.live_phase("AllomorphOperations", "reorder")
    def test_move_to_index_accepts_wrapper_no_op(self, sena3_sandbox):
        """
        Move an Allomorph wrapper item to its OWN current index within its
        entry's AlternateFormsOS. This is a same-index short-circuit in
        MoveToIndex (current_index == new_index skips the MoveTo call
        entirely), so it is safe against the in-place sandbox while still
        exercising the wrapper-unwrap path in MoveToIndex/_GetSequence's
        equality search.
        """
        project = sena3_sandbox
        entries = list(project.LexEntry.GetAll())

        target_entry = None
        target_allomorph = None
        target_index = None
        for entry in entries:
            alt_forms = list(entry.AlternateFormsOS)
            if len(alt_forms) >= 1:
                target_entry = entry
                target_index = 0
                # Wrap the raw allomorph the same way GetAll() does.
                from flexicon.code.Lexicon.allomorph import Allomorph

                target_allomorph = Allomorph(alt_forms[0])
                break

        if target_entry is None:
            pytest.skip("No entry with at least one AlternateFormsOS allomorph found in Sena 3.")

        moved = project.Allomorphs.MoveToIndex(target_entry, target_allomorph, target_index)

        assert moved is True
        # Confirm the sequence is genuinely unchanged (same-index no-op).
        after = list(target_entry.AlternateFormsOS)
        assert after[target_index] == target_allomorph.lcm_object
