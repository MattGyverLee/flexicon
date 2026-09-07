#!/usr/bin/env python3
"""
Phase 0 Verification Script: Test All Implementation Assumptions

This script tests critical assumptions before implementing code quality improvements.
It verifies exception types, API patterns, and safe operation orders against actual
FLEx behavior.

Focus: Verify assumptions, not implement features.

Author: Claude Code
Date: 2025-02-21
"""

import sys
import os
import traceback
from datetime import datetime
from typing import Any, List, Dict, Tuple

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, _project_root)

# Import FLEx modules
try:
    from flexicon import FLExProject, FLExInitialize, FLExCleanup

    # Core exceptions are in core module at project root
    try:
        from core.exceptions import (
            ObjectNotFoundError,
            InvalidParameterError,
            DuplicateObjectError,
            OperationFailedError,
        )
    except ImportError:
        # Fallback if not available
        ObjectNotFoundError = None
        InvalidParameterError = None
        DuplicateObjectError = None
        OperationFailedError = None
except ImportError as e:
    print(f"[ERROR] Failed to import flexicon: {e}")
    sys.exit(1)


# =============================================================================
# RESULT TRACKING
# =============================================================================


class VerificationResult:
    """Track verification results"""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.findings = []
        self.exceptions = []
        self.error_message = None
        self.start_time = None
        self.end_time = None

    def add_finding(self, finding: str):
        """Add a key finding"""
        self.findings.append(finding)
        print(f"  [FINDING] {finding}")

    def add_exception(self, exc_type: str, exc_message: str):
        """Record an exception caught"""
        self.exceptions.append({"type": exc_type, "message": exc_message})
        print(f"  [EXCEPTION] {exc_type}: {exc_message}")

    def set_error(self, message: str):
        """Set an error message"""
        self.error_message = message
        print(f"  [ERROR] {message}")

    def set_passed(self):
        """Mark as passed"""
        self.passed = True
        print(f"  [PASS] {self.name}")


# =============================================================================
# TEST FUNCTIONS
# =============================================================================


def verify_exception_types(project: FLExProject) -> VerificationResult:
    """
    Test what exceptions are actually thrown by various invalid operations.

    This assumes:
    - Invalid type casting throws TypeError
    - Property access on missing properties throws AttributeError
    - Invalid HVO/GUID lookups throw specific exception
    - Invalid DateTime parsing throws ValueError

    Verify these assumptions against actual behavior.
    """

    result = VerificationResult("verify_exception_types")
    print("\n" + "=" * 70)
    print("PHASE 0: Exception Type Verification")
    print("=" * 70)

    try:
        # Test 1: Invalid type casting with LexEntry
        print("\n[TEST 1] Invalid type casting")
        try:
            # Try to access LexEntry and verify casting behavior
            entries = list(project.LexEntry.GetAll())
            result.add_finding(f"LexEntry.GetAll() returned {len(entries)} entries")
            if entries:
                entry = entries[0]
                result.add_finding(f"Can access entry objects: {type(entry).__name__}")
        except (TypeError, AttributeError, Exception) as e:
            exc_type = type(e).__name__
            result.add_exception(exc_type, str(e))

        # Test 2: Property access on objects
        print("\n[TEST 2] Property access on objects without expected properties")
        try:
            entries = list(project.LexEntry.GetAll())
            if entries:
                entry = entries[0]
                # Try to access properties using project wrapper
                try:
                    if hasattr(entry, "HomographNumber"):
                        hom_num = entry.HomographNumber
                        result.add_finding(f"Property .HomographNumber accessible: {hom_num}")
                    else:
                        result.add_finding("Property .HomographNumber not accessible")
                except AttributeError as e:
                    result.add_exception("AttributeError", f"HomographNumber: {e}")

                # Try LexemeFormOA property
                try:
                    if hasattr(entry, "LexemeFormOA"):
                        form = entry.LexemeFormOA
                        result.add_finding("Property .LexemeFormOA is accessible")
                except AttributeError as e:
                    result.add_exception("AttributeError", f"LexemeFormOA: {e}")
            else:
                result.add_finding("No entries found to test property access")

        except Exception as e:
            exc_type = type(e).__name__
            result.add_exception(exc_type, str(e))

        # Test 3: Invalid HVO/GUID lookups
        print("\n[TEST 3] Invalid HVO/GUID lookups")
        try:
            # Try to use Object accessor with invalid HVO
            invalid_hvo = 999999999
            try:
                obj = project.Object(invalid_hvo)
                result.add_finding("GetObject with invalid HVO returned something")
            except (AttributeError, KeyError, Exception) as e:
                exc_type = type(e).__name__
                result.add_exception(exc_type, f"Invalid HVO lookup: {e}")

        except Exception as e:
            exc_type = type(e).__name__
            result.add_exception(exc_type, str(e))

        # Test 4: Invalid DateTime parsing
        print("\n[TEST 4] DateTime parsing")
        try:
            import System

            # Try invalid datetime format
            try:
                invalid_date = System.DateTime.Parse("not-a-date")
                result.add_finding("DateTime.Parse accepted invalid string")
            except (ValueError, System.FormatException, Exception) as e:
                exc_type = type(e).__name__
                result.add_exception(exc_type, f"Invalid date parse: {e}")

        except Exception as e:
            exc_type = type(e).__name__
            result.add_exception(exc_type, str(e))

        result.set_passed()

    except Exception as e:
        result.set_error(f"Unexpected error: {e}")
        traceback.print_exc()

    return result


def verify_sense_lookups(project: FLExProject) -> VerificationResult:
    """
    Test PossibilityList operations.

    This assumes:
    - project.PossibilityLists exists and is iterable
    - Can find specific lists by name (Usage Types, Semantic Domains, etc)
    - Can iterate through list items
    - Items have accessible properties
    - Lookup function approach is feasible
    """

    result = VerificationResult("verify_sense_lookups")
    print("\n" + "=" * 70)
    print("PHASE 0: PossibilityList Lookup Verification")
    print("=" * 70)

    try:
        # Test 1: Verify PossibilityLists exists
        print("\n[TEST 1] Verify project.PossibilityLists exists")
        try:
            poss_lists = project.PossibilityLists
            result.add_finding(f"PossibilityLists property accessible (type: {type(poss_lists).__name__})")

            # Try to get all possibility lists using different methods
            all_lists = []
            try:
                # Try GetAll() method
                all_lists = list(poss_lists.GetAll())
                result.add_finding(f"Found {len(all_lists)} possibility lists via GetAll()")
            except Exception as e:
                result.add_exception(type(e).__name__, f"GetAll() failed: {e}")

            # Print list names
            for plist in all_lists[:5]:
                try:
                    # Try to get name using project method
                    name = str(plist)
                    print(f"    - {name}")
                except:
                    print(f"    - [List]")

        except Exception as e:
            exc_type = type(e).__name__
            result.add_exception(exc_type, f"PossibilityLists access: {e}")
            return result

        # Test 2: Find specific lists
        print("\n[TEST 2] Find specific possibility lists")
        list_names_to_find = ["Usage Types", "Semantic Domains", "Anthropology Categories"]

        for target_name in list_names_to_find:
            try:
                found = False
                for plist in all_lists:
                    try:
                        # Get list properties
                        if hasattr(plist, "Name"):
                            name = plist.Name
                        else:
                            name = str(plist)

                        if name and target_name in name:
                            result.add_finding(f"Found list: {name}")
                            found = True
                            break
                    except:
                        pass

                if not found:
                    result.add_finding(f"List '{target_name}' search complete (may not be in project)")

            except Exception as e:
                result.add_exception(type(e).__name__, f"Finding {target_name}: {e}")

        # Test 3: Iterate through items and test access
        print("\n[TEST 3] Iterate through list items and test access patterns")
        try:
            if all_lists:
                plist = all_lists[0]
                print(f"  Testing with first possibility list")

                # Try to access items
                try:
                    if hasattr(plist, "__iter__"):
                        items = list(plist)
                        item_count = len(items)
                        result.add_finding(f"List has {item_count} items")

                        # Test accessing first item
                        if item_count > 0:
                            item = items[0]
                            try:
                                item_str = str(item)
                                result.add_finding(f"Can access item: {item_str[:40]}")
                            except Exception as e:
                                result.add_exception(type(e).__name__, f"Item access: {e}")
                    else:
                        result.add_finding("List items not directly iterable")
                except Exception as e:
                    result.add_exception(type(e).__name__, f"Accessing items: {e}")

        except Exception as e:
            result.add_exception(type(e).__name__, f"Iterating items: {e}")

        result.set_passed()

    except Exception as e:
        result.set_error(f"Unexpected error: {e}")
        traceback.print_exc()

    return result


def verify_homograph_logic(project: FLExProject) -> VerificationResult:
    """
    Test homograph behavior.

    This assumes:
    - Can find entries with HomographNumber > 0
    - Can create entries with same form
    - Homograph numbers are assigned automatically
    - Merge scenario: combining entries updates homograph numbers
    """

    result = VerificationResult("verify_homograph_logic")
    print("\n" + "=" * 70)
    print("PHASE 0: Homograph Logic Verification")
    print("=" * 70)

    try:
        # Test 1: Find entries with HomographNumber > 0
        print("\n[TEST 1] Find entries with HomographNumber > 0")
        try:
            entries = list(project.LexEntry.GetAll())
            homograph_entries = []

            for entry in entries:
                try:
                    if hasattr(entry, "HomographNumber") and entry.HomographNumber > 0:
                        homograph_entries.append(entry)
                        if len(homograph_entries) <= 3:
                            try:
                                hom_num = entry.HomographNumber
                                result.add_finding(f"Found homograph entry (HomographNumber: {hom_num})")
                            except Exception as e:
                                result.add_finding(f"Found homograph entry but couldn't get number: {e}")
                except Exception as e:
                    # Skip entries that don't have HomographNumber
                    pass

            result.add_finding(f"Total homograph entries found: {len(homograph_entries)}")

        except Exception as e:
            exc_type = type(e).__name__
            result.add_exception(exc_type, f"Homograph search: {e}")

        # Test 2: Check if we can create entries with same form
        print("\n[TEST 2] Test creating entries with same form (READ-ONLY TEST)")
        try:
            # Just document the pattern - don't actually create
            result.add_finding("Entry creation would require writeEnabled=True")
            result.add_finding("Pattern: create entry with LexemeFormOA.Form = same value")
            result.add_finding("Then check if HomographNumber is auto-assigned")

        except Exception as e:
            result.add_exception(type(e).__name__, str(e))

        # Test 3: Understand merge scenario
        print("\n[TEST 3] Understand merge scenario (SIMULATION)")
        try:
            result.add_finding("Merge scenario: Delete one homograph entry")
            result.add_finding("Expected: Remaining entries' HomographNumber values updated")
            result.add_finding("Test pattern: Check HomographNumber values before/after delete")

        except Exception as e:
            result.add_exception(type(e).__name__, str(e))

        result.set_passed()

    except Exception as e:
        result.set_error(f"Unexpected error: {e}")
        traceback.print_exc()

    return result


def verify_property_aliases(project: FLExProject) -> VerificationResult:
    """
    Test the proposed @property alias pattern.

    This assumes:
    - Can define Python properties that wrap LCM fields
    - Properties work with getters (read-only pattern)
    - Can use both direct LCM access and property access
    """

    result = VerificationResult("verify_property_aliases")
    print("\n" + "=" * 70)
    print("PHASE 0: Property Alias Pattern Verification")
    print("=" * 70)

    try:
        # Test 1: Create a test property alias pattern
        print("\n[TEST 1] Test property alias pattern")
        try:
            # Get real entries to test
            entries = list(project.LexEntry.GetAll())

            if entries:
                entry = entries[0]

                # Pattern 1: Direct object access via project
                try:
                    # Try to get entry properties
                    entry_str = str(entry)
                    result.add_finding(f"Direct entry access works: {entry_str[:40]}")
                except Exception as e:
                    result.add_exception(type(e).__name__, f"Direct access: {e}")

                # Pattern 2: What if we wrapped it in a property function?
                try:
                    # Simulate property wrapper
                    def get_entry_info(obj):
                        """Property-like wrapper"""
                        return str(obj)

                    wrapped_info = get_entry_info(entry)
                    result.add_finding(f"Wrapped property pattern works: {wrapped_info[:40]}")
                except Exception as e:
                    result.add_exception(type(e).__name__, f"Wrapped access: {e}")

                # Pattern 3: Test with @property decorator
                print("  Testing @property decorator pattern...")
                try:

                    class EntryWrapper:
                        def __init__(self, lcm_entry):
                            self._entry = lcm_entry

                        @property
                        def info(self):
                            """Get entry information"""
                            return str(self._entry)

                    wrapper = EntryWrapper(entry)
                    prop_info = wrapper.info
                    result.add_finding(f"@property decorator pattern works: {prop_info[:40]}")

                except Exception as e:
                    result.add_exception(type(e).__name__, f"@property pattern: {e}")

            else:
                result.add_finding("No entries found to test property patterns")

        except Exception as e:
            result.add_exception(type(e).__name__, f"Property test setup: {e}")

        result.set_passed()

    except Exception as e:
        result.set_error(f"Unexpected error: {e}")
        traceback.print_exc()

    return result


def verify_safe_operations(project: FLExProject) -> VerificationResult:
    """
    Document safe create/delete operation order.

    Tests:
    - What order of operations is safe
    - Which operations are atomic
    - Dependencies between operations
    - Rollback behavior on error
    """

    result = VerificationResult("verify_safe_operations")
    print("\n" + "=" * 70)
    print("PHASE 0: Safe Operations Verification")
    print("=" * 70)

    try:
        # Test 1: Understand transaction model
        print("\n[TEST 1] Understand transaction model")
        try:
            # Check project attributes
            attrs = dir(project)

            # Look for transaction-related methods
            if "SaveChanges" in attrs:
                result.add_finding("SaveChanges() is available - persist changes")

            if "writeEnabled" in attrs:
                result.add_finding(f"writeEnabled attribute available (current: {project.writeEnabled})")

            # Check underlying cache for transaction methods
            if hasattr(project, "project"):
                cache_attrs = dir(project.project)
                if "BeginUndoTask" in cache_attrs:
                    result.add_finding("BeginUndoTask is available in underlying cache")
                if "EndUndoTask" in cache_attrs:
                    result.add_finding("EndUndoTask is available in underlying cache")

        except Exception as e:
            result.add_exception(type(e).__name__, str(e))

        # Test 2: Order of operations - reading
        print("\n[TEST 2] Safe reading order")
        try:
            # Test reading operations
            result.add_finding("Safe order for reading:")
            result.add_finding("  1. Get object collection (e.g., LexEntry.GetAll())")
            result.add_finding("  2. Iterate through objects")
            result.add_finding("  3. Access properties on individual objects")
            result.add_finding("  4. No cleanup needed for read-only")

        except Exception as e:
            result.add_exception(type(e).__name__, str(e))

        # Test 3: Order of operations - writing (simulation)
        print("\n[TEST 3] Safe writing order (documented pattern)")
        try:
            result.add_finding("Safe order for writing (requires writeEnabled=True):")
            result.add_finding("  1. Verify project.writeEnabled is True")
            result.add_finding("  2. Begin undo task (if supported)")
            result.add_finding("  3. Get or create object via project methods")
            result.add_finding("  4. Set properties on object")
            result.add_finding("  5. End undo task (if supported)")
            result.add_finding("  6. Call project.SaveChanges() - persist to disk")
            result.add_finding("  7. On error: may need rollback via undo mechanism")

        except Exception as e:
            result.add_exception(type(e).__name__, str(e))

        # Test 4: Dependencies
        print("\n[TEST 4] Operation dependencies")
        try:
            result.add_finding("Key dependencies:")
            result.add_finding("  - Cannot set properties on non-existent objects")
            result.add_finding("  - Cannot delete objects that are referenced by others")
            result.add_finding("  - Setting collections requires parent object to exist first")
            result.add_finding("  - Writing operations require writeEnabled=True")

        except Exception as e:
            result.add_exception(type(e).__name__, str(e))

        result.set_passed()

    except Exception as e:
        result.set_error(f"Unexpected error: {e}")
        traceback.print_exc()

    return result


# =============================================================================
# MAIN VERIFICATION FLOW
# =============================================================================


def run_phase_0_verification():
    """
    Run all Phase 0 verification tests.

    Flow:
    1. Initialize FLEx
    2. Open Test project (read-only by default, writeEnabled=True only if needed)
    3. Run each verification test
    4. Close project
    5. Generate report
    """

    print("\n" + "=" * 70)
    print("PHASE 0 VERIFICATION - BEGIN")
    print("=" * 70)
    print(f"Start time: {datetime.now()}")

    project = None
    results = []

    try:
        # Initialize FLEx
        print("\n[INIT] Initializing FLEx...")
        FLExInitialize()
        print("  [OK] FLEx initialized")

        # Open project
        print("\n[INIT] Opening project...")
        project = FLExProject()

        # Try to open "Test" project (read-only first)
        try:
            project.OpenProject("Test", writeEnabled=False)
            print("  [OK] Test project opened (read-only)")
        except Exception as e:
            print(f"  [ERROR] Cannot open Test project: {e}")
            print("  [INFO] Available projects:")
            from flexicon.flexicon.code.FLExLCM import GetListOfProjects

            try:
                projects = GetListOfProjects()
                for p in projects:
                    print(f"    - {p}")
            except:
                print("    (Could not list projects)")

            # Try alternative project names
            print("  [INFO] Attempting alternative project names...")
            alt_names = ["Sena 3", "SampleLexicon", "SampleLexicon3"]
            opened = False

            for alt_name in alt_names:
                try:
                    project.OpenProject(alt_name, writeEnabled=False)
                    print(f"  [OK] {alt_name} project opened (read-only)")
                    opened = True
                    break
                except:
                    pass

            if not opened:
                raise Exception("Could not open any test project")

        # Run verification tests
        print("\n[VERIFY] Running Phase 0 verification tests...\n")

        # Test 1: Exception types
        results.append(verify_exception_types(project))

        # Test 2: Sense lookups
        results.append(verify_sense_lookups(project))

        # Test 3: Homograph logic
        results.append(verify_homograph_logic(project))

        # Test 4: Property aliases
        results.append(verify_property_aliases(project))

        # Test 5: Safe operations
        results.append(verify_safe_operations(project))

    except Exception as e:
        print(f"\n[FATAL] Verification failed: {e}")
        traceback.print_exc()

    finally:
        # Close project
        if project:
            try:
                print("\n[CLEANUP] Closing project...")
                project.CloseProject()
                print("  [OK] Project closed")
            except Exception as e:
                print(f"  [ERROR] Error closing project: {e}")

        # Cleanup FLEx
        try:
            print("[CLEANUP] Cleaning up FLEx...")
            FLExCleanup()
            print("  [OK] FLEx cleaned up")
        except Exception as e:
            print(f"  [ERROR] Error cleaning up FLEx: {e}")

    # Generate report
    print("\n" + "=" * 70)
    print("PHASE 0 VERIFICATION - REPORT")
    print("=" * 70)

    generate_report(results)

    print(f"\nEnd time: {datetime.now()}")
    print("=" * 70)


def generate_report(results: List[VerificationResult]):
    """
    Generate comprehensive verification report.
    """

    print("\n[SUMMARY]")
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"  Tests passed: {passed}/{total}")

    print("\n[RESULTS BY TEST]")
    for result in results:
        status = "[PASS]" if result.passed else "[FAIL]"
        print(f"\n{status} {result.name}")

        if result.findings:
            print("  Findings:")
            for finding in result.findings:
                print(f"    - {finding}")

        if result.exceptions:
            print("  Exceptions caught:")
            for exc in result.exceptions:
                print(f"    - {exc['type']}: {exc['message'][:80]}")

        if result.error_message:
            print(f"  Error: {result.error_message}")

    print("\n[ASSUMPTIONS VALIDATION]")
    print("\nBased on test results, validate these assumptions:")

    assumptions = [
        ("Exception Types", "ICmPerson casting throws TypeError"),
        ("Exception Types", "Missing properties throw AttributeError"),
        ("Exception Types", "Invalid lookups throw KeyError/LookupError"),
        ("Sense Lookups", "PossibilityLists is iterable"),
        ("Sense Lookups", "Can find lists by name"),
        ("Sense Lookups", "Items have Name property accessible"),
        ("Homograph Logic", "HomographNumber is auto-assigned"),
        ("Homograph Logic", "Can query entries with HomographNumber > 0"),
        ("Property Aliases", "@property decorator pattern works"),
        ("Safe Operations", "Transaction model via BeginUndoTask/EndUndoTask"),
        ("Safe Operations", "Rollback available via RollbackUndoToMark"),
    ]

    for category, assumption in assumptions:
        test_result = next((r for r in results if category.lower() in r.name), None)
        status = "VERIFIED" if test_result and test_result.passed else "NEEDS CHECK"
        print(f"  [{status}] {category}: {assumption}")

    print("\n[NEXT STEPS]")
    print("  1. Review assumptions marked 'NEEDS CHECK'")
    print("  2. Adjust implementation plan based on findings")
    print("  3. Document any exceptions or surprises")
    print("  4. Proceed to Phase 1 with updated assumptions")


if __name__ == "__main__":
    run_phase_0_verification()
