#
#   test_issue542_affix_slot_readers_live.py
#
#   Live read-path verification for issue #542, against a write-enabled
#   Sena 3 sandbox (a fresh tempdir copy of the Sena 3 .fwbackup fixture --
#   CLAUDE.md "Live LCM Verification": "Nothing may write to the Target
#   project" per binding user directive; all writes here go to the Sena 3
#   sandbox, never the real Target).
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_542_"


@pytest.mark.live_phase("POSOperations", "read")
def test_slot_readers_round_trip_via_object_and_hvo(sena3_sandbox):
    from SIL.LCModel import IMoInflAffixSlot
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = sena3_sandbox
    assert project.writeEnabled is True

    pos = None
    entry = None
    try:
        pos = project.POS.Create(f"{TEST_PREFIX}pos", "T542")
        slot_required = project.POS.CreateAffixSlot(
            pos, f"{TEST_PREFIX}slot_req", optional=False
        )
        slot_optional = project.POS.CreateAffixSlot(
            pos, f"{TEST_PREFIX}slot_opt", optional=True
        )
        req_hvo = int(slot_required.Hvo)
        opt_hvo = int(slot_optional.Hvo)

        # --- GetSlotName: raw object and HVO agree ---
        assert project.POS.GetSlotName(slot_required) == f"{TEST_PREFIX}slot_req"
        assert project.POS.GetSlotName(req_hvo) == f"{TEST_PREFIX}slot_req"

        # --- IsSlotOptional: matches what CreateAffixSlot wrote ---
        assert project.POS.IsSlotOptional(slot_required) is False
        assert project.POS.IsSlotOptional(slot_optional) is True
        assert project.POS.IsSlotOptional(opt_hvo) is True

        # --- SetSlotName: write, then re-query directly from the LCM ---
        project.POS.SetSlotName(slot_required, f"{TEST_PREFIX}slot_req_renamed")
        fresh_slot = IMoInflAffixSlot(project.Object(req_hvo))
        reread_name = ITsString(
            fresh_slot.Name.get_String(project.project.DefaultAnalWs)
        ).Text
        assert reread_name == f"{TEST_PREFIX}slot_req_renamed"
        assert project.POS.GetSlotName(req_hvo) == f"{TEST_PREFIX}slot_req_renamed"

        # --- SetSlotOptional: write, then re-query directly from the LCM ---
        project.POS.SetSlotOptional(slot_required, True)
        fresh_slot = IMoInflAffixSlot(project.Object(req_hvo))
        assert fresh_slot.Optional is True
        assert project.POS.IsSlotOptional(req_hvo) is True

        project.POS.SetSlotOptional(opt_hvo, False)
        fresh_slot = IMoInflAffixSlot(project.Object(opt_hvo))
        assert fresh_slot.Optional is False
        assert project.POS.IsSlotOptional(slot_optional) is False

        # --- GetAffixesInSlot: create an inflectional-affix MSA filling the slot ---
        entry = project.LexEntry.Create(f"{TEST_PREFIX}prefix", morph_type_name="prefix")
        sense = entry.SensesOS[0]
        infl = project.MSA.CreateInflAff(sense, pos, slots=[slot_required])
        msa_hvo = int(infl.Hvo)

        affixes = project.POS.GetAffixesInSlot(slot_required)
        affix_hvos = {int(a.Hvo) for a in affixes}
        assert affix_hvos == {msa_hvo}

        # Cross-check against the inverse lookup (#543).
        slots_from_msa = project.MSA.GetInflAffMsaSlots(sense)
        assert {int(s.Hvo) for s in slots_from_msa} == {req_hvo}

        # HVO input to GetAffixesInSlot agrees with the object input.
        affixes_via_hvo = project.POS.GetAffixesInSlot(req_hvo)
        assert {int(a.Hvo) for a in affixes_via_hvo} == {msa_hvo}

        # No affixes fill the untouched optional slot.
        assert project.POS.GetAffixesInSlot(slot_optional) == []
    finally:
        if entry is not None:
            project.LexEntry.Delete(entry)
        if pos is not None:
            project.POS.Delete(pos)


@pytest.mark.live_phase("POSOperations", "read")
def test_get_affix_slots_returns_affixslot_wrapper(sena3_sandbox):
    from flexicon.code.Grammar.affix_slot import AffixSlot
    from flexicon.code.Grammar.affix_template import AffixTemplate

    project = sena3_sandbox
    pos = None
    try:
        pos = project.POS.Create(f"{TEST_PREFIX}wrap_pos", "T542W")
        slot = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}wrap_slot", optional=True)

        slots = project.POS.GetAffixSlots(pos)
        assert len(slots) == 1
        wrapped = slots[0]
        assert isinstance(wrapped, AffixSlot)
        assert wrapped.name == f"{TEST_PREFIX}wrap_slot"
        assert wrapped.optional is True
        assert wrapped.affixes == []

        # Backward compat: raw LCM member access still proxies through.
        assert int(wrapped.Hvo) == int(slot.Hvo)
        assert wrapped.Optional is True

        # Wrapper round-trips into AddSlotToTemplate (unwrapped internally).
        template = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}wrap_template"
        )
        project.MorphRules.AddSlotToTemplate(template, wrapped, "prefix")

        wrapped_template = AffixTemplate(template)
        template_slots = wrapped_template.prefix_slots
        assert len(template_slots) == 1
        assert isinstance(template_slots[0], AffixSlot)
        assert template_slots[0].name == f"{TEST_PREFIX}wrap_slot"
    finally:
        if pos is not None:
            project.POS.Delete(pos)


@pytest.mark.live_phase("POSOperations", "add")
def test_create_affix_slot_returns_affixslot_wrapper(sena3_sandbox):
    """
    CreateAffixSlot returns an AffixSlot wrapper (not a raw
    IMoInflAffixSlot), and the wrapper flows straight into
    AddSlotToTemplate and SetInflAffMsaSlots without unwrapping by the
    caller. Every claim here is confirmed by re-querying the LCM after
    the write, not by asserting on the value just passed in.
    """
    from SIL.LCModel import IMoInflAffixTemplate, IPartOfSpeech

    from flexicon.code.Grammar.affix_slot import AffixSlot

    project = sena3_sandbox
    assert project.writeEnabled is True

    pos = None
    entry = None
    try:
        pos = project.POS.Create(f"{TEST_PREFIX}create_pos", "T542C")
        slot = project.POS.CreateAffixSlot(
            pos, f"{TEST_PREFIX}create_slot", optional=True
        )

        # CreateAffixSlot returns an AffixSlot, not a raw IMoInflAffixSlot.
        assert isinstance(slot, AffixSlot)
        assert slot.name == f"{TEST_PREFIX}create_slot"
        assert slot.optional is True
        slot_hvo = int(slot.Hvo)

        # --- Pass the wrapper straight into AddSlotToTemplate ---
        template = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}create_template"
        )
        template_hvo = int(template.Hvo)
        project.MorphRules.AddSlotToTemplate(template, slot, "prefix")

        # Read back the template's prefix slots directly from the LCM
        # (not from the value just passed in).
        pos_hvo = int(pos.Hvo)
        owner = IPartOfSpeech(project.Object(pos_hvo))
        fresh_template = None
        for raw in owner.AffixTemplatesOS:
            if int(raw.Hvo) == template_hvo:
                fresh_template = IMoInflAffixTemplate(raw)
                break
        assert fresh_template is not None
        prefix_hvos = {int(item.Hvo) for item in fresh_template.PrefixSlotsRS}
        assert slot_hvo in prefix_hvos

        # --- Pass the wrapper straight into SetInflAffMsaSlots ---
        entry = project.LexEntry.Create(
            f"{TEST_PREFIX}create_prefix", morph_type_name="prefix"
        )
        sense = entry.SensesOS[0]
        infl = project.MSA.CreateInflAff(sense, pos, slots=[])
        assert infl is not None

        project.MSA.SetInflAffMsaSlots(sense, [slot], replace=True)

        # Read back via GetInflAffMsaSlots -- the LCM, not the input list.
        slots_from_msa = project.MSA.GetInflAffMsaSlots(sense)
        assert {int(s.Hvo) for s in slots_from_msa} == {slot_hvo}
    finally:
        if entry is not None:
            project.LexEntry.Delete(entry)
        if pos is not None:
            project.POS.Delete(pos)


@pytest.mark.live_phase("POSOperations", "read")
def test_bad_slot_input_raises_parameter_error(sena3_sandbox):
    from flexicon.code.FLExProject import FP_ParameterError

    project = sena3_sandbox
    pos = None
    try:
        pos = project.POS.Create(f"{TEST_PREFIX}bad_pos", "T542B")

        with pytest.raises(FP_ParameterError):
            project.POS.GetSlotName(pos)  # a POS is not an affix slot
    finally:
        if pos is not None:
            project.POS.Delete(pos)


@pytest.mark.live_phase("POSOperations", "read")
def test_sena3_affix_slots_are_readable_if_present(sena3_sandbox):
    """
    Read-only sanity check against the Sena 3 sandbox: any pre-existing
    affix slots must be readable through the new wrapper/readers without
    raising.

    Uses the same write-enabled sandbox as the other tests in this file
    (no additional project needs to be opened) but performs no writes of
    its own -- it only reads whatever slots already exist in the fixture
    data.
    """
    project = sena3_sandbox

    found_any = False
    for pos in project.POS.GetAll():
        slots = project.POS.GetAffixSlots(pos)
        for slot in slots:
            found_any = True
            name = slot.name
            assert isinstance(name, str)
            optional = slot.optional
            assert isinstance(optional, bool)
            affixes = project.POS.GetAffixesInSlot(slot)
            assert isinstance(affixes, list)
    # Not asserting found_any is True: Sena 3's slot inventory is data,
    # not a guarantee. This test's value is "no raise while reading
    # every slot that does exist."
    _ = found_any
