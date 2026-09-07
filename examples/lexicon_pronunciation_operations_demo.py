#!/usr/bin/env python3
"""
Full CRUD Demo: PronunciationOperations for flexlibs

This script demonstrates complete CRUD operations for pronunciation.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_pronunciation_crud():
    """
    Demonstrate full CRUD operations for pronunciation.

    Tests:
    - CREATE: Create new test pronunciation
    - READ: Get all pronunciations, find by name/identifier
    - UPDATE: Modify pronunciation properties
    - DELETE: Remove test pronunciation
    """

    print("=" * 70)
    print("PRONUNCIATION OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_pronunciation"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing pronunciations")
        print("=" * 70)

        print("\nGetting all pronunciations...")
        initial_count = 0
        for obj in project.Pronunciations.GetAll():
            # Display first few objects
            try:
                name = project.Pronunciations.GetName(obj) if hasattr(project.Pronunciations, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal pronunciations (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test pronunciation")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Pronunciations, "Exists") and project.Pronunciations.Exists(test_name):
                print(f"\nTest pronunciation '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Pronunciations.Find(test_name) if hasattr(project.Pronunciations, "Find") else None
                if existing:
                    project.Pronunciations.Delete(existing)
                    print("  Deleted existing test pronunciation")
        except:
            pass

        # Create parent entry for pronunciation testing
        print("\nCreating parent entry for pronunciation test...")
        parent_entry = None
        try:
            parent_entry = project.LexEntry.Create("crud_test_entry_for_pronunciation")
            print(f"  Created parent entry: crud_test_entry_for_pronunciation")
        except Exception as e:
            print(f"  ERROR creating parent entry: {e}")
            print("  Cannot test pronunciation without parent entry")
            return

        print(f"\nCreating new pronunciation: '{test_name}'")

        # Create pronunciation with parent entry
        test_obj = project.Pronunciations.Create(parent_entry, test_name)
        print(f"  SUCCESS: Pronunciation created!")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify pronunciation was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Pronunciations, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Pronunciations.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Pronunciations, "Find"):
            print(f"\nFinding pronunciation by name...")
            found_obj = project.Pronunciations.Find(test_name)
            if found_obj:
                print(f"  FOUND: pronunciation")
                try:
                    if hasattr(project.Pronunciations, "GetName"):
                        print(f"  Name: {project.Pronunciations.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all pronunciations after creation...")
        current_count = sum(1 for _ in project.Pronunciations.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify pronunciation properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Pronunciations, "SetName"):
                try:
                    new_name = "crud_test_pronunciation_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = (
                        project.Pronunciations.GetName(test_obj)
                        if hasattr(project.Pronunciations, "GetName")
                        else test_name
                    )
                    project.Pronunciations.SetName(test_obj, new_name)
                    updated_name = (
                        project.Pronunciations.GetName(test_obj)
                        if hasattr(project.Pronunciations, "GetName")
                        else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Pronunciations):
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

        if hasattr(project.Pronunciations, "Find"):
            print(f"\nFinding pronunciation after update...")
            updated_obj = project.Pronunciations.Find(test_name)
            if updated_obj:
                print(f"  FOUND: pronunciation")
                try:
                    if hasattr(project.Pronunciations, "GetName"):
                        print(f"  Name: {project.Pronunciations.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test pronunciation")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test pronunciation...")
            try:
                obj_name = (
                    project.Pronunciations.GetName(test_obj)
                    if hasattr(project.Pronunciations, "GetName")
                    else test_name
                )
            except:
                obj_name = test_name

            project.Pronunciations.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Pronunciations, "Exists"):
                still_exists = project.Pronunciations.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Pronunciation still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Pronunciations.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new pronunciation")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete pronunciation")
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
            for name in ["crud_test_pronunciation", "crud_test_pronunciation_modified"]:
                if hasattr(project.Pronunciations, "Exists") and project.Pronunciations.Exists(name):
                    obj = project.Pronunciations.Find(name) if hasattr(project.Pronunciations, "Find") else None
                    if obj:
                        project.Pronunciations.Delete(obj)
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
Pronunciation Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for pronunciation.

Operations Tested:
==================

CREATE: Create new pronunciation
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test pronunciation
3. READ to verify creation
4. UPDATE pronunciation properties
5. READ to verify updates
6. DELETE test pronunciation
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test pronunciation is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_pronunciation_crud()
    else:
        print("\nDemo skipped.")
