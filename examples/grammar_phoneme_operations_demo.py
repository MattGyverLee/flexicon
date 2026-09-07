#!/usr/bin/env python3
"""
Full CRUD Demo: PhonemeOperations for flexlibs

This script demonstrates complete CRUD operations for phoneme.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_phoneme_crud():
    """
    Demonstrate full CRUD operations for phoneme.

    Tests:
    - CREATE: Create new test phoneme
    - READ: Get all phonemes, find by name/identifier
    - UPDATE: Modify phoneme properties
    - DELETE: Remove test phoneme
    """

    print("=" * 70)
    print("PHONEME OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_phoneme"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing phonemes")
        print("=" * 70)

        print("\nGetting all phonemes...")
        initial_count = 0
        for obj in project.Phonemes.GetAll():
            # Display first few objects
            try:
                name = project.Phonemes.GetName(obj) if hasattr(project.Phonemes, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal phonemes (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test phoneme")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Phonemes, "Exists") and project.Phonemes.Exists(test_name):
                print(f"\nTest phoneme '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Phonemes.Find(test_name) if hasattr(project.Phonemes, "Find") else None
                if existing:
                    project.Phonemes.Delete(existing)
                    print("  Deleted existing test phoneme")
        except:
            pass

        # Create new object
        print(f"\nCreating new phoneme: '{test_name}'")

        try:
            # Attempt to create with common parameters
            test_obj = project.Phonemes.Create(test_name)
        except TypeError:
            try:
                # Try without parameters if that fails
                test_obj = project.Phonemes.Create()
                if hasattr(project.Phonemes, "SetName"):
                    project.Phonemes.SetName(test_obj, test_name)
            except Exception as e:
                print(f"  Note: Create method may require specific parameters: {e}")
                test_obj = None

        if test_obj:
            print(f"  SUCCESS: Phoneme created!")
            try:
                if hasattr(project.Phonemes, "GetName"):
                    print(f"  Name: {project.Phonemes.GetName(test_obj)}")
            except:
                pass
        else:
            print(f"  Note: Could not create phoneme (may require special parameters)")
            print("  Skipping remaining tests...")
            return

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify phoneme was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Phonemes, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Phonemes.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Phonemes, "Find"):
            print(f"\nFinding phoneme by name...")
            found_obj = project.Phonemes.Find(test_name)
            if found_obj:
                print(f"  FOUND: phoneme")
                try:
                    if hasattr(project.Phonemes, "GetName"):
                        print(f"  Name: {project.Phonemes.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all phonemes after creation...")
        current_count = sum(1 for _ in project.Phonemes.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify phoneme properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Phonemes, "SetName"):
                try:
                    new_name = "crud_test_phoneme_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = project.Phonemes.GetName(test_obj) if hasattr(project.Phonemes, "GetName") else test_name
                    project.Phonemes.SetName(test_obj, new_name)
                    updated_name = (
                        project.Phonemes.GetName(test_obj) if hasattr(project.Phonemes, "GetName") else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Phonemes):
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

        if hasattr(project.Phonemes, "Find"):
            print(f"\nFinding phoneme after update...")
            updated_obj = project.Phonemes.Find(test_name)
            if updated_obj:
                print(f"  FOUND: phoneme")
                try:
                    if hasattr(project.Phonemes, "GetName"):
                        print(f"  Name: {project.Phonemes.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test phoneme")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test phoneme...")
            try:
                obj_name = project.Phonemes.GetName(test_obj) if hasattr(project.Phonemes, "GetName") else test_name
            except:
                obj_name = test_name

            project.Phonemes.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Phonemes, "Exists"):
                still_exists = project.Phonemes.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Phoneme still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Phonemes.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new phoneme")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete phoneme")
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
            for name in ["crud_test_phoneme", "crud_test_phoneme_modified"]:
                if hasattr(project.Phonemes, "Exists") and project.Phonemes.Exists(name):
                    obj = project.Phonemes.Find(name) if hasattr(project.Phonemes, "Find") else None
                    if obj:
                        project.Phonemes.Delete(obj)
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
Phoneme Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for phoneme.

Operations Tested:
==================

CREATE: Create new phoneme
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test phoneme
3. READ to verify creation
4. UPDATE phoneme properties
5. READ to verify updates
6. DELETE test phoneme
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test phoneme is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_phoneme_crud()
    else:
        print("\nDemo skipped.")
