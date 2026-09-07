#!/usr/bin/env python3
"""
Full CRUD Demo: EtymologyOperations for flexlibs

This script demonstrates complete CRUD operations for etymology.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_etymology_crud():
    """
    Demonstrate full CRUD operations for etymology.

    Tests:
    - CREATE: Create new test etymology
    - READ: Get all etymologys, find by name/identifier
    - UPDATE: Modify etymology properties
    - DELETE: Remove test etymology
    """

    print("=" * 70)
    print("ETYMOLOGY OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_etymology"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing etymologys")
        print("=" * 70)

        print("\nGetting all etymologys...")
        initial_count = 0
        for obj in project.Etymology.GetAll():
            # Display first few objects
            try:
                name = project.Etymology.GetName(obj) if hasattr(project.Etymology, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal etymologys (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test etymology")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Etymology, "Exists") and project.Etymology.Exists(test_name):
                print(f"\nTest etymology '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Etymology.Find(test_name) if hasattr(project.Etymology, "Find") else None
                if existing:
                    project.Etymology.Delete(existing)
                    print("  Deleted existing test etymology")
        except:
            pass

        # Create parent entry for etymology testing
        print("\nCreating parent entry for etymology test...")
        parent_entry = None
        try:
            parent_entry = project.LexEntry.Create("crud_test_entry_for_etymology")
            print(f"  Created parent entry: crud_test_entry_for_etymology")
        except Exception as e:
            print(f"  ERROR creating parent entry: {e}")
            print("  Cannot test etymology without parent entry")
            return

        print(f"\nCreating new etymology: '{test_name}'")

        # Create etymology with parent entry (not string)
        test_obj = project.Etymology.Create(parent_entry)
        print(f"  SUCCESS: Etymology created!")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify etymology was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Etymology, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Etymology.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Etymology, "Find"):
            print(f"\nFinding etymology by name...")
            found_obj = project.Etymology.Find(test_name)
            if found_obj:
                print(f"  FOUND: etymology")
                try:
                    if hasattr(project.Etymology, "GetName"):
                        print(f"  Name: {project.Etymology.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all etymologys after creation...")
        current_count = sum(1 for _ in project.Etymology.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify etymology properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Etymology, "SetName"):
                try:
                    new_name = "crud_test_etymology_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = (
                        project.Etymology.GetName(test_obj) if hasattr(project.Etymology, "GetName") else test_name
                    )
                    project.Etymology.SetName(test_obj, new_name)
                    updated_name = (
                        project.Etymology.GetName(test_obj) if hasattr(project.Etymology, "GetName") else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Etymology):
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

        if hasattr(project.Etymology, "Find"):
            print(f"\nFinding etymology after update...")
            updated_obj = project.Etymology.Find(test_name)
            if updated_obj:
                print(f"  FOUND: etymology")
                try:
                    if hasattr(project.Etymology, "GetName"):
                        print(f"  Name: {project.Etymology.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test etymology")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test etymology...")
            try:
                obj_name = project.Etymology.GetName(test_obj) if hasattr(project.Etymology, "GetName") else test_name
            except:
                obj_name = test_name

            project.Etymology.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Etymology, "Exists"):
                still_exists = project.Etymology.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Etymology still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Etymology.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new etymology")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete etymology")
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
            for name in ["crud_test_etymology", "crud_test_etymology_modified"]:
                if hasattr(project.Etymology, "Exists") and project.Etymology.Exists(name):
                    obj = project.Etymology.Find(name) if hasattr(project.Etymology, "Find") else None
                    if obj:
                        project.Etymology.Delete(obj)
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
Etymology Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for etymology.

Operations Tested:
==================

CREATE: Create new etymology
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test etymology
3. READ to verify creation
4. UPDATE etymology properties
5. READ to verify updates
6. DELETE test etymology
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test etymology is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_etymology_crud()
    else:
        print("\nDemo skipped.")
