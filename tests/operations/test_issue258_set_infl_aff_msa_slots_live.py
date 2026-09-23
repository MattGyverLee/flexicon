#
#   test_issue258_set_infl_aff_msa_slots_live.py
#
#   Live write-path verification for issue #258 (target_sandbox).
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_258_"


@pytest.mark.live_phase("MSAOperations", "modify")
def test_set_infl_aff_msa_slots_replace_and_append(target_sandbox):
    from SIL.LCModel import IMoInflAffMsa, IMoInflAffixSlot

    project = target_sandbox
    assert project.writeEnabled is True

    pos = project.POS.Create(f"{TEST_PREFIX}pos", "T58")
    slot_a = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}slot_a")
    slot_b = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}slot_b")

    entry = project.LexEntry.Create(f"{TEST_PREFIX}prefix", morph_type_name="prefix")
    sense = entry.SensesOS[0]

    infl = project.MSA.CreateInflAff(sense, pos, slots=[slot_a])
    msa_hvo = infl.Hvo

    project.MSA.SetInflAffMsaSlots(sense, [slot_b], replace=True)

    fresh = IMoInflAffMsa(project.Object(msa_hvo))
    hvos_after_replace = {int(s.Hvo) for s in fresh.SlotsRC}
    assert hvos_after_replace == {int(slot_b.Hvo)}

    project.MSA.SetInflAffMsaSlots(sense, [slot_a], replace=False)

    fresh = IMoInflAffMsa(project.Object(msa_hvo))
    hvos_after_append = {int(s.Hvo) for s in fresh.SlotsRC}
    assert hvos_after_append == {int(slot_a.Hvo), int(slot_b.Hvo)}

    for item in fresh.SlotsRC:
        IMoInflAffixSlot(item)

    project.LexEntry.Delete(entry)
    project.POS.Delete(pos)
