# -*- coding: utf-8 -*-

#   demo_writing_systems.py
#
#   Demonstrates writing system management operations in FLEx projects.
#
#   Platform: Python .NET
#
#   Copyright 2025
#

import sys

from flexlibs2 import FLExInitialize, FLExCleanup
from flexlibs2 import FLExProject, FP_ProjectError

# ============ Configurables ===============

# Project to use
TEST_PROJECT = r"__flexlibs_testing"


def demo_writing_system_operations(project):
    """
    Demonstrate various writing system operations.
    """

    print("\n" + "=" * 70)
    print("WRITING SYSTEM OPERATIONS DEMO")
    print("=" * 70)

    # --- Getting Writing Systems ---
    print("\n1. Getting All Writing Systems")
    print("-" * 50)

    for ws in project.WritingSystems.GetAll():
        name = project.WritingSystems.GetDisplayName(ws)
        tag = project.WritingSystems.GetLanguageTag(ws)
        font = project.WritingSystems.GetFontName(ws)
        size = project.WritingSystems.GetFontSize(ws)
        rtl = project.WritingSystems.GetRightToLeft(ws)

        print(f"  {name} ({tag})")
        print(f"    Font: {font}, Size: {size}pt")
        print(f"    RTL: {rtl}")

    # --- Vernacular Writing Systems ---
    print("\n2. Vernacular Writing Systems")
    print("-" * 50)

    for ws in project.WritingSystems.GetVernacular():
        name = project.WritingSystems.GetDisplayName(ws)
        tag = project.WritingSystems.GetLanguageTag(ws)
        print(f"  Vernacular: {name} ({tag})")

    # --- Analysis Writing Systems ---
    print("\n3. Analysis Writing Systems")
    print("-" * 50)

    for ws in project.WritingSystems.GetAnalysis():
        name = project.WritingSystems.GetDisplayName(ws)
        tag = project.WritingSystems.GetLanguageTag(ws)
        print(f"  Analysis: {name} ({tag})")

    # --- Default Writing Systems ---
    print("\n4. Default Writing Systems")
    print("-" * 50)

    default_vern = project.WritingSystems.GetDefaultVernacular()
    vern_name = project.WritingSystems.GetDisplayName(default_vern)
    vern_tag = project.WritingSystems.GetLanguageTag(default_vern)
    print(f"  Default Vernacular: {vern_name} ({vern_tag})")

    default_anal = project.WritingSystems.GetDefaultAnalysis()
    anal_name = project.WritingSystems.GetDisplayName(default_anal)
    anal_tag = project.WritingSystems.GetLanguageTag(default_anal)
    print(f"  Default Analysis: {anal_name} ({anal_tag})")

    # --- Checking Existence ---
    print("\n5. Checking Writing System Existence")
    print("-" * 50)

    test_tags = ["en", "fr", "es", "ar", "qaa-x-kal", "qaa-x-test"]
    for tag in test_tags:
        exists = project.WritingSystems.Exists(tag)
        print(f"  {tag}: {'EXISTS' if exists else 'NOT FOUND'}")

    # --- Font Configuration (Read-Only Demo) ---
    print("\n6. Font Configuration (Current Settings)")
    print("-" * 50)

    for ws in list(project.WritingSystems.GetVernacular())[:2]:
        name = project.WritingSystems.GetDisplayName(ws)
        font_name = project.WritingSystems.GetFontName(ws)
        font_size = project.WritingSystems.GetFontSize(ws)
        print(f"  {name}:")
        print(f"    Current Font: {font_name}")
        print(f"    Current Size: {font_size}pt")

    # --- RTL Configuration ---
    print("\n7. Right-to-Left Settings")
    print("-" * 50)

    for ws in project.WritingSystems.GetAll():
        name = project.WritingSystems.GetDisplayName(ws)
        tag = project.WritingSystems.GetLanguageTag(ws)
        rtl = project.WritingSystems.GetRightToLeft(ws)
        direction = "Right-to-Left" if rtl else "Left-to-Right"
        print(f"  {name} ({tag}): {direction}")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70 + "\n")


def demo_writing_system_modifications(project):
    """
    Demonstrate writing system modifications (requires write enabled).
    This is commented out by default to avoid modifying the test project.
    """

    print("\n" + "=" * 70)
    print("WRITING SYSTEM MODIFICATIONS (WRITE MODE)")
    print("=" * 70)
    print("\nNOTE: These operations require writeEnabled=True")
    print("Uncomment in main() to test modifications.\n")

    # Example: Create a new writing system
    # ws = project.WritingSystems.Create("qaa-x-example", "Example Language")
    # project.WritingSystems.SetFontName(ws, "Charis SIL")
    # project.WritingSystems.SetFontSize(ws, 14)
    # project.WritingSystems.SetRightToLeft(ws, False)

    # Example: Modify existing writing system
    # if project.WritingSystems.Exists("en"):
    #     project.WritingSystems.SetFontName("en", "Calibri")
    #     project.WritingSystems.SetFontSize("en", 12)

    # Example: Set default vernacular
    # vern_wss = list(project.WritingSystems.GetVernacular())
    # if len(vern_wss) > 0:
    #     project.WritingSystems.SetDefaultVernacular(vern_wss[0])

    # Example: Delete a writing system (use with caution!)
    # if project.WritingSystems.Exists("qaa-x-test"):
    #     project.WritingSystems.Delete("qaa-x-test")

    print("  (Modification examples are commented out)")
    print("\n" + "=" * 70 + "\n")


# -------------------------------------------------------------------
if __name__ == "__main__":

    FLExInitialize()

    project = FLExProject()

    try:
        # Open project in read-only mode for demo
        project.OpenProject(projectName=TEST_PROJECT, writeEnabled=False)
    except FP_ProjectError as e:
        print("OpenProject failed!")
        print(e.message)
        FLExCleanup()
        sys.exit(1)

    # Run the demo
    demo_writing_system_operations(project)

    # Show modification examples (commented out)
    demo_writing_system_modifications(project)

    # To test modifications, change to:
    # project.OpenProject(projectName=TEST_PROJECT, writeEnabled=True)
    # And uncomment the operations in demo_writing_system_modifications()

    # Clean-up
    project.CloseProject()

    FLExCleanup()

    print("Demo completed successfully!")
