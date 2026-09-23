#
#   test_issue255_affix_slot_live.py
#
#   Live write-path verification for issue #255 against a tempdir copy
#   of the Target project (target_sandbox). Nothing is written to the
#   user's real Target.
#
#   Copy of the structure in test_target_live_smoke.py: pytestmark
#   requires_live_project, TEST_ prefix, sandbox fixture.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import pathlib

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"
_EVIDENCE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "specs"
    / "255-affix-slot"
    / "evidence"
)
_MEASUREMENTS = _EVIDENCE / "_live_measurements.json"
_CYCLE3_MEASUREMENTS = _EVIDENCE / "_cycle3_measurements.json"


def _template_on(project, pos_hvo, template_hvo):
    """Re-fetch a template from its owning POS. Not the object just returned."""
    from SIL.LCModel import IMoInflAffixTemplate, IPartOfSpeech

    owner = IPartOfSpeech(project.Object(pos_hvo))
    for raw in owner.AffixTemplatesOS:
        if raw.Hvo == template_hvo:
            return IMoInflAffixTemplate(raw)
    return None


def _side_hvos(template, side_name):
    sequence = getattr(template, side_name)
    return [int(item.Hvo) for item in sequence]


def _analysis_text(multistring, ws_handle):
    """Read one writing-system alternative back off the LCM object."""
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    text = ITsString(multistring.get_String(ws_handle)).Text
    return text or ""


class TestIssue255AffixSlotLive:
    """Create a slot, read it back, and insert it on a template side."""

    @pytest.mark.live_phase("POSOperations", "add")
    def test_create_slot_and_add_to_prefix_side(self, target_sandbox):
        import clr
        from SIL.LCModel import (
            IMoInflAffixSlot,
            IMoInflAffixTemplate,
            IPartOfSpeech,
        )

        from flexicon.code.FLExProject import FP_ParameterError

        project = target_sandbox
        assert project.writeEnabled is True
        assert getattr(project, "project", None) is not None

        record = {"status": "fail"}
        try:
            poses = list(project.POS.GetAll())
            created_pos = False
            if not poses:
                pos = project.POS.Create(f"{TEST_PREFIX}Category", "TC")
                created_pos = True
            else:
                pos = poses[0]
            pos_hvo = pos.Hvo

            pre_slot_count = len(list(project.POS.GetAffixSlots(pos)))
            record["pre_slot_count"] = pre_slot_count
            record["created_pos"] = created_pos
            record["pos_hvo"] = pos_hvo

            slot_name = f"{TEST_PREFIX}PossConcord"
            created = project.POS.CreateAffixSlot(pos, slot_name, optional=False)
            assert created is not None
            slot_hvo = created.Hvo

            ws = project.project.DefaultAnalWs
            reread = [
                IMoInflAffixSlot(item)
                for item in project.POS.GetAffixSlots(pos)
                if item.Hvo == slot_hvo
            ]
            assert len(reread) == 1, (
                f"GetAffixSlots did not return the new slot HVO {slot_hvo}"
            )
            fresh_slot = reread[0]
            read_name = _analysis_text(fresh_slot.Name, ws)
            read_optional = fresh_slot.Optional
            assert read_name == slot_name, (
                f"Name read back from the LCM was {read_name!r}, "
                f"expected {slot_name!r}"
            )
            assert read_optional == False  # noqa: E712  -- LCM bool, not identity

            runtime = fresh_slot.GetType()
            bool_props = sorted(
                prop.Name
                for prop in runtime.GetProperties()
                if prop.PropertyType.Name == "Boolean"
            )
            assert "Optional" in bool_props

            template_name = f"{TEST_PREFIX}Possessive"
            template = project.MorphRules.CreateAffixTemplate(pos, template_name)
            template_hvo = template.Hvo

            owner = IPartOfSpeech(project.Object(pos_hvo))
            pre_template = None
            for raw in owner.AffixTemplatesOS:
                if raw.Hvo == template_hvo:
                    pre_template = IMoInflAffixTemplate(raw)
                    break
            assert pre_template is not None
            pre_side_count = pre_template.PrefixSlotsRS.Count
            record["pre_side"] = "prefix"
            record["pre_side_count"] = int(pre_side_count)

            returned = project.MorphRules.AddSlotToTemplate(
                template, created, "Prefix"
            )
            assert returned.Hvo == template_hvo

            owner = IPartOfSpeech(project.Object(pos_hvo))
            post_template = None
            for raw in owner.AffixTemplatesOS:
                if raw.Hvo == template_hvo:
                    post_template = IMoInflAffixTemplate(raw)
                    break
            assert post_template is not None
            post_hvos = [item.Hvo for item in post_template.PrefixSlotsRS]
            assert slot_hvo in post_hvos
            assert int(post_template.PrefixSlotsRS.Count) == int(pre_side_count) + 1

            seq_type = post_template.PrefixSlotsRS.GetType()
            seq_methods = sorted(
                {
                    method.Name
                    for method in seq_type.GetMethods()
                    if method.Name in ("Add", "Insert", "InsertAt")
                }
            )
            record["sequence_methods"] = seq_methods

            second = project.POS.CreateAffixSlot(
                pos, f"{TEST_PREFIX}NounClass", optional=True
            )
            project.MorphRules.AddSlotToTemplate(
                post_template, second, "prefix", index=0
            )
            owner = IPartOfSpeech(project.Object(pos_hvo))
            ordered = None
            for raw in owner.AffixTemplatesOS:
                if raw.Hvo == template_hvo:
                    ordered = IMoInflAffixTemplate(raw)
                    break
            ordered_hvos = [item.Hvo for item in ordered.PrefixSlotsRS]
            assert ordered_hvos[0] == second.Hvo
            assert slot_hvo in ordered_hvos

            with pytest.raises(FP_ParameterError):
                project.MorphRules.AddSlotToTemplate(
                    ordered, created, "prefix", index=99
                )
            owner = IPartOfSpeech(project.Object(pos_hvo))
            after_reject = None
            for raw in owner.AffixTemplatesOS:
                if raw.Hvo == template_hvo:
                    after_reject = IMoInflAffixTemplate(raw)
                    break
            assert [item.Hvo for item in after_reject.PrefixSlotsRS] == ordered_hvos

            iface = clr.GetClrType(IMoInflAffixSlot)
            iface_bools = sorted(
                prop.Name
                for prop in iface.GetProperties()
                if prop.PropertyType.Name == "Boolean"
            )

            record.update(
                {
                    "status": "pass",
                    "slot_name_read_back": read_name,
                    "optional_read_back": bool(read_optional),
                    "slot_hvo": slot_hvo,
                    "post_slot_count": len(list(project.POS.GetAffixSlots(pos))),
                    "post_side_count": int(after_reject.PrefixSlotsRS.Count),
                    "post_side_hvos": list(ordered_hvos),
                    "concrete_bool_properties": bool_props,
                    "interface_bool_properties": iface_bools,
                    "second_slot_hvo": second.Hvo,
                    "second_optional_read_back": bool(
                        IMoInflAffixSlot(second).Optional
                    ),
                }
            )
        finally:
            _MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
            _MEASUREMENTS.write_text(
                json.dumps(record, indent=2), encoding="utf-8"
            )

    @pytest.mark.live_phase("POSOperations", "add")
    def test_ancestor_slot_accepted_descendant_slot_rejected(self, target_sandbox):
        """Obligatory default, ancestor slot accepted, descendant slot rejected."""
        import clr
        from SIL.LCModel import IMoInflAffixSlot, IPartOfSpeech

        from flexicon.code.FLExProject import FP_ParameterError

        project = target_sandbox
        assert project.writeEnabled is True

        record = {"status": "fail"}
        try:
            iface = clr.GetClrType(IPartOfSpeech)
            all_affix = iface.GetProperty("AllAffixSlots")
            assert all_affix is not None
            record["all_affix_slots_property"] = all_affix.Name
            record["all_affix_slots_type"] = all_affix.PropertyType.FullName

            parent = project.POS.Create(f"{TEST_PREFIX}Cycle3Parent", "T3P")
            child = project.POS.AddSubcategory(
                parent, f"{TEST_PREFIX}Cycle3Child", "T3C"
            )
            parent_hvo = int(parent.Hvo)
            child_hvo = int(child.Hvo)
            record["parent_hvo"] = parent_hvo
            record["child_hvo"] = child_hvo

            parent_fresh = IPartOfSpeech(project.Object(parent_hvo))
            pre_parent_slots = [
                int(item.Hvo) for item in project.POS.GetAffixSlots(parent_fresh)
            ]
            record["pre_parent_slot_hvos"] = pre_parent_slots

            slot_name = f"{TEST_PREFIX}Cycle3Obligatory"
            created = project.POS.CreateAffixSlot(parent, slot_name)
            parent_slot_hvo = int(created.Hvo)

            ws = project.project.DefaultAnalWs
            reread = [
                IMoInflAffixSlot(item)
                for item in project.POS.GetAffixSlots(
                    IPartOfSpeech(project.Object(parent_hvo))
                )
                if int(item.Hvo) == parent_slot_hvo
            ]
            assert len(reread) == 1
            fresh_slot = reread[0]
            read_optional = fresh_slot.Optional
            assert _analysis_text(fresh_slot.Name, ws) == slot_name
            assert read_optional == False  # noqa: E712  -- LCM bool, not identity
            record["parent_slot_hvo"] = parent_slot_hvo
            record["optional_read_back"] = bool(read_optional)

            child_pos = IPartOfSpeech(project.Object(child_hvo))
            child_visible = [int(item.Hvo) for item in child_pos.AllAffixSlots]
            record["child_all_affix_slots_before"] = child_visible
            assert parent_slot_hvo in child_visible

            child_template = project.MorphRules.CreateAffixTemplate(
                child, f"{TEST_PREFIX}Cycle3ChildTemplate"
            )
            child_template_hvo = int(child_template.Hvo)
            pre_child_side = _side_hvos(
                _template_on(project, child_hvo, child_template_hvo),
                "PrefixSlotsRS",
            )
            record["pre_child_prefix_hvos"] = pre_child_side

            project.MorphRules.AddSlotToTemplate(
                child_template, created, "prefix"
            )
            post_child = _template_on(project, child_hvo, child_template_hvo)
            post_child_side = _side_hvos(post_child, "PrefixSlotsRS")
            record["post_child_prefix_hvos"] = post_child_side
            assert parent_slot_hvo in post_child_side

            child_slot = project.POS.CreateAffixSlot(
                child, f"{TEST_PREFIX}Cycle3ChildSlot"
            )
            child_slot_hvo = int(child_slot.Hvo)
            parent_pos = IPartOfSpeech(project.Object(parent_hvo))
            parent_visible = [int(item.Hvo) for item in parent_pos.AllAffixSlots]
            record["child_slot_hvo"] = child_slot_hvo
            record["parent_all_affix_slots"] = parent_visible
            assert child_slot_hvo not in parent_visible

            parent_template = project.MorphRules.CreateAffixTemplate(
                parent, f"{TEST_PREFIX}Cycle3ParentTemplate"
            )
            parent_template_hvo = int(parent_template.Hvo)
            pre_parent_side = _side_hvos(
                _template_on(project, parent_hvo, parent_template_hvo),
                "PrefixSlotsRS",
            )
            record["pre_parent_prefix_hvos"] = pre_parent_side

            with pytest.raises(FP_ParameterError):
                project.MorphRules.AddSlotToTemplate(
                    parent_template, child_slot, "prefix"
                )

            post_parent_side = _side_hvos(
                _template_on(project, parent_hvo, parent_template_hvo),
                "PrefixSlotsRS",
            )
            record["post_parent_prefix_hvos"] = post_parent_side
            assert post_parent_side == pre_parent_side

            record["status"] = "pass"
        finally:
            _CYCLE3_MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
            _CYCLE3_MEASUREMENTS.write_text(
                json.dumps(record, indent=2), encoding="utf-8"
            )
