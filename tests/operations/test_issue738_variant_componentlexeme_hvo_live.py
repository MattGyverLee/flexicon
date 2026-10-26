#
#   test_issue738_variant_componentlexeme_hvo_live.py
#
#   Live verification for issue #738 Variant ComponentLexemesRS HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_738_"


def _first_variant_type(project):
    for vtype in project.Variants.GetAllTypes():
        return vtype
    return None


def _entry_with_lexeme_form(project):
    for entry in project.LexEntry.GetAll():
        if entry.LexemeFormOA is not None:
            return entry
    return None


def _distinct_component_entry(project, owner_entry):
    for entry in project.LexEntry.GetAll():
        if entry.Hvo != owner_entry.Hvo and entry.LexemeFormOA is not None:
            return entry
    return None


@pytest.mark.requires_live_project
class TestIssue738VariantComponentLexemesRsHvoLive:
    """Add/RemoveComponentLexeme must not rely on Python proxy identity in ComponentLexemesRS."""

    @pytest.mark.live_phase("VariantOperations", "modify")
    def test_remove_component_via_bare_object_view(self, target_sandbox):
        from SIL.LCModel.Core.KernelInterfaces import ITsString
        from SIL.LCModel.Core.Text import TsStringUtils

        project = target_sandbox
        owner = _entry_with_lexeme_form(project)
        component = _distinct_component_entry(project, owner) if owner else None
        vtype = _first_variant_type(project)
        if owner is None or component is None or vtype is None:
            pytest.skip("Target lacks entries with lexeme forms or variant types")

        ws = project.project.DefaultVernWs
        original_form_text = (
            ITsString(owner.LexemeFormOA.Form.get_String(ws)).Text or ""
        )

        variant_ref = None
        try:
            variant_ref = project.Variants.Create(
                owner, f"{TEST_PREFIX}variant_remove", vtype
            )
            project.Variants.AddComponentLexeme(variant_ref, component)
            assert len(project.Variants.GetComponentLexemes(variant_ref)) == 1

            bare_component = project.Object(component.Hvo)
            project.Variants.RemoveComponentLexeme(variant_ref, bare_component)
            assert len(project.Variants.GetComponentLexemes(variant_ref)) == 0
        finally:
            if variant_ref is not None:
                project.Variants.Delete(variant_ref)
            restored = TsStringUtils.MakeString(original_form_text, ws)
            with project.UndoableOperation("test cleanup: restore lexeme form #738"):
                owner.LexemeFormOA.Form.set_String(ws, restored)

    @pytest.mark.live_phase("VariantOperations", "modify")
    def test_add_component_skips_duplicate_for_bare_object_view(self, target_sandbox):
        from SIL.LCModel.Core.KernelInterfaces import ITsString
        from SIL.LCModel.Core.Text import TsStringUtils

        project = target_sandbox
        owner = _entry_with_lexeme_form(project)
        component = _distinct_component_entry(project, owner) if owner else None
        vtype = _first_variant_type(project)
        if owner is None or component is None or vtype is None:
            pytest.skip("Target lacks entries with lexeme forms or variant types")

        ws = project.project.DefaultVernWs
        original_form_text = (
            ITsString(owner.LexemeFormOA.Form.get_String(ws)).Text or ""
        )

        variant_ref = None
        try:
            variant_ref = project.Variants.Create(
                owner, f"{TEST_PREFIX}variant_add_dup", vtype
            )
            project.Variants.AddComponentLexeme(variant_ref, component)
            assert len(project.Variants.GetComponentLexemes(variant_ref)) == 1

            bare_component = project.Object(component.Hvo)
            project.Variants.AddComponentLexeme(variant_ref, bare_component)
            assert len(project.Variants.GetComponentLexemes(variant_ref)) == 1
        finally:
            if variant_ref is not None:
                project.Variants.Delete(variant_ref)
            restored = TsStringUtils.MakeString(original_form_text, ws)
            with project.UndoableOperation("test cleanup: restore lexeme form #738 dup"):
                owner.LexemeFormOA.Form.set_String(ws, restored)
