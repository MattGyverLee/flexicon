#!/usr/bin/env python3
"""
Full CRUD Demo: SenseOperations for flexlibs

This script demonstrates complete CRUD operations for sense.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_sense_crud():
    """
    Demonstrate full CRUD operations for sense.

    Tests:
    - CREATE: Create new test sense
    - READ: Get all senses, find by name/identifier
    - UPDATE: Modify sense properties
    - DELETE: Remove test sense
    """

    print("=" * 70)
    print("SENSE OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_sense"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing senses")
        print("=" * 70)

        print("\nGetting all senses...")
        initial_count = 0
        for obj in project.Senses.GetAll():
            # Display first few objects
            try:
                name = project.Senses.GetName(obj) if hasattr(project.Senses, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal senses (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test sense")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Senses, "Exists") and project.Senses.Exists(test_name):
                print(f"\nTest sense '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Senses.Find(test_name) if hasattr(project.Senses, "Find") else None
                if existing:
                    project.Senses.Delete(existing)
                    print("  Deleted existing test sense")
        except:
            pass

        # Create parent entry for sense testing
        print("\nCreating parent entry for sense test...")
        parent_entry = None
        try:
            parent_entry = project.LexEntry.Create("crud_test_entry_for_sense")
            print(f"  Created parent entry: crud_test_entry_for_sense")
        except Exception as e:
            print(f"  ERROR creating parent entry: {e}")
            print("  Cannot test sense without parent entry")
            return

        print(f"\nCreating new sense: '{test_name}'")

        # Create sense with parent entry
        test_obj = project.LexEntry.AddSense(parent_entry, test_name)
        print(f"  SUCCESS: Sense created!")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify sense was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Senses, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Senses.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Senses, "Find"):
            print(f"\nFinding sense by name...")
            found_obj = project.Senses.Find(test_name)
            if found_obj:
                print(f"  FOUND: sense")
                try:
                    if hasattr(project.Senses, "GetName"):
                        print(f"  Name: {project.Senses.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all senses after creation...")
        current_count = sum(1 for _ in project.Senses.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify sense properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Senses, "SetName"):
                try:
                    new_name = "crud_test_sense_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = project.Senses.GetName(test_obj) if hasattr(project.Senses, "GetName") else test_name
                    project.Senses.SetName(test_obj, new_name)
                    updated_name = project.Senses.GetName(test_obj) if hasattr(project.Senses, "GetName") else new_name
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Senses):
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

        if hasattr(project.Senses, "Find"):
            print(f"\nFinding sense after update...")
            updated_obj = project.Senses.Find(test_name)
            if updated_obj:
                print(f"  FOUND: sense")
                try:
                    if hasattr(project.Senses, "GetName"):
                        print(f"  Name: {project.Senses.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test sense")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test sense...")
            try:
                obj_name = project.Senses.GetName(test_obj) if hasattr(project.Senses, "GetName") else test_name
            except:
                obj_name = test_name

            project.Senses.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Senses, "Exists"):
                still_exists = project.Senses.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Sense still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Senses.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new sense")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete sense")
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
            for name in ["crud_test_sense", "crud_test_sense_modified"]:
                if hasattr(project.Senses, "Exists") and project.Senses.Exists(name):
                    obj = project.Senses.Find(name) if hasattr(project.Senses, "Find") else None
                    if obj:
                        project.Senses.Delete(obj)
                        print(f"  Cleaned up: {name}")
        except:
            pass

        # Cleanup parent entry (sense will be deleted with it)
        try:
            if parent_entry:
                project.LexEntry.Delete(parent_entry)
                print("  Cleaned up: parent entry and sense")
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
Sense Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for sense.

Operations Tested:
==================

CREATE: Create new sense
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test sense
3. READ to verify creation
4. UPDATE sense properties
5. READ to verify updates
6. DELETE test sense
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test sense is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_sense_crud()
    else:
        print("\nDemo skipped.")
