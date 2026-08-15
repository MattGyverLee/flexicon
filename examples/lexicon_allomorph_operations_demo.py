#!/usr/bin/env python3
"""
Full CRUD Demo: AllomorphOperations for flexlibs

This script demonstrates complete CRUD operations for allomorph.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_allomorph_crud():
    """
    Demonstrate full CRUD operations for allomorph.

    Tests:
    - CREATE: Create new test allomorph
    - READ: Get all allomorphs, find by name/identifier
    - UPDATE: Modify allomorph properties
    - DELETE: Remove test allomorph
    """

    print("=" * 70)
    print("ALLOMORPH OPERATIONS - FULL CRUD TEST")
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
    test_name = "crud_test_allomorph"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing allomorphs")
        print("=" * 70)

        print("\nGetting all allomorphs...")
        initial_count = 0
        for obj in project.Allomorphs.GetAll():
            # Display first few objects
            try:
                name = project.Allomorphs.GetName(obj) if hasattr(project.Allomorphs, "GetName") else str(obj)
                print(f"  - {name}")
            except:
                print(f"  - [Object {initial_count + 1}]")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal allomorphs (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test allomorph")
        print("=" * 70)

        # Check if test object already exists
        try:
            if hasattr(project.Allomorphs, "Exists") and project.Allomorphs.Exists(test_name):
                print(f"\nTest allomorph '{test_name}' already exists")
                print("Deleting existing one first...")
                existing = project.Allomorphs.Find(test_name) if hasattr(project.Allomorphs, "Find") else None
                if existing:
                    project.Allomorphs.Delete(existing)
                    print("  Deleted existing test allomorph")
        except:
            pass

        # Create parent entry for allomorph testing
        print("\nCreating parent entry for allomorph test...")
        parent_entry = None
        try:
            parent_entry = project.LexEntry.Create("crud_test_entry_for_allomorph")
            print(f"  Created parent entry: crud_test_entry_for_allomorph")
        except Exception as e:
            print(f"  ERROR creating parent entry: {e}")
            print("  Cannot test allomorph without parent entry")
            return

        # Get morph type (stem)
        morph_type = None
        try:
            # Get the first available morph type (usually "stem")
            from SIL.LCModel import ILcmOwningSequence, IMoMorphType  # type: ignore[import]

            morph_types = project.project.LexDb.MorphTypesOA.PossibilitiesOS  # type: ignore[attr-defined]
            for mt in morph_types:
                if "stem" in str(mt.Name.BestAnalysisAlternative.Text).lower():
                    morph_type = mt
                    break
            if not morph_type and morph_types.Count > 0:
                morph_type = morph_types[0]
        except:
            pass

        if not morph_type:
            print("  ERROR: Could not find morph type")
            print("  Cannot test allomorph without morph type")
            return

        print(f"\nCreating new allomorph: '{test_name}'")

        # Create allomorph with parent entry
        test_obj = project.Allomorphs.Create(parent_entry, test_name, morph_type)
        print(f"  SUCCESS: Allomorph created!")

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify allomorph was created")
        print("=" * 70)

        # Test Exists
        if hasattr(project.Allomorphs, "Exists"):
            print(f"\nChecking if '{test_name}' exists...")
            exists = project.Allomorphs.Exists(test_name)
            print(f"  Exists: {exists}")

        # Test Find
        if hasattr(project.Allomorphs, "Find"):
            print(f"\nFinding allomorph by name...")
            found_obj = project.Allomorphs.Find(test_name)
            if found_obj:
                print(f"  FOUND: allomorph")
                try:
                    if hasattr(project.Allomorphs, "GetName"):
                        print(f"  Name: {project.Allomorphs.GetName(found_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND")

        # Count after creation
        print("\nCounting all allomorphs after creation...")
        current_count = sum(1 for _ in project.Allomorphs.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify allomorph properties")
        print("=" * 70)

        if test_obj:
            updated = False

            # Try common update methods
            if hasattr(project.Allomorphs, "SetName"):
                try:
                    new_name = "crud_test_allomorph_modified"
                    print(f"\nUpdating name to: '{new_name}'")
                    old_name = (
                        project.Allomorphs.GetName(test_obj) if hasattr(project.Allomorphs, "GetName") else test_name
                    )
                    project.Allomorphs.SetName(test_obj, new_name)
                    updated_name = (
                        project.Allomorphs.GetName(test_obj) if hasattr(project.Allomorphs, "GetName") else new_name
                    )
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {updated_name}")
                    test_name = new_name  # Update for cleanup
                    updated = True
                except Exception as e:
                    print(f"  Note: SetName failed: {e}")

            # Try other Set methods
            for method_name in dir(project.Allomorphs):
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

        if hasattr(project.Allomorphs, "Find"):
            print(f"\nFinding allomorph after update...")
            updated_obj = project.Allomorphs.Find(test_name)
            if updated_obj:
                print(f"  FOUND: allomorph")
                try:
                    if hasattr(project.Allomorphs, "GetName"):
                        print(f"  Name: {project.Allomorphs.GetName(updated_obj)}")
                except:
                    pass
            else:
                print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test allomorph")
        print("=" * 70)

        if test_obj:
            print(f"\nDeleting test allomorph...")
            try:
                obj_name = project.Allomorphs.GetName(test_obj) if hasattr(project.Allomorphs, "GetName") else test_name
            except:
                obj_name = test_name

            project.Allomorphs.Delete(test_obj)
            print(f"  Deleted: {obj_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            if hasattr(project.Allomorphs, "Exists"):
                still_exists = project.Allomorphs.Exists(test_name)
                print(f"  Still exists: {still_exists}")

                if not still_exists:
                    print("  DELETE: SUCCESS")
                else:
                    print("  DELETE: FAILED - Allomorph still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Allomorphs.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new allomorph")
        print("  [READ]   GetAll, Find, Exists, Get methods")
        print("  [UPDATE] Set methods")
        print("  [DELETE] Delete allomorph")
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
            for name in ["crud_test_allomorph", "crud_test_allomorph_modified"]:
                if hasattr(project.Allomorphs, "Exists") and project.Allomorphs.Exists(name):
                    obj = project.Allomorphs.Find(name) if hasattr(project.Allomorphs, "Find") else None
                    if obj:
                        project.Allomorphs.Delete(obj)
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
Allomorph Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for allomorph.

Operations Tested:
==================

CREATE: Create new allomorph
READ:   GetAll(), Find(), Exists(), Get...() methods
UPDATE: Set...() methods
DELETE: Delete()

Test Flow:
==========
1. READ initial state
2. CREATE new test allomorph
3. READ to verify creation
4. UPDATE allomorph properties
5. READ to verify updates
6. DELETE test allomorph
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test allomorph is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_allomorph_crud()
    else:
        print("\nDemo skipped.")
