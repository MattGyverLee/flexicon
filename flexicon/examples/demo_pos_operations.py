#!/usr/bin/env python3
#
#   demo_pos_operations.py
#
#   Demonstration of POSOperations module usage
#

import sys

sys.path.insert(0, "../code")

from FLExProject import FLExProject
from POSOperations import POSOperations


def main():
    """
    Demonstrate the usage of POSOperations class.
    """

    # Initialize and open project
    project = FLExProject()

    try:
        # Open project (replace with your project name)
        # For write operations, use writeEnabled=True
        project.OpenProject("test-project", writeEnabled=False)

        print(f"Project: {project.ProjectName()}\n")

        # Create POSOperations instance
        posOps = POSOperations(project)

        # --- Example 1: Get all parts of speech ---
        print("=== All Parts of Speech ===")
        for pos in posOps.GetAll():
            name = posOps.GetName(pos)
            abbr = posOps.GetAbbreviation(pos)
            print(f"  {name} ({abbr})")

            # Show subcategories if any
            subcats = posOps.GetSubcategories(pos)
            if subcats:
                for subcat in subcats:
                    sub_name = posOps.GetName(subcat)
                    sub_abbr = posOps.GetAbbreviation(subcat)
                    print(f"    → {sub_name} ({sub_abbr})")
        print()

        # --- Example 2: Find a specific POS ---
        print("=== Finding a POS ===")
        noun = posOps.Find("Noun")
        if noun:
            print(f"Found 'Noun': {posOps.GetAbbreviation(noun)}")
        else:
            print("'Noun' not found")
        print()

        # --- Example 3: Check if POS exists ---
        print("=== Checking Existence ===")
        print(f"'Verb' exists: {posOps.Exists('Verb')}")
        print(f"'Interjection' exists: {posOps.Exists('Interjection')}")
        print()

        # --- Example 4: Create, update, and delete (requires writeEnabled=True) ---
        # Uncomment the following if you open with writeEnabled=True
        """
        print("=== Creating a new POS ===")
        if not posOps.Exists("Particle"):
            particle = posOps.Create("Particle", "Prt", "GOLD:Particle")
            print(f"Created: {posOps.GetName(particle)} ({posOps.GetAbbreviation(particle)})")

        print("\\n=== Updating a POS ===")
        particle = posOps.Find("Particle")
        if particle:
            posOps.SetAbbreviation(particle, "Part")
            print(f"Updated abbreviation to: {posOps.GetAbbreviation(particle)}")

        print("\\n=== Deleting a POS ===")
        if posOps.Exists("Obsolete"):
            obsolete = posOps.Find("Obsolete")
            posOps.Delete(obsolete)
            print("Deleted 'Obsolete' POS")
        """

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    finally:
        # Always close the project
        project.CloseProject()

    return 0


if __name__ == "__main__":
    sys.exit(main())
