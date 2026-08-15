#!/usr/bin/env python3
"""
Generate demonstration files for Operations classes.

This script creates demonstration files showing how to use various
Operations classes in flexicon. It analyzes the methods available
in each Operations class and generates example code.
"""

import os
import sys
from pathlib import Path

# Add flexlibs to path (use relative path from script location)
script_dir = Path(__file__).parent
flexlibs_root = script_dir.parent
sys.path.insert(0, str(flexlibs_root))

from flexicon.code.Grammar.NaturalClassOperations import NaturalClassOperations
from flexicon.code.Grammar.EnvironmentOperations import EnvironmentOperations
from flexicon.code.Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations
from flexicon.code.Grammar.InflectionFeatureOperations import InflectionFeatureOperations
from flexicon.code.Grammar.GramCatOperations import GramCatOperations
from flexicon.code.Lexicon.LexSenseOperations import LexSenseOperations
from flexicon.code.Lexicon.ExampleOperations import ExampleOperations
from flexicon.code.Lexicon.PronunciationOperations import PronunciationOperations
from flexicon.code.Lexicon.VariantOperations import VariantOperations
from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations
from flexicon.code.Lexicon.EtymologyOperations import EtymologyOperations
from flexicon.code.Lexicon.LexReferenceOperations import LexReferenceOperations


def get_public_methods(cls):
    """
    Get all public methods from a class.

    Args:
        cls: The class to inspect

    Returns:
        Sorted list of public method names
    """
    methods = []
    for name in dir(cls):
        if not name.startswith("_") and callable(getattr(cls, name, None)):
            methods.append(name)
    return sorted(methods)


def generate_demo(ops_class, filename, property_name, display_name, domain):
    """
    Generate a demonstration file for an Operations class.

    Args:
        ops_class: The Operations class to demonstrate
        filename: Output filename for the demo
        property_name: Property name on FLExProject (e.g., 'Phonemes')
        display_name: Human-readable name for the operations
        domain: Domain identifier for function naming

    Returns:
        None (writes file to examples directory)
    """
    methods = get_public_methods(ops_class)

    # Categorize methods
    create_methods = [m for m in methods if m.startswith("Create") or m.startswith("Add")]
    read_methods = [m for m in methods if m.startswith("Get") or m == "Find" or m == "Exists"]
    update_methods = [m for m in methods if m.startswith("Set") or m.startswith("Update")]
    delete_methods = [m for m in methods if m.startswith("Delete") or m.startswith("Remove")]

    content = f'''#!/usr/bin/env python3
"""
Demonstration of {ops_class.__name__} for flexlibs

This script demonstrates the comprehensive {ops_class.__name__} class
for managing {display_name.lower()} in a FLEx project.
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup

def demo_{domain.lower()}_operations():
    """Demonstrate {ops_class.__name__} functionality."""

    # Initialize FieldWorks
    FLExInitialize()

    # Open project
    project = FLExProject()
    try:
        project.OpenProject("Kenyang-M", writeEnabled=True)
    except Exception as e:
        print(f"Cannot run demo - FLEx project not available: {{e}}")
        FLExCleanup()
        return

    print("=" * 60)
    print("{ops_class.__name__} Demonstration")
    print("=" * 60)

    # --- Test all methods ---
    print("\\n1. Testing GetAll (if available):")
    try:
        if hasattr(project.{property_name}, 'GetAll'):
            count = 0
            for item in project.{property_name}.GetAll():
                count += 1
                if count >= 5:
                    print(f"   ... (showing first 5 of {{count}}+ items)")
                    break
            print(f"   Total items: {{count}}")
        else:
            print("   GetAll method not available")
    except Exception as e:
        print(f"   ERROR: {{e}}")

    print("\\n2. Testing Create (if available):")
    try:
        if hasattr(project.{property_name}, 'Create'):
            print("   Create method available (not tested to preserve data)")
        else:
            print("   Create method not available")
    except Exception as e:
        print(f"   ERROR: {{e}}")

    print("\\n3. Testing Find/Exists (if available):")
    try:
        if hasattr(project.{property_name}, 'Find'):
            print("   Find method available")
        if hasattr(project.{property_name}, 'Exists'):
            print("   Exists method available")
    except Exception as e:
        print(f"   ERROR: {{e}}")

    print("\\n4. Available methods in {ops_class.__name__}:")
    methods = {methods}
    for method in methods[:10]:  # Show first 10
        print(f"   - {{method}}()")
    if len(methods) > 10:
        print(f"   ... and {{len(methods) - 10}} more")

    print("\\n" + "=" * 60)
    print("Demonstration complete!")
    print("=" * 60)

    project.CloseProject()
    FLExCleanup()

if __name__ == "__main__":
    print("""
{ops_class.__name__} Demo
{"=" * len(ops_class.__name__)}======

This demonstrates the {ops_class.__name__} class.

Available methods ({len(methods)} total):

Create operations ({len(create_methods)}):
{chr(10).join('  - ' + m + '()' for m in create_methods[:5])}
{"  ..." if len(create_methods) > 5 else ""}

Read operations ({len(read_methods)}):
{chr(10).join('  - ' + m + '()' for m in read_methods[:5])}
{"  ..." if len(read_methods) > 5 else ""}

Update operations ({len(update_methods)}):
{chr(10).join('  - ' + m + '()' for m in update_methods[:5])}
{"  ..." if len(update_methods) > 5 else ""}

Delete operations ({len(delete_methods)}):
{chr(10).join('  - ' + m + '()' for m in delete_methods[:5])}
{"  ..." if len(delete_methods) > 5 else ""}

Note: Actual execution requires a FLEx project and Python.NET runtime.
    """)
    demo_{domain.lower()}_operations()
'''

    # Use relative path from script location
    examples_dir = flexlibs_root / "examples"
    examples_dir.mkdir(exist_ok=True)
    output_path = examples_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {filename}")


def main():
    """Generate all demonstration files."""
    # Define demonstrations to generate
    demos = [
        (
            NaturalClassOperations,
            "grammar_naturalclass_operations_demo.py",
            "NaturalClasses",
            "Natural Classes",
            "naturalclass",
        ),
        (
            EnvironmentOperations,
            "grammar_environment_operations_demo.py",
            "Environments",
            "Environments",
            "environment",
        ),
        (
            PhonologicalRuleOperations,
            "grammar_phonrule_operations_demo.py",
            "PhonRules",
            "Phonological Rules",
            "phonrule",
        ),
        (
            InflectionFeatureOperations,
            "grammar_inflection_operations_demo.py",
            "InflectionFeatures",
            "Inflection Features",
            "inflection",
        ),
        (GramCatOperations, "grammar_gramcat_operations_demo.py", "GramCat", "Grammatical Categories", "gramcat"),
        (LexSenseOperations, "lexicon_sense_operations_demo.py", "Senses", "Lexical Senses", "sense"),
        (ExampleOperations, "lexicon_example_operations_demo.py", "Examples", "Example Sentences", "example"),
        (
            PronunciationOperations,
            "lexicon_pronunciation_operations_demo.py",
            "Pronunciations",
            "Pronunciations",
            "pronunciation",
        ),
        (VariantOperations, "lexicon_variant_operations_demo.py", "Variants", "Variant Forms", "variant"),
        (AllomorphOperations, "lexicon_allomorph_operations_demo.py", "Allomorphs", "Allomorphs", "allomorph"),
        (EtymologyOperations, "lexicon_etymology_operations_demo.py", "Etymology", "Etymologies", "etymology"),
        (
            LexReferenceOperations,
            "lexicon_lexreference_operations_demo.py",
            "LexReferences",
            "Lexical References",
            "lexreference",
        ),
    ]

    print("Generating demonstration files...")
    print(f"Total demos to generate: {len(demos)}\n")

    for ops_class, filename, prop, display, domain in demos:
        generate_demo(ops_class, filename, prop, display, domain)

    print("\nAll demonstrations generated!")


if __name__ == "__main__":
    main()
