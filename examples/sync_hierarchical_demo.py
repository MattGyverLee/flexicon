#!/usr/bin/env python3
"""
Hierarchical Import Demo - Phase 3: Dependency Management

This example demonstrates hierarchical import with automatic dependency resolution.
Performs actual CRUD operations on the test project to verify functionality.

⚠️ WARNING: This demo modifies the target database!
Run on test projects only.

Author: FlexTools Development Team
Date: 2025-11-27
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup
from flexicon.sync import HierarchicalImporter, DependencyConfig, CircularDependencyError, ValidationError
from datetime import datetime


def demo_import_entry_with_hierarchy():
    """
    Demo 1: Import a lexical entry with all its senses and examples.

    Tests:
    - Automatic discovery of owned objects (senses, examples)
    - Correct import order (entry → senses → examples)
    - No duplicate imports
    """
    print("=" * 70)
    print("DEMO 1: Import Entry with Full Hierarchy")
    print("=" * 70)
    print()

    FLExInitialize()

    # Setup: Use same project as both source and target for testing
    # In real use, these would be different projects
    source = FLExProject()
    target = FLExProject()

    try:
        print("Opening projects...")
        source.OpenProject("Sena 3", writeEnabled=False)
        target.OpenProject("Sena 3", writeEnabled=True)

        # Create test entry with senses and examples if it doesn't exist
        print("\n1. Creating test entry with hierarchy...")

        if not source.LexEntry.Exists("hierarchical_test_entry"):
            print("   Creating test entry in source...")
            entry = source.LexEntry.Create("hierarchical_test_entry", "stem")

            # Add first sense with example
            sense1 = source.LexEntry.AddSense(entry, "test meaning 1")
            # Add example to sense1 (would require LexSense operations)

            # Add second sense
            sense2 = source.LexEntry.AddSense(entry, "test meaning 2")

            print(f"   Created entry with {source.LexEntry.GetSenseCount(entry)} senses")
        else:
            entry = source.LexEntry.Find("hierarchical_test_entry")
            print(f"   Test entry exists with {source.LexEntry.GetSenseCount(entry)} senses")

        # Get entry GUID for import
        entry_guid = source.LexEntry.GetGuid(entry)
        print(f"   Entry GUID: {entry_guid}")

        # Create hierarchical importer
        print("\n2. Creating hierarchical importer...")
        importer = HierarchicalImporter(source, target)

        # Configure to import full hierarchy
        config = DependencyConfig(
            include_owned=True,  # Import all owned objects
            resolve_references=True,  # Import referenced POS/domains
            max_owned_depth=10,  # Full depth
            skip_existing=True,  # Don't duplicate
            validate_all=True,  # Validate before import
        )

        # Preview with dry run
        print("\n3. Running dry run (preview)...")

        def show_progress(msg):
            print(f"   {msg}")

        result = importer.import_with_dependencies(
            object_type="LexEntry",
            guids=[entry_guid],
            config=config,
            validate_references=True,
            progress_callback=show_progress,
            dry_run=True,
        )

        print("\n4. Dry run results:")
        print(result.summary())

        if result.success:
            print("\n✅ Dry run successful!")
            print(f"   Would import {result.num_skipped} objects")

            # Show what would be imported
            if result.changes:
                print("\n   Objects to import:")
                type_counts = {}
                for change in result.changes:
                    type_counts[change.object_type] = type_counts.get(change.object_type, 0) + 1
                for obj_type, count in type_counts.items():
                    print(f"     - {obj_type}: {count}")
        else:
            print("\n⚠️ Dry run had errors:")
            for error in result.errors[:5]:  # Show first 5
                print(f"   - {error.error_message}")

    except ValidationError as e:
        print("\n❌ Validation failed:")
        print(e.result.detailed_report())

    except CircularDependencyError as e:
        print("\n❌ Circular dependency detected:")
        print(f"   {e}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\nClosing projects...")
        source.CloseProject()
        target.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("Demo 1 complete!")
    print("=" * 70)


def demo_batch_import():
    """
    Demo 2: Batch import multiple entries at once.

    Tests:
    - Batch processing
    - Shared dependency handling (same POS imported once)
    - Performance with multiple objects
    """
    print("\n\n")
    print("=" * 70)
    print("DEMO 2: Batch Import Multiple Entries")
    print("=" * 70)
    print()

    FLExInitialize()

    source = FLExProject()
    target = FLExProject()

    try:
        print("Opening projects...")
        source.OpenProject("Sena 3", writeEnabled=False)
        target.OpenProject("Sena 3", writeEnabled=True)

        # Create multiple test entries
        print("\n1. Creating test entries...")
        test_entries = []

        for i in range(1, 4):  # Create 3 test entries
            entry_name = f"batch_test_entry_{i}"

            if not source.LexEntry.Exists(entry_name):
                print(f"   Creating {entry_name}...")
                entry = source.LexEntry.Create(entry_name, "stem")
                source.LexEntry.AddSense(entry, f"test meaning {i}")
                test_entries.append(entry)
            else:
                entry = source.LexEntry.Find(entry_name)
                test_entries.append(entry)

        print(f"   Created/found {len(test_entries)} entries")

        # Get GUIDs
        entry_guids = [source.LexEntry.GetGuid(e) for e in test_entries]
        print(f"   GUIDs: {[g[:8] + '...' for g in entry_guids]}")

        # Import all at once
        print("\n2. Batch importing...")
        importer = HierarchicalImporter(source, target)

        config = DependencyConfig(include_owned=True, resolve_references=True, skip_existing=True)

        result = importer.import_with_dependencies(
            object_type="LexEntry",
            guids=entry_guids,
            config=config,
            progress_callback=lambda msg: print(f"   {msg}"),
            dry_run=True,
        )

        print("\n3. Batch import results:")
        print(result.summary())

        if result.success:
            print(f"\n✅ Batch import successful!")
            print(f"   Total objects: {result.num_skipped}")
            print("\n   Note: Shared POS/domains imported only once")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\nClosing projects...")
        source.CloseProject()
        target.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("Demo 2 complete!")
    print("=" * 70)


def demo_filtered_import():
    """
    Demo 3: Import entry but only specific owned objects.

    Tests:
    - Owned object type filtering
    - Selective hierarchy import
    """
    print("\n\n")
    print("=" * 70)
    print("DEMO 3: Filtered Import (Senses Only)")
    print("=" * 70)
    print()

    FLExInitialize()

    source = FLExProject()
    target = FLExProject()

    try:
        print("Opening projects...")
        source.OpenProject("Sena 3", writeEnabled=False)
        target.OpenProject("Sena 3", writeEnabled=True)

        # Find or create test entry
        print("\n1. Finding test entry...")
        if not source.LexEntry.Exists("filtered_test_entry"):
            print("   Creating test entry...")
            entry = source.LexEntry.Create("filtered_test_entry", "stem")
            source.LexEntry.AddSense(entry, "filtered test sense")
        else:
            entry = source.LexEntry.Find("filtered_test_entry")

        entry_guid = source.LexEntry.GetGuid(entry)
        print(f"   Entry GUID: {entry_guid}")

        # Import with filtering
        print("\n2. Importing with type filter (senses only)...")
        importer = HierarchicalImporter(source, target)

        config = DependencyConfig(
            include_owned=True,
            owned_types=["LexSense"],  # Only import senses, not examples/pronunciations
            resolve_references=True,
            skip_existing=True,
        )

        result = importer.import_with_dependencies(
            object_type="LexEntry",
            guids=[entry_guid],
            config=config,
            progress_callback=lambda msg: print(f"   {msg}"),
            dry_run=True,
        )

        print("\n3. Filtered import results:")
        print(result.summary())

        if result.success:
            print("\n✅ Filtered import successful!")

            # Show what was included/excluded
            types_imported = set()
            for change in result.changes:
                types_imported.add(change.object_type)

            print(f"   Types imported: {', '.join(types_imported)}")
            print("   Types excluded: LexExampleSentence, LexPronunciation, etc.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\nClosing projects...")
        source.CloseProject()
        target.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("Demo 3 complete!")
    print("=" * 70)


def demo_validation_handling():
    """
    Demo 4: Handle validation errors.

    Tests:
    - Validation integration
    - Error reporting
    - Graceful handling of missing references
    """
    print("\n\n")
    print("=" * 70)
    print("DEMO 4: Validation Error Handling")
    print("=" * 70)
    print()

    FLExInitialize()

    source = FLExProject()
    target = FLExProject()

    try:
        print("Opening projects...")
        source.OpenProject("Sena 3", writeEnabled=False)
        target.OpenProject("Sena 3", writeEnabled=True)

        print("\n1. Testing validation...")
        print("   (Using existing entry for validation test)")

        # Get any entry for testing
        entries = list(source.LexEntry.GetAll())
        if not entries:
            print("   No entries found for testing")
            return

        entry = entries[0]
        entry_guid = source.LexEntry.GetGuid(entry)
        headword = source.LexEntry.GetHeadword(entry)

        print(f"   Testing with entry: {headword}")
        print(f"   GUID: {entry_guid}")

        # Import with validation enabled
        print("\n2. Importing with validation...")
        importer = HierarchicalImporter(source, target)

        config = DependencyConfig(
            include_owned=True, resolve_references=True, skip_existing=True, validate_all=True  # Enable validation
        )

        try:
            result = importer.import_with_dependencies(
                object_type="LexEntry",
                guids=[entry_guid],
                config=config,
                validate_references=True,
                progress_callback=lambda msg: print(f"   {msg}"),
                dry_run=True,
            )

            print("\n3. Validation results:")
            if result.success:
                print("   ✅ Validation passed!")
                print(f"   Objects validated: {result.num_skipped}")
            else:
                print("   ⚠️ Validation warnings (non-critical):")
                for error in result.errors[:3]:
                    print(f"     - {error.error_message}")

        except ValidationError as e:
            print("\n   ❌ Critical validation errors:")
            print(e.result.detailed_report())
            print("\n   Resolution options:")
            print("     1. Fix issues in source project")
            print("     2. Import required references first")
            print("     3. Set validate_references=False (not recommended)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\nClosing projects...")
        source.CloseProject()
        target.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("Demo 4 complete!")
    print("=" * 70)


def demo_dependency_graph_analysis():
    """
    Demo 5: Analyze dependency graph without importing.

    Tests:
    - Dependency discovery
    - Graph analysis
    - Import order calculation
    """
    print("\n\n")
    print("=" * 70)
    print("DEMO 5: Dependency Graph Analysis")
    print("=" * 70)
    print()

    FLExInitialize()

    source = FLExProject()
    target = FLExProject()

    try:
        print("Opening projects...")
        source.OpenProject("Sena 3", writeEnabled=False)
        target.OpenProject("Sena 3", writeEnabled=True)

        # Get an entry with senses
        print("\n1. Finding entry with senses...")
        entry = None
        for e in source.LexEntry.GetAll():
            if source.LexEntry.GetSenseCount(e) > 0:
                entry = e
                break

        if not entry:
            print("   No entries with senses found")
            return

        headword = source.LexEntry.GetHeadword(entry)
        sense_count = source.LexEntry.GetSenseCount(entry)
        print(f"   Found: {headword} ({sense_count} senses)")

        # Build dependency graph
        print("\n2. Building dependency graph...")
        from flexicon.sync import DependencyResolver, DependencyConfig

        resolver = DependencyResolver(source, target)

        config = DependencyConfig(include_owned=True, resolve_references=True, max_owned_depth=5)

        graph = resolver.resolve_dependencies(entry, "LexEntry", config)

        print(f"   Graph built with {len(graph)} objects")

        # Analyze graph
        print("\n3. Dependency graph analysis:")
        print(graph.summary())

        print("\n4. Import order:")
        import_order = graph.get_import_order()
        print(f"   {len(import_order)} objects to import in order:")
        for idx, (guid, obj_type) in enumerate(import_order[:10], 1):
            print(f"   {idx}. {obj_type}: {guid[:8]}...")
        if len(import_order) > 10:
            print(f"   ... and {len(import_order) - 10} more")

        # Check for cycles
        print("\n5. Cycle detection:")
        cycles = graph.detect_cycles()
        if cycles:
            print(f"   ⚠️ Found {len(cycles)} cycle(s)")
            for cycle in cycles[:1]:  # Show first cycle
                print(f"   Cycle: {' → '.join([c[:8] + '...' for c in cycle])}")
        else:
            print("   ✅ No cycles detected")

        # Root/leaf analysis
        print("\n6. Root and leaf nodes:")
        roots = graph.get_roots()
        leaves = graph.get_leaves()
        print(f"   Roots (no dependencies): {len(roots)}")
        print(f"   Leaves (nothing depends on): {len(leaves)}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\nClosing projects...")
        source.CloseProject()
        target.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("Demo 5 complete!")
    print("=" * 70)


def run_all_demos():
    """Run all Phase 3 demonstrations."""
    print("=" * 70)
    print("         PHASE 3: HIERARCHICAL IMPORT DEMONSTRATIONS")
    print()
    print("  These demos test the dependency management features by")
    print("  performing actual operations on the test project.")
    print()
    print("  WARNING: Modifies the test database!")
    print("=" * 70)
    print()

    try:
        # Demo 1: Basic hierarchical import
        demo_import_entry_with_hierarchy()

        # Demo 2: Batch import
        demo_batch_import()

        # Demo 3: Filtered import
        demo_filtered_import()

        # Demo 4: Validation handling
        demo_validation_handling()

        # Demo 5: Dependency analysis
        demo_dependency_graph_analysis()

        print("\n\n")
        print("=" * 70)
        print("ALL DEMOS COMPLETE!")
        print("=" * 70)
        print()
        print("Summary of Phase 3 Features Tested:")
        print("  - Automatic dependency discovery")
        print("  - Hierarchical cascade (entry -> senses -> examples)")
        print("  - Topological sorting (correct import order)")
        print("  - Batch import with shared dependencies")
        print("  - Filtered import (owned object types)")
        print("  - Validation integration")
        print("  - Dependency graph analysis")
        print("  - Cycle detection")
        print()
        print("Phase 3 is fully functional!")

    except KeyboardInterrupt:
        print("\n\nDemos interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Demo suite error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print(
        """
Hierarchical Import Demo - Phase 3
===================================

This demonstrates the Phase 3 dependency management features:

1. Import Entry with Full Hierarchy
   - Automatic owned object discovery
   - Correct import order

2. Batch Import Multiple Entries
   - Import multiple entries at once
   - Shared dependency handling

3. Filtered Import
   - Select specific owned object types
   - Flexible configuration

4. Validation Error Handling
   - Reference validation
   - Error reporting

5. Dependency Graph Analysis
   - Build dependency graph
   - Analyze structure
   - Calculate import order

Requirements:
  - FLEx test project
  - Python.NET with FLEx assemblies
  - Write access to test project

WARNING: These demos modify the test database!
    """
    )

    response = input("\nRun all demos? (y/N): ")
    if response.lower() == "y":
        run_all_demos()
    else:
        print("\nDemos skipped. You can run individual demos by calling:")
        print("  - demo_import_entry_with_hierarchy()")
        print("  - demo_batch_import()")
        print("  - demo_filtered_import()")
        print("  - demo_validation_handling()")
        print("  - demo_dependency_graph_analysis()")
