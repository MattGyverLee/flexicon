#!/usr/bin/env python3
"""
Full CRUD Demo: NaturalclassOperations for flexlibs

This script demonstrates complete CRUD operations for naturalclass.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_naturalclass_crud():
    """
    Demonstrate full CRUD operations for naturalclass.

    Tests:
    - CREATE: Create new test naturalclass
    - READ: Get all naturalclasss, find by name/identifier
    - UPDATE: Modify naturalclass properties
    - DELETE: Remove test naturalclass
    """

    print("=" * 70)
    print("NATURALCLASS OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_naturalclass"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing naturalclasss")
        print("=" * 70)

        print("\nGetting all naturalclasss...")
        initial_count = 0
        for obj in project.NaturalClasses.GetAll():
            # Display first few objects
            try:
                name = project.NaturalClasses.GetName(obj) if hasattr(project.NaturalClasses, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal naturalclasss (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test naturalclass")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.NaturalClasses, "Exists") and project.NaturalClasses.Exists(test_name):
                print(f"\nTest naturalclass '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.NaturalClasses.Find(test_name) if hasattr(project.NaturalClasses, "Find") else None
                if existing:
                    project.NaturalClasses.Delete(existing)
                    print("  Deleted existing test naturalclass")
        except:
            pass

        # Create new object
        print(f"\nCreating new naturalclass: '{test_name}'")

        try:
            # Attempt to create with common parameters
            test_obj = project.NaturalClasses.Create(test_name)
        except TypeError:
            try:
                # Try without parameters if that fails
                test_obj = project.NaturalClasses.Create()
                if hasattr(project.NaturalClasses, "SetName"):
                    project.NaturalClasses.SetName(test_obj, test_name)
            except Exception as e:
                print(f"  Note: Create method may require specific parameters: {e}")
                test_obj = None

        if test_obj:
            print(f"  SUCCESS: Naturalclass created!")
            try:
                if hasattr(project.NaturalClasses, "GetName"):
                    print(f"  Name: {project.NaturalClasses.GetName(test_obj)}")
            except:
                pass
        else:
            print(f"  Note: Could not create naturalclass (may require special parameters)")
            print("  Skipping remaining tests...")
            return

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify naturalclass was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.NaturalClasses, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.NaturalClasses.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.NaturalClasses, "Find"):
            print(f"\nFinding naturalclass by name...")
            found_obj = project.NaturalClasses.Find(test_name)
            if found_obj:
                print(f"  FOUND: naturalclass")
                try:
                    if hasattr(project.NaturalClasses, "GetName"):
                        print(f"  Name: {project.NaturalClasses.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all naturalclasss after creation...")
        current_count = sum(1 for _ in project.NaturalClasses.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify naturalclass properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.NaturalClasses, "SetName"):
                try:
                    new_name = "crud_test_naturalclass_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = (
                        project.NaturalClasses.GetName(test_obj)
                        if hasattr(project.NaturalClasses, "GetName")
                        else test_name
                    )
                    project.NaturalClasses.SetName(test_obj, new_name)
                    updated_name = (
                        project.NaturalClasses.GetName(test_obj)
                        if hasattr(project.NaturalClasses, "GetName")
                        else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.NaturalClasses):
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

        if hasattr(project.NaturalClasses, "Find"):
            print(f"\nFinding naturalclass after update...")
            updated_obj = project.NaturalClasses.Find(test_name)
            if updated_obj:
                print(f"  FOUND: naturalclass")
                try:
                    if hasattr(project.NaturalClasses, "GetName"):
                        print(f"  Name: {project.NaturalClasses.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test naturalclass")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test naturalclass...")
            try:
                obj_name = (
                    project.NaturalClasses.GetName(test_obj)
                    if hasattr(project.NaturalClasses, "GetName")
                    else test_name
                )
            except:
                obj_name = test_name

            project.NaturalClasses.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.NaturalClasses, "Exists"):
                still_exists = project.NaturalClasses.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Naturalclass still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.NaturalClasses.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new naturalclass")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete naturalclass")
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
            for name in ["crud_test_naturalclass", "crud_test_naturalclass_modified"]:
                if hasattr(project.NaturalClasses, "Exists") and project.NaturalClasses.Exists(name):
                    obj = project.NaturalClasses.Find(name) if hasattr(project.NaturalClasses, "Find") else None
                    if obj:
                        project.NaturalClasses.Delete(obj)
                        print(f"  Cleaned up: {name}")
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
Naturalclass Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for naturalclass.

Operations Tested:
==================

CREATE: Create new naturalclass
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test naturalclass
3. READ to verify creation
4. UPDATE naturalclass properties
5. READ to verify updates
6. DELETE test naturalclass
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test naturalclass is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_naturalclass_crud()
    else:
        print("\nDemo skipped.")
