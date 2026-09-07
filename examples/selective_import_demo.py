"""
Selective Import Demo - Linguistic Workflow

Demonstrates the CORRECT way to import linguistic data:
1. Selective one-way import (not bidirectional sync)
2. Date-based filtering (new objects only)
3. Reference validation (prevent orphans)
4. Safety-first approach

This matches the actual linguist use case:
"Back up project → test changes → import new allomorphs to stable"

Author: FlexTools Development Team
Date: 2025-11-27
"""

from datetime import datetime
from flexicon.sync import SelectiveImport, ValidationSeverity


def demo_linguist_workflow():
    """
    Demonstrate the actual linguistic workflow.

    Scenario:
    - Linguist backs up StableProject to test new phonology rules
    - Works in GrammarTest, creates new allomorphs
    - Wants to import ONLY the new allomorphs back to StableProject
    - Never touch existing stable data
    """
    print("=" * 60)
    print("LINGUISTIC WORKFLOW: Selective Import")
    print("=" * 60)
    print()

    # Assume user has:
    # 1. Backed up StableProject → GrammarTest at some point
    # 2. Worked in GrammarTest, adding new allomorphs
    # 3. Now wants to import new allomorphs back

    # Simulated backup timestamp
    backup_time = datetime(2025, 11, 1, 10, 0, 0)
    print(f"📅 Project backed up at: {backup_time}")
    print(f"📝 Changes made in GrammarTest after backup")
    print(f"✅ Grammar tests passed - ready to import")
    print()

    # Open projects (FlexTools provides these)
    # stable_project = flextools.OpenProject("StableProject", writeEnabled=True)
    # test_project = flextools.OpenProject("GrammarTest", writeEnabled=False)

    print("⚠️  SAFETY NOTES:")
    print("   - This is ONE-WAY import (test → stable)")
    print("   - Will NOT overwrite existing stable data")
    print("   - Only imports objects created after backup")
    print("   - Validates references before import")
    print()

    # For demo, we'll show the code pattern
    print("CODE PATTERN:")
    print("-" * 60)
    print(
        """
    from flexicon.sync import SelectiveImport
    from datetime import datetime

    # Initialize importer
    importer = SelectiveImport(
        source_project=test_project,      # Where you made changes
        target_project=stable_project     # Where to import to
    )

    # Import ONLY new allomorphs
    result = importer.import_new_objects(
        object_type="Allomorph",
        created_after=backup_time,        # Only new objects
        validate_references=True,         # Check for orphans
        dry_run=True                      # Safe preview first!
    )

    # Review results
    print(result.summary())

    # If dry run looks good, do actual import
    if result.success and input("Proceed? (y/n): ") == 'y':
        result_real = importer.import_new_objects(
            object_type="Allomorph",
            created_after=backup_time,
            validate_references=True,
            dry_run=False              # Actually import
        )
        print(f"✅ Imported {result_real.num_created} allomorphs")
    """
    )
    print("-" * 60)
    print()

    print("✅ This workflow is SAFE because:")
    print("   1. One-way operation (doesn't touch source)")
    print("   2. Only imports NEW objects (preserves existing)")
    print("   3. Validates references (prevents orphans)")
    print("   4. Dry-run preview (check before commit)")
    print()


def demo_filtered_import():
    """
    Demonstrate importing with custom filter.

    Scenario:
    - Import only consultant-verified allomorphs
    - Or only allomorphs of specific morph type
    - Or only allomorphs in specific phonological environment
    """
    print("=" * 60)
    print("FILTERED IMPORT: Custom Selection")
    print("=" * 60)
    print()

    print("CODE PATTERN:")
    print("-" * 60)
    print(
        """
    from flexicon.sync import SelectiveImport

    importer = SelectiveImport(source_project, target_project)

    # Example 1: Import only verified allomorphs
    def is_verified(obj):
        return (hasattr(obj, 'Status') and
                obj.Status == 'Verified')

    result = importer.import_by_filter(
        object_type="Allomorph",
        filter_fn=is_verified,
        validate_references=True
    )

    # Example 2: Import only stems (not affixes)
    def is_stem(obj):
        if hasattr(obj, 'MorphTypeRA'):
            morph_type = obj.MorphTypeRA
            if morph_type and hasattr(morph_type, 'Name'):
                name = morph_type.Name.AnalysisDefaultWritingSystem
                return 'stem' in name.lower()
        return False

    result = importer.import_by_filter(
        object_type="Allomorph",
        filter_fn=is_stem,
        validate_references=True
    )

    # Example 3: Import only allomorphs with examples
    def has_examples(obj):
        # Navigate: Allomorph → Entry → Senses → Examples
        if hasattr(obj, 'Owner'):
            entry = obj.Owner
            if hasattr(entry, 'SensesOS'):
                for sense in entry.SensesOS:
                    if hasattr(sense, 'ExamplesOS'):
                        if len(sense.ExamplesOS) > 0:
                            return True
        return False

    result = importer.import_by_filter(
        object_type="Allomorph",
        filter_fn=has_examples,
        validate_references=True
    )
    """
    )
    print("-" * 60)
    print()


def demo_validation_workflow():
    """
    Demonstrate validation before import.

    Shows what happens when references are missing.
    """
    print("=" * 60)
    print("VALIDATION: Preventing Data Corruption")
    print("=" * 60)
    print()

    print("⚠️  LINGUISTIC DATA INTEGRITY")
    print()
    print("When importing a Sense, it may reference:")
    print("  - Part of Speech (POS)")
    print("  - Semantic Domains")
    print("  - Morph Syntactic Analysis (MSA)")
    print("  - Reversal Entries")
    print()
    print("If these don't exist in target project:")
    print("  ❌ Import will FAIL")
    print("  ✅ You'll get clear error message")
    print("  ✅ No partial/corrupted import")
    print()

    print("VALIDATION OUTPUT EXAMPLE:")
    print("-" * 60)
    print(
        """
    VALIDATION RESULTS
    ----------------------------------------
    Critical Issues: 2
    Warnings: 1
    Info: 0
    Total: 3

    ❌ CRITICAL ISSUES - OPERATION BLOCKED

    ISSUES:
    ----------------------------------------
    [CRITICAL] LexSense abc12345: Referenced POS/MSA does not exist in target project
      reference_guid: def67890

    [CRITICAL] LexSense abc12345: Semantic domain not found in target
      domain_guid: ghi24680

    [WARNING] LexSense abc12345: Sense has 3 example(s) that will NOT be copied
      num_examples: 3

    ❌ Cannot import - fix references first!
    """
    )
    print("-" * 60)
    print()

    print("HOW TO FIX:")
    print("  1. Import POS/Semantic Domains first (from target)")
    print("  2. Or map source references to target equivalents")
    print("  3. Or accept that some data will be lost")
    print()


def demo_what_not_to_do():
    """
    Show the WRONG way (old sync method) vs RIGHT way.
    """
    print("=" * 60)
    print("❌ WRONG vs ✅ RIGHT")
    print("=" * 60)
    print()

    print("❌ WRONG WAY (Bidirectional Sync):")
    print("-" * 60)
    print(
        """
    # DON'T DO THIS for linguistic data!
    from flexicon.sync import SyncEngine

    sync = SyncEngine(test_project, stable_project)
    result = sync.sync(
        object_type="Allomorph",
        conflict_resolver="source_wins"  # ❌ Overwrites stable!
    )
    """
    )
    print()
    print("Problems:")
    print("  ❌ Bidirectional (can corrupt both projects)")
    print("  ❌ No date filtering (syncs everything)")
    print("  ❌ 'source_wins' overwrites stable data")
    print("  ❌ Can sync deleted objects")
    print()

    print("✅ RIGHT WAY (Selective Import):")
    print("-" * 60)
    print(
        """
    # DO THIS instead!
    from flexicon.sync import SelectiveImport
    from datetime import datetime

    importer = SelectiveImport(test_project, stable_project)
    result = importer.import_new_objects(
        object_type="Allomorph",
        created_after=backup_date,  # ✅ Only new
        validate_references=True,   # ✅ Check safety
        dry_run=True               # ✅ Preview first
    )
    """
    )
    print()
    print("Benefits:")
    print("  ✅ One-way (stable project protected)")
    print("  ✅ Date filtering (only imports new)")
    print("  ✅ Never overwrites existing data")
    print("  ✅ Validates before importing")
    print("  ✅ Dry-run preview")
    print()


def main():
    """Run all demos."""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "SELECTIVE IMPORT - LINGUISTIC WORKFLOW" + " " * 9 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    demos = [
        ("Linguist Workflow", demo_linguist_workflow),
        ("Filtered Import", demo_filtered_import),
        ("Validation", demo_validation_workflow),
        ("Wrong vs Right", demo_what_not_to_do),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"\n{'=' * 60}")
        print(f"DEMO {i}/{len(demos)}: {name}")
        print(f"{'=' * 60}\n")
        demo_func()
        if i < len(demos):
            input("\nPress Enter to continue to next demo...")

    print()
    print("=" * 60)
    print("KEY TAKEAWAYS")
    print("=" * 60)
    print()
    print("1. Use SelectiveImport, NOT SyncEngine for linguistic data")
    print("2. Always filter by date (created_after/modified_after)")
    print("3. Always validate_references=True")
    print("4. Always dry_run=True first")
    print("5. NEVER use bidirectional sync on production projects")
    print()
    print("📚 For more info, see:")
    print("   - docs/SYNC_FRAMEWORK_PHASE2_REVIEWS_SUMMARY.md")
    print("   - flexlibs/sync/validation.py")
    print("   - flexlibs/sync/selective_import.py")
    print()


if __name__ == "__main__":
    main()
