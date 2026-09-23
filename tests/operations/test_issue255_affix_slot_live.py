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
_MEASUREMENTS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "specs"
    / "255-affix-slot"
    / "evidence"
    / "_live_measurements.json"
)


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
