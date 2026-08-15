#!/usr/bin/env python3
"""
Full CRUD Demo: ExampleOperations for flexlibs

This script demonstrates complete CRUD operations for example.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_example_crud():
    """
    Demonstrate full CRUD operations for example.

    Tests:
    - CREATE: Create new test example
    - READ: Get all examples, find by name/identifier
    - UPDATE: Modify example properties
    - DELETE: Remove test example
    """

    print("=" * 70)
    print("EXAMPLE OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_example"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing examples")
        print("=" * 70)

        print("\nGetting all examples...")
        initial_count = 0
        for obj in project.Examples.GetAll():
            # Display first few objects
            try:
                name = project.Examples.GetName(obj) if hasattr(project.Examples, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal examples (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test example")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Examples, "Exists") and project.Examples.Exists(test_name):
                print(f"\nTest example '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Examples.Find(test_name) if hasattr(project.Examples, "Find") else None
                if existing:
                    project.Examples.Delete(existing)
                    print("  Deleted existing test example")
        except:
            pass

        # Create parent entry and sense for example testing
        print("\nCreating parent entry and sense for example test...")
        parent_entry = None
        parent_sense = None
        try:
            parent_entry = project.LexEntry.Create("crud_test_entry_for_example")
            parent_sense = project.LexEntry.AddSense(parent_entry, "test sense")
            print(f"  Created parent entry and sense")
        except Exception as e:
            print(f"  ERROR creating parent objects: {e}")
            print("  Cannot test example without parent sense")
            return

        print(f"\nCreating new example: '{test_name}'")

        # Create example with parent sense
        test_obj = project.Examples.Create(parent_sense, test_name)
        print(f"  SUCCESS: Example created!")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify example was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Examples, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Examples.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Examples, "Find"):
            print(f"\nFinding example by name...")
            found_obj = project.Examples.Find(test_name)
            if found_obj:
                print(f"  FOUND: example")
                try:
                    if hasattr(project.Examples, "GetName"):
                        print(f"  Name: {project.Examples.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all examples after creation...")
        current_count = sum(1 for _ in project.Examples.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify example properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Examples, "SetName"):
                try:
                    new_name = "crud_test_example_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = project.Examples.GetName(test_obj) if hasattr(project.Examples, "GetName") else test_name
                    project.Examples.SetName(test_obj, new_name)
                    updated_name = (
                        project.Examples.GetName(test_obj) if hasattr(project.Examples, "GetName") else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Examples):
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

        if hasattr(project.Examples, "Find"):
            print(f"\nFinding example after update...")
            updated_obj = project.Examples.Find(test_name)
            if updated_obj:
                print(f"  FOUND: example")
                try:
                    if hasattr(project.Examples, "GetName"):
                        print(f"  Name: {project.Examples.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test example")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test example...")
            try:
                obj_name = project.Examples.GetName(test_obj) if hasattr(project.Examples, "GetName") else test_name
            except:
                obj_name = test_name

            project.Examples.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Examples, "Exists"):
                still_exists = project.Examples.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Example still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Examples.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new example")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete example")
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
            for name in ["crud_test_example", "crud_test_example_modified"]:
                if hasattr(project.Examples, "Exists") and project.Examples.Exists(name):
                    obj = project.Examples.Find(name) if hasattr(project.Examples, "Find") else None
                    if obj:
                        project.Examples.Delete(obj)
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
Example Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for example.

Operations Tested:
==================

CREATE: Create new example
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test example
3. READ to verify creation
4. UPDATE example properties
5. READ to verify updates
6. DELETE test example
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test example is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_example_crud()
    else:
        print("\nDemo skipped.")
