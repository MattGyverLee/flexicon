#!/usr/bin/env python3
"""
Full CRUD Demo: EnvironmentOperations for flexlibs

This script demonstrates complete CRUD operations for phonological environments.
Performs actual create, read, update, and delete operations on test data.

Author: FlexTools Development Team
Date: 2026-02-28
Version: 2.3.0
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup


def demo_environment_crud():
    """
    Demonstrate full CRUD operations for phonological environments.

    Tests:
    - CREATE: Create new test environment
    - READ: Get all environments, find by name
    - UPDATE: Modify environment name and string representation
    - DELETE: Remove test environment
    """

    print("=" * 70)
    print("PHONOLOGICAL ENVIRONMENT OPERATIONS - FULL CRUD TEST")
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

    test_env = None
    test_name = "crud_test_environment"

    try:
        # ==================== READ: Initial state ====================
        print("\n" + "=" * 70)
        print("STEP 1: READ - Get existing environments")
        print("=" * 70)

        print("\nGetting all environments...")
        initial_count = 0
        for env in project.Environments.GetAll():
            name = project.Environments.GetName(env)
            str_rep = project.Environments.GetStringRepresentation(env)
            print(f"  - {name}: {str_rep}")
            initial_count += 1
            if initial_count >= 5:
                break

        print(f"\nTotal environments (showing first 5): {initial_count}")

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("STEP 2: CREATE - Create new test environment")
        print("=" * 70)

        # Check if test environment already exists
        if project.Environments.Exists(test_name):
            print(f"\nTest environment '{test_name}' already exists")
            print("Deleting existing one first...")
            existing = project.Environments.Find(test_name)
            if existing:
                project.Environments.Delete(existing)
                print("  Deleted existing test environment")

        # Create new environment
        print(f"\nCreating new environment: '{test_name}'")
        print("  String representation: '/ _ #'")

        test_env = project.Environments.Create(name=test_name, string_representation="/ _ #")

        if test_env:
            print(f"  SUCCESS: Environment created!")
            print(f"  Name: {project.Environments.GetName(test_env)}")
            print(f"  String: {project.Environments.GetStringRepresentation(test_env)}")
        else:
            print("  FAILED: Could not create environment")
            return

        # ==================== READ: Verify creation ====================
        print("\n" + "=" * 70)
        print("STEP 3: READ - Verify environment was created")
        print("=" * 70)

        # Test Exists
        print(f"\nChecking if '{test_name}' exists...")
        exists = project.Environments.Exists(test_name)
        print(f"  Exists: {exists}")

        # Test Find
        print(f"\nFinding environment by name...")
        found_env = project.Environments.Find(test_name)
        if found_env:
            print(f"  FOUND: {project.Environments.GetName(found_env)}")
            print(f"  String: {project.Environments.GetStringRepresentation(found_env)}")
        else:
            print("  NOT FOUND")

        # Count environments after creation
        print("\nCounting all environments after creation...")
        current_count = sum(1 for _ in project.Environments.GetAll())
        print(f"  Count before: {initial_count}")
        print(f"  Count after:  {current_count}")
        print(f"  Difference:   +{current_count - initial_count}")

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("STEP 4: UPDATE - Modify environment properties")
        print("=" * 70)

        if test_env:
            # Update name
            new_name = "crud_test_environment_modified"
            print(f"\nUpdating name to: '{new_name}'")

            old_name = project.Environments.GetName(test_env)
            project.Environments.SetName(test_env, new_name)
            updated_name = project.Environments.GetName(test_env)

            print(f"  Old name: {old_name}")
            print(f"  New name: {updated_name}")

            # Update string representation
            new_string = "/ V _ #"
            print(f"\nUpdating string representation to: '{new_string}'")

            old_string = project.Environments.GetStringRepresentation(test_env)
            project.Environments.SetStringRepresentation(test_env, new_string)
            updated_string = project.Environments.GetStringRepresentation(test_env)

            print(f"  Old string: {old_string}")
            print(f"  New string: {updated_string}")

            # Verify updates
            print("\nVerifying updates...")
            if updated_name == new_name:
                print("  Name update: SUCCESS")
            else:
                print(f"  Name update: FAILED (got '{updated_name}')")

            if updated_string == new_string:
                print("  String update: SUCCESS")
            else:
                print(f"  String update: FAILED (got '{updated_string}')")

        # ==================== READ: Verify updates ====================
        print("\n" + "=" * 70)
        print("STEP 5: READ - Verify updates persisted")
        print("=" * 70)

        # Re-find with new name
        print(f"\nFinding environment by updated name...")
        updated_env = project.Environments.Find("crud_test_environment_modified")
        if updated_env:
            print(f"  FOUND: {project.Environments.GetName(updated_env)}")
            print(f"  String: {project.Environments.GetStringRepresentation(updated_env)}")
        else:
            print("  NOT FOUND - Update may not have persisted")

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("STEP 6: DELETE - Remove test environment")
        print("=" * 70)

        if test_env:
            print(f"\nDeleting test environment...")
            env_name = project.Environments.GetName(test_env)

            project.Environments.Delete(test_env)
            print(f"  Deleted: {env_name}")

            # Verify deletion
            print("\nVerifying deletion...")
            still_exists = project.Environments.Exists(env_name)
            print(f"  Still exists: {still_exists}")

            if not still_exists:
                print("  DELETE: SUCCESS")
            else:
                print("  DELETE: FAILED - Environment still exists")

            # Count after deletion
            final_count = sum(1 for _ in project.Environments.GetAll())
            print(f"\n  Count after delete: {final_count}")
            print(f"  Back to initial:    {final_count == initial_count}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("CRUD TEST SUMMARY")
        print("=" * 70)
        print("\nOperations tested:")
        print("  [CREATE] Create new environment")
        print("  [READ]   GetAll, Find, Exists, GetName, GetStringRepresentation")
        print("  [UPDATE] SetName, SetStringRepresentation")
        print("  [DELETE] Delete environment")
        print("\nTest completed successfully!")

    except Exception as e:
        print(f"\n\nERROR during CRUD test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup: Ensure test environment is removed
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)

        try:
            for name in ["crud_test_environment", "crud_test_environment_modified"]:
                if project.Environments.Exists(name):
                    env = project.Environments.Find(name)
                    if env:
                        project.Environments.Delete(env)
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
Phonological Environment Operations - Full CRUD Demo
=====================================================

This demonstrates COMPLETE CRUD operations for phonological environments.

Operations Tested:
==================

CREATE (1 method):
  - Create(name, string_representation)

READ (5 methods):
  - GetAll()                      - Iterate all environments
  - Find(name)                    - Find by name
  - Exists(name)                  - Check existence
  - GetName(env)                  - Get environment name
  - GetStringRepresentation(env)  - Get environment string

UPDATE (2 methods):
  - SetName(env, name)                        - Update name
  - SetStringRepresentation(env, string)      - Update string

DELETE (1 method):
  - Delete(env)                   - Remove environment

Test Flow:
==========
1. READ initial state
2. CREATE new test environment
3. READ to verify creation
4. UPDATE environment properties
5. READ to verify updates
6. DELETE test environment
7. Verify deletion

Requirements:
  - FLEx project with write access
  - Python.NET runtime

WARNING: This demo modifies the database!
         Test environment is created and deleted during the demo.
    """
    )

    response = input("\nRun CRUD demo? (y/N): ")
    if response.lower() == "y":
        demo_environment_crud()
    else:
        print("\nDemo skipped.")
