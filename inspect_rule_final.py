#!/usr/bin/env python3
"""
Final comprehensive inspection with all property details.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flexicon import FLExProject, FLExInitialize, FLExCleanup

# Initialize FLEx
FLExInitialize()

try:
    # Open the Test project
    project = FLExProject()
    project.OpenProject("Test", writeEnabled=False)

    from flexicon.code.Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations

    phonRuleOps = PhonologicalRuleOperations(project)
    rule = phonRuleOps.Find("a neutralization")

    if not rule:
        print("[ERROR] Rule not found!")
    else:
        print(f"================================================================================")
        print(f"PHONOLOGICAL RULE: a neutralization")
        print(f"================================================================================")
        print(f"HVO: {rule.Hvo}")
        print(f"ClassName: {rule.ClassName}")

        # Get the actual string values from the MultiUnicodeAccessor
        try:
            # Name is a MultiUnicodeAccessor - get the actual string
            ws_handle = project.WSHandle("en")  # Try English
            name_val = rule.Name.get(ws_handle) if hasattr(rule.Name, "get") else str(rule.Name)
            print(f"Name: {name_val}")
        except:
            print(f"Name: {rule.Name}")

        try:
            # Description is a MultiStringAccessor
            ws_handle = project.WSHandle("en")
            desc_val = rule.Description.get(ws_handle) if hasattr(rule.Description, "get") else str(rule.Description)
            print(f"Description: {desc_val}")
        except:
            print(f"Description: {rule.Description}")

        print(f"Direction: {rule.Direction} (0=left-to-right)")
        print(f"Disabled: {rule.Disabled}")

        # Try to access RightHandSidesOS instead of just RHS child objects
        print(f"\n=== STRUCTURE ===")
        try:
            rhs_list = list(rule.RightHandSidesOS)
            print(f"RightHandSidesOS: {len(rhs_list)} items")
            for i, rhs in enumerate(rhs_list):
                print(f"  [{i}] {rhs.ClassName} (HVO: {rhs.Hvo})")
        except:
            print(f"RightHandSidesOS: (not accessible or error)")

        # Structure description (input and context)
        print(f"\nStructure Description Objects (StrucDescOS):")
        try:
            struc_desc = list(rule.StrucDescOS)
            print(f"  Count: {len(struc_desc)}")
            for i, sd in enumerate(struc_desc):
                print(f"  [{i}] {sd.ClassName} (HVO: {sd.Hvo})")
                # This is the INPUT SEGMENT
                try:
                    fs = getattr(sd, "FeatureStructureRA", None)
                    if fs:
                        # Get the name of the phoneme/feature
                        try:
                            fs_name = fs.Name
                            if hasattr(fs_name, "get"):
                                fs_name = fs_name.get(project.WSHandle("en"))
                            print(f"      FeatureStructureRA (Input): {fs.ClassName} - {fs_name}")
                        except:
                            print(f"      FeatureStructureRA: {fs.ClassName}")
                except Exception as e:
                    print(f"      (no FeatureStructureRA or error: {e})")
        except Exception as e:
            print(f"  Error: {e}")

        # Now examine the OwnedObjects which includes RHS and input
        print(f"\n=== ALL OWNED OBJECTS ===")
        owned_objs = list(rule.OwnedObjects)
        print(f"Total: {len(owned_objs)}\n")

        for i, obj in enumerate(owned_objs):
            print(f"[{i}] {obj.ClassName} (HVO: {obj.Hvo})")

            if obj.ClassName == "PhSegRuleRHS":
                print(f"    RIGHT-HAND SIDE (output)")
                print(f"    Output segments/classes:")
                try:
                    output_children = list(obj.OwnedObjects)
                    for j, child in enumerate(output_children):
                        print(f"      [{j}] {child.ClassName} (HVO: {child.Hvo})")

                        # Check what this output element references
                        if hasattr(child, "FeatureStructureRA"):
                            try:
                                fs = child.FeatureStructureRA
                                if fs:
                                    try:
                                        fs_name = fs.Name
                                        if hasattr(fs_name, "get"):
                                            fs_name = fs_name.get(project.WSHandle("en"))
                                        print(
                                            f"          Output element (via FeatureStructureRA): {fs.ClassName} - {fs_name}"
                                        )
                                    except:
                                        print(f"          Output element: {fs.ClassName}")
                            except:
                                pass

                        if hasattr(child, "NatlClassRA"):
                            try:
                                nc = child.NatlClassRA
                                if nc:
                                    try:
                                        nc_name = nc.Name
                                        if hasattr(nc_name, "get"):
                                            nc_name = nc_name.get(project.WSHandle("en"))
                                        print(f"          Natural class (via NatlClassRA): {nc.ClassName} - {nc_name}")
                                    except:
                                        print(f"          Natural class: {nc.ClassName}")
                            except:
                                pass

                except Exception as e:
                    print(f"    Error: {e}")

            elif obj.ClassName == "PhSimpleContextSeg":
                print(f"    INPUT SEGMENT")
                try:
                    fs = obj.FeatureStructureRA
                    if fs:
                        try:
                            fs_name = fs.Name
                            if hasattr(fs_name, "get"):
                                fs_name = fs_name.get(project.WSHandle("en"))
                            print(f"      Input segment (FeatureStructureRA): {fs.ClassName} - {fs_name}")
                        except:
                            print(f"      Input segment: {fs.ClassName}")
                except:
                    print(f"      (no FeatureStructureRA)")

            print()

        # Summary view
        print(f"\n=== RULE FORMULA VIEW ===")
        print(f"a neutralization rule structure:")
        print(f"  Input:  <something> (from StrucDescOS)")
        print(f"  Output: <something> (from RightHandSidesOS children)")

finally:
    project.CloseProject()
    FLExCleanup()
