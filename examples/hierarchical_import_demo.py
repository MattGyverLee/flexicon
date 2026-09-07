"""
Hierarchical Import Demo - Phase 3

Demonstrates importing FLEx objects with automatic dependency resolution.

Author: FlexTools Development Team
Date: 2025-11-27
"""

from datetime import datetime
from flexicon.sync import HierarchicalImporter, DependencyConfig, CircularDependencyError, ValidationError


def demo_import_entry_with_senses():
    """
    Demo: Import a lexical entry with all its senses and examples.

    This is the most common linguistic workflow - importing complete
    entries with all their content in a single operation.
    """
    print("=" * 60)
    print("DEMO: Import Entry with All Senses and Examples")
    print("=" * 60)

    # Setup (in real usage, these would be actual FlexProject instances)
    from flexicon import FLExProject

    source = FLExProject("path/to/consultant_project.fwdata", writeEnabled=False)

    target = FLExProject("path/to/main_project.fwdata", writeEnabled=True)

    # Initialize hierarchical importer
    importer = HierarchicalImporter(source, target)

    # Configure dependency resolution
    config = DependencyConfig(
        include_owned=True,  # Import all owned objects
        resolve_references=True,  # Import referenced POS/domains
        max_owned_depth=10,  # Traverse full hierarchy
        skip_existing=True,  # Skip objects already in target
        validate_all=True,  # Validate before import
    )

    # Entry GUID to import
    entry_guid = "entry-guid-12345"

    print(f"\nImporting entry {entry_guid}...")

    def progress(msg):
        """Progress callback."""
        print(f"  {msg}")

    try:
        # First, do dry run to preview
        result = importer.import_with_dependencies(
            object_type="LexEntry",
            guids=[entry_guid],
            config=config,
            validate_references=True,
            progress_callback=progress,
            dry_run=True,
        )

        print(f"\n✓ Dry run complete:")
        print(f"  Would import: {result.num_skipped} objects")
        print(result.summary())

        # If looks good, do actual import
        if result.success:
            print("\nProceeding with actual import...")

            result = importer.import_with_dependencies(
                object_type="LexEntry",
                guids=[entry_guid],
                config=config,
                validate_references=True,
                progress_callback=progress,
                dry_run=False,
            )

            print(f"\n✓ Import complete:")
            print(f"  Created: {result.num_created} objects")
            print(result.summary())

            # What was imported?
            print("\nImported objects:")
            for change in result.changes:
                print(f"  - {change.object_type}: {change.object_guid[:8]}...")

    except ValidationError as e:
        print(f"\n❌ Validation failed:")
        print(e.result.detailed_report())

    except CircularDependencyError as e:
        print(f"\n❌ Circular dependency detected:")
        print(f"  {e}")


def demo_import_with_filtering():
    """
    Demo: Import entry but only include senses and examples (no pronunciations).

    Shows how to filter which owned objects to include.
    """
    print("\n" + "=" * 60)
    print("DEMO: Import with Filtered Owned Objects")
    print("=" * 60)

    from flexicon import FLExProject

    source = FLExProject("source.fwdata", writeEnabled=False)
    target = FLExProject("target.fwdata", writeEnabled=True)

    importer = HierarchicalImporter(source, target)

    # Only include senses and examples, not pronunciations
    config = DependencyConfig(
        include_owned=True, owned_types=["LexSense", "LexExampleSentence"], resolve_references=True  # Filter types
    )

    result = importer.import_with_dependencies(
        object_type="LexEntry", guids=["entry-guid"], config=config, dry_run=False
    )

    print(f"\n✓ Imported {result.num_created} objects (senses & examples only)")


def demo_import_semantic_domain_with_entries():
    """
    Demo: Import semantic domain and all entries that reference it.

    Shows bidirectional import - import a reference object and all
    objects that refer to it.
    """
    print("\n" + "=" * 60)
    print("DEMO: Import Semantic Domain with All Referencing Entries")
    print("=" * 60)

    from flexicon import FLExProject

    source = FLExProject("consultant.fwdata", writeEnabled=False)
    target = FLExProject("main.fwdata", writeEnabled=True)

    importer = HierarchicalImporter(source, target)

    domain_guid = "domain-guid-12345"

    print(f"\nImporting semantic domain {domain_guid}...")
    print("  Finding all entries/senses that use this domain...")

    result = importer.import_related(
        object_type="CmSemanticDomain",
        guid=domain_guid,
        include_referring_objects=["LexSense"],  # Import senses using this domain
        dry_run=True,
    )

    print(f"\n✓ Would import:")
    print(f"  1 semantic domain")
    print(f"  {result.num_skipped - 1} senses that reference it")
    print(f"  Total: {result.num_skipped} objects")


def demo_batch_import_multiple_entries():
    """
    Demo: Import multiple entries at once with dependency resolution.

    Shows how to import several entries in one operation, automatically
    resolving shared dependencies (same POS, domains, etc.).
    """
    print("\n" + "=" * 60)
    print("DEMO: Batch Import Multiple Entries")
    print("=" * 60)

    from flexicon import FLExProject

    source = FLExProject("consultant.fwdata", writeEnabled=False)
    target = FLExProject("main.fwdata", writeEnabled=True)

    importer = HierarchicalImporter(source, target)

    # Import 5 entries at once
    entry_guids = ["entry-1-guid", "entry-2-guid", "entry-3-guid", "entry-4-guid", "entry-5-guid"]

    config = DependencyConfig(
        include_owned=True, resolve_references=True, skip_existing=True  # Won't duplicate shared POS/domains
    )

    print(f"\nImporting {len(entry_guids)} entries...")

    result = importer.import_with_dependencies(object_type="LexEntry", guids=entry_guids, config=config, dry_run=False)

    print(f"\n✓ Import complete:")
    print(f"  Entries: 5")
    print(f"  Total objects imported: {result.num_created}")
    print(f"  (Includes senses, examples, POS, domains, etc.)")

    # Show shared dependencies
    print("\nNote: If multiple entries used the same POS or semantic domain,")
    print("      they were imported only once (not duplicated).")


def demo_handle_validation_errors():
    """
    Demo: Handle validation errors during hierarchical import.

    Shows what happens when imported objects have missing references
    or validation issues.
    """
    print("\n" + "=" * 60)
    print("DEMO: Handling Validation Errors")
    print("=" * 60)

    from flexicon import FLExProject

    source = FLExProject("source.fwdata", writeEnabled=False)
    target = FLExProject("target.fwdata", writeEnabled=True)

    importer = HierarchicalImporter(source, target)

    # This entry has a sense with missing POS
    problematic_entry = "entry-with-issues"

    try:
        result = importer.import_with_dependencies(
            object_type="LexEntry", guids=[problematic_entry], validate_references=True, dry_run=False
        )

        print("✓ Import succeeded")

    except ValidationError as e:
        print("❌ Validation failed with critical issues:")
        print(e.result.detailed_report())
        print("\nResolution options:")
        print("  1. Fix the issues in source project")
        print("  2. Import required POS first")
        print("  3. Disable validation (NOT recommended)")


def demo_handle_circular_dependencies():
    """
    Demo: Handle circular dependencies.

    Shows what happens when objects have circular references
    (e.g., variant entries referencing each other).
    """
    print("\n" + "=" * 60)
    print("DEMO: Handling Circular Dependencies")
    print("=" * 60)

    from flexicon import FLExProject

    source = FLExProject("source.fwdata", writeEnabled=False)
    target = FLExProject("target.fwdata", writeEnabled=True)

    importer = HierarchicalImporter(source, target)

    # These entries reference each other as variants
    entry_with_cycle = "entry-variant-cycle"

    try:
        # By default, cycles cause error
        result = importer.import_with_dependencies(object_type="LexEntry", guids=[entry_with_cycle], dry_run=False)

    except CircularDependencyError as e:
        print(f"❌ Circular dependency detected: {e}")
        print("\nTrying with allow_cycles=True...")

        # Allow cycles - framework will break them at weakest links
        config = DependencyConfig(allow_cycles=True)

        result = importer.import_with_dependencies(
            object_type="LexEntry", guids=[entry_with_cycle], config=config, dry_run=False
        )

        print(f"✓ Import succeeded by breaking cycles")
        print(f"  Imported: {result.num_created} objects")
        print("\nNote: Cross-references were broken to allow import.")
        print("      You may need to manually update variant links.")


def demo_progress_tracking():
    """
    Demo: Track progress during large import operations.

    Shows how to use progress callbacks for long-running imports.
    """
    print("\n" + "=" * 60)
    print("DEMO: Progress Tracking")
    print("=" * 60)

    from flexicon import FLExProject

    source = FLExProject("source.fwdata", writeEnabled=False)
    target = FLExProject("target.fwdata", writeEnabled=True)

    importer = HierarchicalImporter(source, target)

    # Track progress with callback
    progress_messages = []

    def track_progress(message):
        """Capture progress messages."""
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {message}")
        progress_messages.append(message)

    print("\nImporting large entry with 50+ senses...")

    result = importer.import_with_dependencies(
        object_type="LexEntry", guids=["large-entry-guid"], progress_callback=track_progress, dry_run=False
    )

    print(f"\n✓ Import complete")
    print(f"  Total progress updates: {len(progress_messages)}")


def demo_comparison_selective_vs_hierarchical():
    """
    Demo: When to use SelectiveImport vs HierarchicalImporter.

    Shows the differences and appropriate use cases for each.
    """
    print("\n" + "=" * 60)
    print("COMPARISON: SelectiveImport vs HierarchicalImporter")
    print("=" * 60)

    print("\n1. SelectiveImport (Phase 2.5):")
    print("   Use when:")
    print("     - Importing NEW objects by date")
    print("     - Filtering by custom criteria")
    print("     - You know objects are independent")
    print("     - Safety is paramount")
    print("\n   Example: Import allomorphs created after backup date")

    print("\n2. HierarchicalImporter (Phase 3):")
    print("   Use when:")
    print("     - Importing complete hierarchies (entry + senses + examples)")
    print("     - Objects have complex dependencies")
    print("     - You want automatic reference resolution")
    print("     - Importing related object graphs")
    print("\n   Example: Import entry with all its content")

    print("\n3. Best Practice:")
    print("     Use HierarchicalImporter with dry_run=True first")
    print("     Review what will be imported")
    print("     Then run with dry_run=False")


if __name__ == "__main__":
    print("\nPHASE 3: Hierarchical Import Demonstrations")
    print("=" * 60)
    print("\nThese demos show how to use the Hierarchical Import feature")
    print("to import FLEx objects with automatic dependency resolution.\n")

    # Run demos
    # demo_import_entry_with_senses()
    # demo_import_with_filtering()
    # demo_import_semantic_domain_with_entries()
    # demo_batch_import_multiple_entries()
    # demo_handle_validation_errors()
    # demo_handle_circular_dependencies()
    # demo_progress_tracking()
    demo_comparison_selective_vs_hierarchical()

    print("\n" + "=" * 60)
    print("Demos complete!")
    print("=" * 60)
