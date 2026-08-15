#!/usr/bin/env python3
"""
Check what's available in the installed FieldWorks LCM API.

This script initializes FieldWorks and checks which interfaces
and classes are available in the LCModel assembly.
"""

import sys
import os
from pathlib import Path

# Initialize flexlibs to set up paths correctly
script_dir = Path(__file__).parent
flexlibs_root = script_dir.parent
os.chdir(str(flexlibs_root))
sys.path.insert(0, str(flexlibs_root))


def check_imports(test_imports, description):
    """
    Check if specified imports exist in LCModel.

    Args:
        test_imports: List of interface/class names to check
        description: Description of what's being tested

    Returns:
        None (prints results)
    """
    from SIL import LCModel

    print(f"\n{description}:")
    for name in test_imports:
        if hasattr(LCModel, name):
            print(f"   ✓ {name:30s} EXISTS")
        else:
            print(f"   ✗ {name:30s} MISSING")
            # Try to find similar names
            similar = [x for x in dir(LCModel) if name[1:5] in x or name[-10:] in x][:5]
            if similar:
                print(f"      Similar names: {', '.join(similar)}")


def show_interfaces(prefix, description):
    """
    Show all interfaces matching a prefix.

    Args:
        prefix: Prefix to filter interfaces (e.g., 'IMo')
        description: Description of the interface category

    Returns:
        None (prints results)
    """
    from SIL import LCModel

    print(f"\n{description}:")
    interfaces = [x for x in dir(LCModel) if x.startswith(prefix)]
    for i, name in enumerate(interfaces[:20], 1):
        print(f"   {i:3d}. {name}")
    if len(interfaces) > 20:
        print(f"   ... and {len(interfaces) - 20} more")


def main():
    """Main function to check LCM API availability."""
    print("Initializing FieldWorks...")
    print("=" * 70)

    # Import the initialization code
    from flexicon.code import FLExGlobals

    FLExGlobals.InitialiseFWGlobals()

    print(f"FieldWorks Code Dir: {FLExGlobals.FWCodeDir}")
    print(f"FieldWorks Version: {FLExGlobals.FWShortVersion}")
    print()

    # Now check what's in LCModel
    import clr

    clr.AddReference("SIL.LCModel")

    print("Checking for problematic imports...")
    print("=" * 70)

    # Test imports from MorphRuleOperations.py
    morph_rule_imports = [
        "IMoMorphRule",
        "IMoAffixProcessFactory",
        "IMoStratumFactory",
    ]
    check_imports(morph_rule_imports, "1. MorphRuleOperations.py imports")

    # Test imports from InflectionFeatureOperations.py
    inflection_imports = [
        "IMoInflClass",
        "IMoInflClassFactory",
        "IFsFeatStruc",
        "IFsFeatStrucFactory",
        "IFsFeatureDefn",  # This is wrong
        "IFsFeatDefn",  # This might be correct
        "IFsComplexFeature",
        "IFsComplexFeatureFactory",
    ]
    check_imports(inflection_imports, "2. InflectionFeatureOperations.py imports")

    # Show all IMo* interfaces
    show_interfaces("IMo", "3. All IMo* interfaces available")

    # Show all IFs* interfaces
    show_interfaces("IFs", "4. All IFs* interfaces available")


if __name__ == "__main__":
    main()
