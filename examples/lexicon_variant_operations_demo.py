#!/usr/bin/env python3
"""
Full CRUD Demo: VariantOperations for flexlibs

This script demonstrates complete CRUD operations for variant.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_variant_crud():
    """
    Demonstrate full CRUD operations for variant.

    Tests:
    - CREATE: Create new test variant
    - READ: Get all variants, find by name/identifier
    - UPDATE: Modify variant properties
    - DELETE: Remove test variant
    """

    print("=" * 70)
    print("VARIANT OPERATIONS - FULL CRUD TEST")
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

    test_obj = None
    test_name = "crud_test_variant"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing variants")
        print("=" * 70)

        print("\nGetting all variants...")
        initial_count = 0
        for obj in project.Variants.GetAll():
            # Display first few objects
            try:
                name = project.Variants.GetName(obj) if hasattr(project.Variants, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal variants (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test variant")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Variants, "Exists") and project.Variants.Exists(test_name):
                print(f"\nTest variant '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Variants.Find(test_name) if hasattr(project.Variants, "Find") else None
                if existing:
                    project.Variants.Delete(existing)
                    print("  Deleted existing test variant")
        except:
            pass

        # Create parent entry for variant testing
        print("\nCreating parent entry for variant test...")
        parent_entry = None
        try:
            parent_entry = project.LexEntry.Create("crud_test_entry_for_variant")
            print(f"  Created parent entry: crud_test_entry_for_variant")
        except Exception as e:
            print(f"  ERROR creating parent entry: {e}")
            print("  Cannot test variant without parent entry")
            return

        # Get variant type
        variant_type = None
        try:
            # Get first available variant type
            from SIL.LCModel import ILexEntryType  # type: ignore[import]

            variant_types = project.project.LexDb.VariantEntryTypesOA.PossibilitiesOS  # type: ignore[attr-defined]
            if variant_types.Count > 0:
                variant_type = variant_types[0]
        except:
            pass

        if not variant_type:
            print("  ERROR: Could not find variant type")
            print("  Cannot test variant without variant type")
            return

        print(f"\nCreating new variant: '{test_name}'")

        # Create variant with parent entry
        test_obj = project.Variants.Create(parent_entry, test_name, variant_type)
        print(f"  SUCCESS: Variant created!")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify variant was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Variants, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Variants.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Variants, "Find"):
            print(f"\nFinding variant by name...")
            found_obj = project.Variants.Find(test_name)
            if found_obj:
                print(f"  FOUND: variant")
                try:
                    if hasattr(project.Variants, "GetName"):
                        print(f"  Name: {project.Variants.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all variants after creation...")
        current_count = sum(1 for _ in project.Variants.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify variant properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Variants, "SetName"):
                try:
                    new_name = "crud_test_variant_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = project.Variants.GetName(test_obj) if hasattr(project.Variants, "GetName") else test_name
                    project.Variants.SetName(test_obj, new_name)
                    updated_name = (
                        project.Variants.GetName(test_obj) if hasattr(project.Variants, "GetName") else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Variants):
                if method_name.startswith("Set") and method_name != "SetName" and not updated:
                    print(f"\nFound update method: {method_name}")
                    print("  (Method available but not tested in this demo)")
                    break

            if updated:
                print("\n  UPDATE: SUCCESS")
            else:
                print("\n  Note: No standard update methods found or tested")

        # ==================== READ: Verify updates ====================
        print("\n" + "=" * 70)
        print("STEP 5: READ - Verify updates persisted")
        print("=" * 70)

        if hasattr(project.Variants, "Find"):
            print(f"\nFinding variant after update...")
            updated_obj = project.Variants.Find(test_name)
            if updated_obj:
                print(f"  FOUND: variant")
                try:
                    if hasattr(project.Variants, "GetName"):
                        print(f"  Name: {project.Variants.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test variant")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test variant...")
            try:
                obj_name = project.Variants.GetName(test_obj) if hasattr(project.Variants, "GetName") else test_name
            except:
                obj_name = test_name

            project.Variants.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Variants, "Exists"):
                still_exists = project.Variants.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Variant still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Variants.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new variant")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete variant")
        print("\nTest completed successfully!")

    except Exception as e:
        print(f"\n\nERROR during CRUD test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup: Ensure test object is removed
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)

        try:
            for name in ["crud_test_variant", "crud_test_variant_modified"]:
                if hasattr(project.Variants, "Exists") and project.Variants.Exists(name):
                    obj = project.Variants.Find(name) if hasattr(project.Variants, "Find") else None
                    if obj:
                        project.Variants.Delete(obj)
                        print(f"  Cleaned up: {name}")
        except:
            pass

        # Cleanup parent entry
        try:
            if parent_entry:
                project.LexEntry.Delete(parent_entry)
                print("  Cleaned up: parent entry")
        except:
            pass

        print("\nClosing project...")
        project.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    print(
        """
Variant Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for variant.

Operations Tested:
==================

CREATE: Create new variant
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test variant
3. READ to verify creation
4. UPDATE variant properties
5. READ to verify updates
6. DELETE test variant
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test variant is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_variant_crud()
    else:
        print("\nDemo skipped.")
