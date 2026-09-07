"""
Sync Execute Demo - Phase 2: Write operations

This example demonstrates the full sync execution with write operations.

⚠️ WARNING: This demo modifies the target database!
Only run in write mode when you understand the consequences.

Author: FlexTools Development Team
Date: 2025-11-26
"""

from flexicon import FLExProject
from flexicon.sync import (
    SyncEngine,
    GuidMatchStrategy,
    SourceWinsResolver,
)


def demo_sync_execution_dry_run():
    """
    Demonstrate sync with dry_run=True (safe preview).

    This shows what would happen without making changes.
    """
    print("=" * 60)
    print("SYNC EXECUTION DEMO - DRY RUN (SAFE)")
    print("=" * 60)
    print()

    # Open projects
    print("Opening projects...")
    source = FLExProject()
    source.OpenProject("Sena 3", writeEnabled=False)

    target = FLExProject()
    target.OpenProject("Sena 3", writeEnabled=True)  # Need write for sync

    try:
        # Create sync engine
        print("Creating sync engine...")
        sync = SyncEngine(source_project=source, target_project=target)

        print(f"Mode: {sync.mode.value}")
        print()

        # Execute sync with dry_run
        print("Executing sync (dry_run=True - no changes will be made)...")
        print()

        result = sync.sync(
            object_type="Allomorph",
            match_strategy=GuidMatchStrategy(),
            conflict_resolver=SourceWinsResolver(),
            dry_run=True,  # SAFE - no changes
            progress_callback=lambda msg: print(f"  {msg}"),
        )

        # Display results
        print()
        print(result.summary())
        print()

        if result.success:
            print("✅ Dry run successful!")
            print()
            print("To actually execute sync:")
            print("  - Set dry_run=False")
            print("  - Review changes carefully")
            print("  - Consider backup first")
        else:
            print("⚠️ Errors encountered during dry run:")
            for error in result.errors:
                print(f"  - {error}")

    finally:
        source.CloseProject()
        target.CloseProject()


def demo_sync_with_comparison():
    """
    Demonstrate workflow: compare first, then sync.

    This is the safest approach - review changes before applying.
    """
    print("=" * 60)
    print("SAFE SYNC WORKFLOW: Compare → Review → Sync")
    print("=" * 60)
    print()

    source = FLExProject()
    source.OpenProject("Sena 3", writeEnabled=False)

    target = FLExProject()
    target.OpenProject("Sena 3", writeEnabled=False)  # Start readonly

    try:
        # Step 1: Compare (readonly)
        print("Step 1: Compare (readonly mode)...")
        sync = SyncEngine(source_project=source, target_project=target)

        diff = sync.compare(object_type="Allomorph")

        print(diff.summary())
        print()

        # Step 2: User reviews changes
        if diff.has_changes:
            print(f"Found {diff.total} changes.")
            print("Review the changes in allomorph_diff.md")
            diff.export("allomorph_diff.md")
            print()

            # Step 3: User decides whether to proceed
            # (In real usage, user would review the file first)
            proceed = input("Proceed with sync? [y/N]: ")

            if proceed.lower() == "y":
                # Close and reopen with write enabled
                target.CloseProject()
                target.OpenProject("Sena 3", writeEnabled=True)

                # Recreate sync engine
                sync = SyncEngine(source_project=source, target_project=target)

                print()
                print("Step 3: Executing sync...")

                result = sync.sync(
                    object_type="Allomorph",
                    match_strategy=GuidMatchStrategy(),
                    conflict_resolver="source_wins",
                    dry_run=False,  # ACTUAL CHANGES
                )

                print()
                print(result.summary())

                # Export log
                result.export_log("allomorph_sync.log")
                print()
                print("Sync log saved to: allomorph_sync.log")
            else:
                print("Sync cancelled by user.")
        else:
            print("No changes to sync - projects are identical.")

    finally:
        source.CloseProject()
        if target:
            target.CloseProject()


def demo_sync_with_conflict_resolution():
    """
    Demonstrate different conflict resolution strategies.
    """
    print("=" * 60)
    print("CONFLICT RESOLUTION DEMO")
    print("=" * 60)
    print()

    source = FLExProject()
    source.OpenProject("Sena 3", writeEnabled=False)

    target = FLExProject()
    target.OpenProject("Sena 3", writeEnabled=True)

    try:
        sync = SyncEngine(source_project=source, target_project=target)

        # Strategy 1: Source wins (most common)
        print("Strategy 1: Source Wins")
        print("  - Source project is authoritative")
        print("  - Overwrites target with source data")
        print()

        result1 = sync.sync(object_type="Allomorph", conflict_resolver="source_wins", dry_run=True)

        print(f"  Result: {result1.num_updated} would be updated")
        print()

        # Strategy 2: Target wins
        print("Strategy 2: Target Wins")
        print("  - Keep target data")
        print("  - Only add new items from source")
        print()

        from flexicon.sync import TargetWinsResolver

        result2 = sync.sync(object_type="Allomorph", conflict_resolver=TargetWinsResolver(), dry_run=True)

        print(f"  Result: {result2.num_updated} would be updated (should be 0)")
        print()

    finally:
        source.CloseProject()
        target.CloseProject()


if __name__ == "__main__":
    print()
    print("FlexLibs Sync Framework - Phase 2 Demo Suite")
    print("⚠️  WARNING: Some demos modify database!")
    print()

    # Run dry-run demo (safe)
    demo_sync_execution_dry_run()

    print()
    input("Press Enter to run comparison→sync workflow demo...")
    demo_sync_with_comparison()

    print()
    input("Press Enter to run conflict resolution demo (dry-run)...")
    demo_sync_with_conflict_resolution()

    print()
    print("All demos complete!")
    print()
    print("Key takeaways:")
    print("  ✅ Always compare first (readonly)")
    print("  ✅ Review changes before syncing")
    print("  ✅ Use dry_run=True to preview")
    print("  ✅ Export logs for audit trail")
    print("  ✅ Consider backups for safety")
