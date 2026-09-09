#!/usr/bin/env python3
"""
Deprecation Pointer: GramCatOperations -> POSOperations

`project.GramCat` is DEPRECATED. It no longer has a CRUD surface of its own:
it returns a deprecated `GramCatOperations`, a subclass of `POSOperations`
that addresses the very same list (`LangProject.PartsOfSpeechOA`). The full
CRUD walkthrough therefore lives in `examples/grammar_pos_operations_demo.py`,
and this script does not repeat it.

Note that `project.GramCat` is NOT `project.POS`:
`project.GramCat is project.POS` is False. It is a distinct, lazily created
and then cached instance. That is deliberate -- it is what keeps the
explanatory `GramCat.Create()` override reachable on the path a legacy caller
actually takes.

What this script does instead:
  1. Explains which FLEx concept each similarly-named API actually addresses.
  2. Shows the DeprecationWarning fired by the first project.GramCat access.
  3. Shows that GramCat is a distinct object over the same POS list.
  4. Shows that project.GramCat.Create() raises FP_ParameterError.

Background (issue #276): GramCatOperations used to walk
`LangProject.MsFeatureSystemOA.TypesOC`, a collection of `IFsFeatStrucType`.
That is a structural template for feature structures, never a grammatical
category. At list level a grammatical category IS a Part of Speech
(`IPartOfSpeech` in `LangProject.PartsOfSpeechOA`), a list POSOperations
already owns completely.

This demo is READ-ONLY. It opens the project without write access and makes
no changes. Removal of the GramCat spelling is scheduled for v5.0.0.

Author: FlexTools Development Team
Date: 2026-09-09
"""

import warnings

from flexicon import (
    FLExProject,
    FLExInitialize,
    FLExCleanup,
    FP_ParameterError,
    GramCatOperations,
    POSOperations,
)


def print_naming_map():
    """Print the three-way disambiguation the name 'GramCat' needs."""
    print("\n" + "=" * 70)
    print("STEP 1: WHICH API DID YOU ACTUALLY WANT?")
    print("=" * 70)
    print(
        """
Three FLEx concepts wear confusingly similar names. They are different LCM
classes, and only the first is a category.

  1. The inventory of categories        (FLEx: Grammar > Categories)
     LCM: IPartOfSpeech in LangProject.PartsOfSpeechOA
     API: project.POS          <- the list the deprecated project.GramCat
                                  also addresses

  2. A sense's "Grammatical Info."      (FLEx: Lexicon sense field)
     LCM: the MSA, ILexSense.MorphoSyntaxAnalysisRA -- a composite that
          references a POS and owns a feature structure
     API: project.Senses.GetGrammaticalInfo(sense)
          project.Senses.GetPartOfSpeechObject(sense)  (just the category)
          project.MSA.*                                (to build one)

  3. A feature-structure template       (FLEx: Grammar > Features, type list)
     LCM: IFsFeatStrucType in LangProject.MsFeatureSystemOA.TypesOC
     API: project.InflectionFeatures.TypeFind(name)
          project.InflectionFeatures.TypeCreate(name, abbreviation)

The old GramCatOperations served (3) while its name promised (1).
"""
    )


def demo_deprecation_warning(project):
    """Show the DeprecationWarning fired by the FIRST project.GramCat access.

    Must run before any other step touches project.GramCat: the property
    builds GramCatOperations once and caches it, so the warning fires exactly
    once per project.
    """
    print("=" * 70)
    print("STEP 2: THE FIRST project.GramCat ACCESS WARNS")
    print("=" * 70)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        first = project.GramCat

    print(f"\n  project.GramCat -> {type(first).__name__}")

    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    if deprecations:
        print("\n  [WARN] DeprecationWarning:")
        for line in str(deprecations[0].message).split(". "):
            if line.strip():
                print(f"    {line.strip().rstrip('.')}.")
    else:
        print("\n  [FAIL] Expected a DeprecationWarning on first access, got none.")

    # The property caches, so the warning does not repeat.
    with warnings.catch_warnings(record=True) as caught_again:
        warnings.simplefilter("always")
        second = project.GramCat

    repeated = [w for w in caught_again if issubclass(w.category, DeprecationWarning)]
    print("\n  Second access (the instance is cached):")
    print(f"    project.GramCat is project.GramCat  ->  {second is first}")
    print(f"    DeprecationWarnings on re-access    ->  {len(repeated)}")
    if repeated or second is not first:
        print("    [FAIL] Expected one silent, cached re-access.")
    else:
        print("    [OK] Warned once, on first access only.")

    print("\n  [NOTE] To surface these in your own scripts:")
    print("           python -W error::DeprecationWarning your_script.py")
    print("  [NOTE] Constructing GramCatOperations(project) by hand warns too.")


def demo_same_list_distinct_object(project):
    """Show GramCat is a distinct object addressing the same POS list."""
    print("\n" + "=" * 70)
    print("STEP 3: A DISTINCT OBJECT OVER THE SAME POS LIST")
    print("=" * 70)

    gramcat = project.GramCat
    pos = project.POS

    print(f"\n  type(project.GramCat)           ->  {type(gramcat).__name__}")
    print(f"  type(project.POS)               ->  {type(pos).__name__}")
    print(f"  project.GramCat is project.POS  ->  {gramcat is pos}")
    print(f"  isinstance(gramcat, GramCatOperations) -> "
          f"{isinstance(gramcat, GramCatOperations)}")
    print(f"  isinstance(gramcat, POSOperations)     -> "
          f"{isinstance(gramcat, POSOperations)}")

    if gramcat is pos:
        print("\n  [FAIL] Expected two distinct objects. The raising")
        print("         GramCat.Create() override is unreachable if the")
        print("         property just returns project.POS.")
        return

    print("\n  [OK] Not the same object -- a deprecated POSOperations subclass.")
    print("       Keeping it distinct is what makes STEP 4 reachable.")

    gramcat_names = [gramcat.GetName(p) for p in gramcat.GetAll()]
    pos_names = [pos.GetName(p) for p in pos.GetAll()]

    print("\n  Both spellings read LangProject.PartsOfSpeechOA:")
    print(f"    len(project.GramCat.GetAll())  ->  {len(gramcat_names)}")
    print(f"    len(project.POS.GetAll())      ->  {len(pos_names)}")
    if gramcat_names == pos_names:
        print("    [OK] Same categories, same order.")
    else:
        print("    [FAIL] The two spellings disagree about the list contents.")

    print("\n  Reading the category inventory (first 5, via the POS spelling):")
    shown = 0
    for p in pos.GetAll():
        print(f"    - {pos.GetName(p)} ({pos.GetAbbreviation(p)})")
        shown += 1
        if shown >= 5:
            break
    if shown == 0:
        print("    (no categories in this project)")


def demo_create_raises(project):
    """Show that project.GramCat.Create() raises and writes nothing."""
    print("\n" + "=" * 70)
    print("STEP 4: project.GramCat.Create() RAISES -- IT NEVER MADE A CATEGORY")
    print("=" * 70)

    print("\n  Calling project.GramCat.Create('crud_test_gramcat')...")
    try:
        project.GramCat.Create("crud_test_gramcat")
    except FP_ParameterError as e:
        print("  [OK] FP_ParameterError raised before any write:\n")
        for line in str(e).replace(". ", ".\n").split("\n"):
            if line.strip():
                print(f"    {line.strip()}")
    else:
        print("  [FAIL] Expected FP_ParameterError and the call succeeded.")
        return

    print(
        """
  [NOTE] Only FP_ParameterError is caught above, deliberately. Were the
         GramCat spelling ever collapsed back onto project.POS, this same
         call would reach POSOperations.Create(name, abbreviation) and raise
         a bare TypeError about a missing 'abbreviation' -- which names
         neither the replacement nor the reason. That regression escapes
         this demo loudly instead of being swallowed.

  Replacements (all write operations -- this demo is read-only, so they are
  shown but not executed):

    # Top-level category:
    verb = project.POS.Create("Verb", "v")

    # Subcategory:
    sub = project.POS.AddSubcategory(verb, "Transitive Verb", "vt")
    assert project.POS.GetParent(sub) is not None

    # A feature-structure type, if that is what you actually wanted:
    ftype = project.InflectionFeatures.TypeCreate("Common agreement", "tCommonAgr")

  [WARN] If this project was ever written to by the old GramCat.Create, it
         has stray IFsFeatStrucType entries under Grammar > Features carrying
         whatever names were passed. Clean those up by hand in FLEx. No
         automatic cleanup is offered and none should be attempted: a stray is
         indistinguishable from a type legitimately made by TypeCreate, and one
         may since have been referenced via TypeRA.
"""
    )


def demo_gramcat_deprecation():
    """Run the read-only deprecation walkthrough."""
    print("=" * 70)
    print("GRAMCAT OPERATIONS - DEPRECATED, USE POS")
    print("=" * 70)

    print_naming_map()

    FLExInitialize()

    project = FLExProject()
    try:
        project.OpenProject("Sena 3", writeEnabled=False)
    except Exception as e:
        print(f"Cannot run demo - FLEx project not available: {e}")
        FLExCleanup()
        return

    try:
        # Order matters: the warning fires on the FIRST GramCat access.
        demo_deprecation_warning(project)
        demo_same_list_distinct_object(project)
        demo_create_raises(project)

        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(
            """
  project.GramCat            -> deprecated GramCatOperations over the POS
                                list; NOT project.POS (the `is` test is False)
  First access               -> DeprecationWarning, once per project (cached)
  GramCat.GetAll/GetName/... -> POS data (IPartOfSpeech), not feature types
  GramCat.Create(...)        -> raises FP_ParameterError, writes nothing
  Removal                    -> scheduled for v5.0.0

  For the full category CRUD walkthrough, run:
      examples/grammar_pos_operations_demo.py

  For migration steps, see docs/MIGRATION_GUIDE.md
      "Breaking Change: project.GramCat now addresses the Part of Speech list"
"""
        )

    except Exception as e:
        print(f"\n\nERROR during demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("Closing project...")
        project.CloseProject()
        FLExCleanup()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    print(
        """
GramCat Operations - Deprecation Pointer
=====================================================

project.GramCat is DEPRECATED (issue #276). It returns a deprecated
GramCatOperations that addresses the Part of Speech list -- the same list as
project.POS, though not the same object. This script explains the rename and
shows the one call that now raises. It does NOT demonstrate CRUD -- see
examples/grammar_pos_operations_demo.py for that.

Shown here:
===========

1. Which API addresses which FLEx concept (categories vs MSA vs feature types)
2. The DeprecationWarning on the first project.GramCat access
3. GramCat as a distinct object over the same POS list
4. project.GramCat.Create() raising FP_ParameterError

Requirements:
  - A FLEx project (opened READ-ONLY)
  - Python.NET runtime

[NOTE] This demo makes NO changes to the database.
    """
    )

    response = input("\nRun deprecation demo? (y/N): ")
    if response.lower() == "y":
        demo_gramcat_deprecation()
    else:
        print("\nDemo skipped.")
