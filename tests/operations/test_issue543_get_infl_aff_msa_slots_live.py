#
#   test_issue543_get_infl_aff_msa_slots_live.py
#
#   Live read-path verification for issue #543 (target_sandbox).
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_543_"


@pytest.mark.live_phase("MSAOperations", "read")
def test_get_infl_aff_msa_slots_matches_slots_rc(target_sandbox):
    from SIL.LCModel import IMoInflAffMsa, IMoInflAffixSlot

    project = target_sandbox
    assert project.writeEnabled is True

    pos = project.POS.Create(f"{TEST_PREFIX}pos", "T543")
    slot_a = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}slot_a")
    slot_b = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}slot_b")

    entry = project.LexEntry.Create(f"{TEST_PREFIX}prefix", morph_type_name="prefix")
    sense = entry.SensesOS[0]

    infl = project.MSA.CreateInflAff(sense, pos, slots=[slot_a])
    msa_hvo = int(infl.Hvo)

    project.MSA.SetInflAffMsaSlots(sense, [slot_b], replace=True)
    project.MSA.SetInflAffMsaSlots(sense, [slot_a], replace=False)

    from_sense = project.MSA.GetInflAffMsaSlots(sense)
    from_msa = project.MSA.GetInflAffMsaSlots(msa_hvo)

    fresh = IMoInflAffMsa(project.Object(msa_hvo))
    expected_hvos = [int(s.Hvo) for s in fresh.SlotsRC]

    assert [int(s.Hvo) for s in from_sense] == expected_hvos
    assert [int(s.Hvo) for s in from_msa] == expected_hvos
    assert set(expected_hvos) == {int(slot_a.Hvo), int(slot_b.Hvo)}

    for item in from_sense:
        IMoInflAffixSlot(item)

    project.LexEntry.Delete(entry)
    project.POS.Delete(pos)


@pytest.mark.live_phase("MSAOperations", "read")
def test_get_infl_aff_msa_slots_empty_for_stem_msa(target_sandbox):
    project = target_sandbox

    pos = project.POS.Create(f"{TEST_PREFIX}stem_pos", "T543B")
    entry = project.LexEntry.Create(f"{TEST_PREFIX}stem", morph_type_name="stem")
    sense = entry.SensesOS[0]

    project.MSA.CreateStem(sense, pos)
    assert project.MSA.GetInflAffMsaSlots(sense) == []

    project.LexEntry.Delete(entry)
    project.POS.Delete(pos)
