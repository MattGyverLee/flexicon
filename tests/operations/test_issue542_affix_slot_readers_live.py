#
#   test_issue542_affix_slot_readers_live.py
#
#   Live read-path verification for issue #542, against the real
#   in-place 'Target' project (no *.fwbackup fixture is present on this
#   runner, so target_sandbox/sena3_sandbox are unavailable; target_project
#   is equally sanctioned for in-place writes -- CLAUDE.md "Live LCM
#   Verification").
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_542_"


@pytest.mark.live_phase("POSOperations", "read")
def test_slot_readers_round_trip_via_object_and_hvo(target_project):
    from SIL.LCModel import IMoInflAffixSlot
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = target_project
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
def test_get_affix_slots_returns_affixslot_wrapper(target_project):
    from flexicon.code.Grammar.affix_slot import AffixSlot
    from flexicon.code.Grammar.affix_template import AffixTemplate

    project = target_project
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


@pytest.mark.live_phase("POSOperations", "read")
def test_bad_slot_input_raises_parameter_error(target_project):
    from flexicon.code.FLExProject import FP_ParameterError

    project = target_project
    pos = None
    try:
        pos = project.POS.Create(f"{TEST_PREFIX}bad_pos", "T542B")

        with pytest.raises(FP_ParameterError):
            project.POS.GetSlotName(pos)  # a POS is not an affix slot
    finally:
        if pos is not None:
            project.POS.Delete(pos)


@pytest.mark.live_phase("POSOperations", "read")
def test_sena3_affix_slots_are_readable_if_present():
    """
    Read-only sanity check against Sena 3: any pre-existing affix slots
    must be readable through the new wrapper/readers without raising.

    Reads are unrestricted (CLAUDE.md): Sena 3 is opened directly,
    read-only, by name -- no sandbox/backup fixture required.
    """
    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    try:
        project.OpenProject("Sena 3", writeEnabled=False)
    except Exception as exc:
        pytest.skip(f"Sena 3 project not available on this runner: {exc}")

    try:
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
    finally:
        project.CloseProject()
