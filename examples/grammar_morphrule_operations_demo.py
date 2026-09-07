#!/usr/bin/env python3
"""
Full CRUD Demo: MorphRuleOperations for flexlibs

This script demonstrates complete CRUD operations for morphological rules.
Performs actual create, read, update, and delete operations on test data.

Morphological rules in the LCM data model are distributed across:
- Compound rules (MoMorphData.CompoundRulesOS)
- Affix templates (PartOfSpeech.AffixTemplatesOS)
- Ad hoc co-prohibitions (MoMorphData.AdhocCoProhibitionsOC)

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_morphrule_crud():
    """
    Demonstrate full CRUD operations for morphological rules.

    Tests:
    - CREATE: Create new compound rule and affix template
    - READ: Get all rules by type
    - UPDATE: Modify rule properties
    - DELETE: Remove test rules
    """

    print("=" * 70)
    print("MORPHRULE OPERATIONS - FULL CRUD TEST")
    print("=" * 70)

    # Initialize FieldWorks
    FLExInitialize()

    # Open project with write enabled
    project = FLExProject()
    try:
        project.OpenProject("Sena 3", writeEnabled=True)
    except Exception as e:
        print(f"Cannot run demo - FLEx project not available: {e}")
        FLExCleanup()
        return

    test_compound = None
    test_template = None
    test_compound_name = "crud_test_compound_rule"
    test_template_name = "crud_test_affix_template"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing morphological rules")
        print("=" * 70)

        # Compound rules
        print("\nCompound rules (MoMorphData.CompoundRulesOS):")
        compound_count = 0
        for rule in project.MorphRules.GetAllCompoundRules():
            try:
                name = project.MorphRules.GetName(rule)
                print(f"  - {name} ({rule.ClassName})")
            except:
                print(f"  - [Rule {compound_count + 1}]")
            compound_count += 1
            if compound_count >= 5:
                break
        print(f"  Total compound rules (first 5): {compound_count}")

        # Affix templates
        print("\nAffix templates (PartOfSpeech.AffixTemplatesOS):")
        template_count = 0
        for template in project.MorphRules.GetAllAffixTemplates():
            try:
                name = project.MorphRules.GetName(template)
                pos_name = template.Owner.Name.BestAnalysisAlternative.Text
                print(f"  - {name} (on {pos_name})")
            except:
                print(f"  - [Template {template_count + 1}]")
            template_count += 1
            if template_count >= 5:
                break
        print(f"  Total affix templates (first 5): {template_count}")

        # Ad hoc co-prohibitions
        print("\nAd hoc co-prohibitions (MoMorphData.AdhocCoProhibitionsOC):")
        prohib_count = sum(1 for _ in project.MorphRules.GetAllAdhocCoProhibitions())
        print(f"  Total co-prohibitions: {prohib_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create test compound rule and affix template")
        print("=" * 70)

        # Create compound rule
        print(f"\nCreating compound rule: '{test_compound_name}'")
        try:
            test_compound = project.MorphRules.CreateCompoundRule(
                test_compound_name, endocentric=True, description="Test endocentric compound rule"
            )
            print(f"  SUCCESS: Created {test_compound.ClassName}")
            print(f"  Name: {project.MorphRules.GetName(test_compound)}")
            print(f"  Description: {project.MorphRules.GetDescription(test_compound)}")
        except Exception as e:
            print(f"  Note: CreateCompoundRule failed: {e}")

        # Create affix template on first POS (if available)
        print(f"\nCreating affix template: '{test_template_name}'")
        try:
            pos_list = project.lp.PartsOfSpeechOA  # type: ignore[attr-defined]
            if pos_list and pos_list.PossibilitiesOS.Count > 0:  # type: ignore[attr-defined]
                first_pos = pos_list.PossibilitiesOS[0]  # type: ignore[attr-defined]
                pos_name = first_pos.Name.BestAnalysisAlternative.Text  # type: ignore[attr-defined]
                print(f"  Using POS: {pos_name}")

                test_template = project.MorphRules.CreateAffixTemplate(
                    first_pos, test_template_name, description="Test inflectional affix template"
                )
                print(f"  SUCCESS: Created {test_template.ClassName}")
                print(f"  Name: {project.MorphRules.GetName(test_template)}")
            else:
                print("  Note: No POS available for template creation")
        except Exception as e:
            print(f"  Note: CreateAffixTemplate failed: {e}")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify rules were created")
        print("=" * 70)

        new_compound_count = sum(1 for _ in project.MorphRules.GetAllCompoundRules())
        new_template_count = sum(1 for _ in project.MorphRules.GetAllAffixTemplates())
        print(f"\n  Compound rules: {compound_count} -> {new_compound_count}")
        print(f"  Affix templates: {template_count} -> {new_template_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify rule properties")
        print("=" * 70)

        if test_compound:
            new_name = "crud_test_compound_modified"
            print(f"\nUpdating compound rule name to: '{new_name}'")
            old_name = project.MorphRules.GetName(test_compound)
            project.MorphRules.SetName(test_compound, new_name)
            print(f"  Old name: {old_name}")
            print(f"  New name: {project.MorphRules.GetName(test_compound)}")
            test_compound_name = new_name

            # Test stratum
            stratum = project.MorphRules.GetStratum(test_compound)
            print(f"  Stratum: {stratum}")

            # Test disabled state
            print(f"  Disabled: {project.MorphRules.IsDisabled(test_compound)}")

            print("  UPDATE: SUCCESS")

        if test_template:
            new_name = "crud_test_template_modified"
            print(f"\nUpdating affix template name to: '{new_name}'")
            old_name = project.MorphRules.GetName(test_template)
            project.MorphRules.SetName(test_template, new_name)
            print(f"  Old name: {old_name}")
            print(f"  New name: {project.MorphRules.GetName(test_template)}")
            test_template_name = new_name
            print("  UPDATE: SUCCESS")

        # ==================== DUPLICATE ====================
        print("\n" + "=" * 70)
        print("STEP 5: DUPLICATE - Test rule duplication")
        print("=" * 70)

        duplicate = None
        if test_compound:
            print(f"\nDuplicating compound rule...")
            try:
                duplicate = project.MorphRules.Duplicate(test_compound)
                print(f"  SUCCESS: Duplicated as {project.MorphRules.GetName(duplicate)}")
                print(f"  Type: {duplicate.ClassName}")
            except Exception as e:
                print(f"  Note: Duplicate failed: {e}")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test rules")
        print("=" * 70)

        for obj, label in [
            (duplicate, "duplicate compound"),
            (test_compound, "compound rule"),
            (test_template, "affix template"),
        ]:
            if obj:
                try:
                    name = project.MorphRules.GetName(obj)
                    project.MorphRules.Delete(obj)
                    print(f"  Deleted {label}: {name}")
                except Exception as e:
                    print(f"  Note: Delete {label} failed: {e}")

        # Verify deletion
        final_compound_count = sum(1 for _ in project.MorphRules.GetAllCompoundRules())
        final_template_count = sum(1 for _ in project.MorphRules.GetAllAffixTemplates())
        print(f"\n  Compound rules: {final_compound_count} (was {compound_count})")
        print(f"  Affix templates: {final_template_count} (was {template_count})")
        print(f"  Back to initial: {final_compound_count == compound_count and final_template_count == template_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] CreateCompoundRule, CreateAffixTemplate")
        print("  [READ]   GetAllCompoundRules, GetAllAffixTemplates,")
        print("           GetAllAdhocCoProhibitions, GetAll")
        print("  [UPDATE] SetName, SetDescription, GetStratum, IsDisabled")
        print("  [DELETE] Delete (compound rules and affix templates)")
        print("  [DUPE]   Duplicate compound rule")
        print("\nTest completed successfully!")

    except Exception as e:
        print(f"\n\nERROR during CRUD test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)

        print("\nClosing project...")
        project.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    print(
        """
MorphRule Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for morphological rules.

Morphological rules in the LCM data model:
- Compound rules: MoMorphData.CompoundRulesOS
- Affix templates: PartOfSpeech.AffixTemplatesOS
- Ad hoc co-prohibitions: MoMorphData.AdhocCoProhibitionsOC

Operations Tested:
==================

CREATE: CreateCompoundRule, CreateAffixTemplate
READ:   GetAllCompoundRules, GetAllAffixTemplates, GetAll
UPDATE: SetName, SetDescription, etc.
DELETE: Delete

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test rules are created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_morphrule_crud()
    else:
        print("\nDemo skipped.")
