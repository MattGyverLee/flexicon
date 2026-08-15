"""
Sync Allomorphs Demo - Example of using the sync framework

This example demonstrates how to use the flexlibs sync framework to compare
and synchronize allomorphs between two FLEx projects.

Phase 1: Comparison/diff functionality only
Phase 2+: Full sync execution

Author: FlexTools Development Team
Date: 2025-11-26
"""

from flexicon import FLExProject
from flexicon.sync import (
    SyncEngine,
    GuidMatchStrategy,
    FieldMatchStrategy,
)


def demo_compare_allomorphs():
    """
    Demonstrate allomorph comparison between two projects.

    This shows the readonly diff mode - what FlexTools would display
    when writeEnabled=False.
    """
    print("=" * 60)
    print("SYNC ALLOMORPHS DEMO - Phase 1: Comparison")
    print("=" * 60)
    print()

    # Open source project (readonly)
    print("Opening source project...")
    source = FLExProject()
    source.OpenProject("Sena 3", writeEnabled=False)

    # Open target project (readonly for comparison)
    print("Opening target project...")
    target = FLExProject()
    target.OpenProject("Sena 3", writeEnabled=False)  # Same project for demo

    try:
        # Create sync engine
        print()
        print("Creating sync engine...")
        sync = SyncEngine(source_project=source, target_project=target)

        print(f"Mode: {sync.mode.value}")
        print()

        # Compare using GUID strategy
        print("Comparing allomorphs (GUID-based matching)...")
        print()

        diff = sync.compare(
            object_type="Allomorph", match_strategy=GuidMatchStrategy(), progress_callback=lambda msg: print(f"  {msg}")
        )

        # Display summary
        print()
        print(diff.summary())
        print()

        # Display detailed report
        if diff.has_changes:
            print("Detailed Report:")
            print(diff.to_report(format="console", verbose=False))

            # Export to file
            print()
            print("Exporting reports...")
            diff.export("allomorph_diff.txt")
            diff.export("allomorph_diff.md")
            print("  - allomorph_diff.txt")
            print("  - allomorph_diff.md")
        else:
            print("Projects are identical - no changes to sync.")

        print()
        print("=" * 60)
        print("Demo complete!")
        print()
        print("Next steps:")
        print("  - Open allomorph_diff.md to review changes")
        print("  - Phase 2 will add sync execution (writeEnabled=True)")
        print("=" * 60)

    finally:
        # Clean up
        source.CloseProject()
        target.CloseProject()


def demo_compare_with_filter():
    """
    Demonstrate filtered comparison.

    Shows how to compare only specific allomorphs using a filter function.
    """
    print("=" * 60)
    print("FILTERED COMPARISON DEMO")
    print("=" * 60)
    print()

    source = FLExProject()
    source.OpenProject("Sena 3", writeEnabled=False)

    target = FLExProject()
    target.OpenProject("Sena 3", writeEnabled=False)

    try:
        sync = SyncEngine(source_project=source, target_project=target)

        # Filter: only compare stem allomorphs
        def stem_only(obj):
            """Include only stem allomorphs."""
            morph_type = source.Allomorph.GetMorphType(obj)
            if morph_type:
                type_name = source.Allomorph.GetMorphTypeName(morph_type)
                return type_name and "stem" in type_name.lower()
            return False

        print("Comparing stem allomorphs only...")
        diff = sync.compare(object_type="Allomorph", match_strategy=GuidMatchStrategy(), filter_fn=stem_only)

        print(diff.summary())

    finally:
        source.CloseProject()
        target.CloseProject()


def demo_field_based_matching():
    """
    Demonstrate field-based matching strategy.

    Shows how to match allomorphs by form instead of GUID.
    Useful for cross-project merging.
    """
    print("=" * 60)
    print("FIELD-BASED MATCHING DEMO")
    print("=" * 60)
    print()

    source = FLExProject()
    source.OpenProject("Sena 3", writeEnabled=False)

    target = FLExProject()
    target.OpenProject("Sena 3", writeEnabled=False)

    try:
        sync = SyncEngine(source_project=source, target_project=target)

        # Register custom strategy
        field_strategy = FieldMatchStrategy(key_fields=["form"], case_sensitive=False)

        sync.register_strategy("form_match", field_strategy)

        print("Comparing allomorphs (form-based matching)...")
        diff = sync.compare(object_type="Allomorph", match_strategy="form_match")  # Use registered strategy name

        print(diff.summary())
        print()
        print("Note: Field-based matching is less reliable than GUID matching")
        print("      but useful when projects don't share common history.")

    finally:
        source.CloseProject()
        target.CloseProject()


if __name__ == "__main__":
    print()
    print("FlexLibs Sync Framework - Demo Suite")
    print()

    # Run main demo
    demo_compare_allomorphs()

    print()
    input("Press Enter to run filtered comparison demo...")
    demo_compare_with_filter()

    print()
    input("Press Enter to run field-based matching demo...")
    demo_field_based_matching()

    print()
    print("All demos complete!")
