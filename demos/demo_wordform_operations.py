#!/usr/bin/env python3
"""
Demo: Wordform Inventory Operations (Work Stream 3)

This script demonstrates how to work with the Wordform Inventory in a FieldWorks
project using the flexlibs library. This is the MOST ACTIVE area of FLEx with 727+
commits in 2024!

The Wordform Inventory bridges texts and lexicon, storing unique word forms from
interlinear texts with their morphological analyses, enabling:
    - Parser training and improvement
    - Interlinear text analysis
    - Concordance generation
    - Word frequency analysis

Usage:
    python demo_wordform_operations.py [project_name]

Features demonstrated:
    - Finding and creating wordforms (FindOrCreate pattern)
    - Creating morphological analyses
    - Adding glosses to analyses
    - Creating morpheme bundles (morphological breakdown)
    - Linking to lexicon (sense connections)
    - Human approval workflow
    - Inventory statistics

Author: flexlibs Work Stream 3
Date: 2025
"""

import sys
from flexicon import FLExProject


def demo_wordform_basics(project):
    """Demonstrate basic wordform operations."""
    print("\n=== Wordform Basics ===\n")

    # Get wordform statistics
    print("1. Wordform Inventory Statistics:")
    wordform_count = sum(1 for _ in project.Wordforms.GetAll())
    print(f"   Total wordforms in inventory: {wordform_count}")

    # Show sample wordforms
    print("\n2. Sample wordforms:")
    for i, wf in enumerate(list(project.Wordforms.GetAll())[:10], 1):
        form = project.Wordforms.GetForm(wf)
        analyses_count = len(project.Wordforms.GetAnalyses(wf))
        occurrences = project.Wordforms.GetOccurrences(wf)
        print(f"   {i}. {form}: {analyses_count} analyses, {occurrences} occurrences")

    # Demonstrate FindOrCreate pattern (most common)
    print("\n3. FindOrCreate pattern (most common for inventory):")
    test_form = "demo-wordform"
    wf = project.Wordforms.FindOrCreate(test_form)
    print(f"   Got wordform: {project.Wordforms.GetForm(wf)}")
    print(f"   (This is the recommended way to work with wordforms)")

    return wf


def demo_wordform_analyses(project, wordform):
    """Demonstrate wordform analysis operations."""
    print("\n=== Wordform Analysis Operations ===\n")

    # Show existing analyses
    print("1. Existing analyses:")
    analyses = project.Wordforms.GetAnalyses(wordform)
    if analyses:
        for i, analysis in enumerate(analyses, 1):
            approved = project.WfiAnalyses.IsHumanApproved(analysis)
            category = project.WfiAnalyses.GetCategory(analysis)
            cat_name = category.Name.BestAnalysisAlternative.Text if category else "none"
            status = "APPROVED" if approved else "parser guess"
            print(f"   {i}. [{status}] Category: {cat_name}")
    else:
        print("   No analyses yet")

    # Create a new analysis
    print("\n2. Create new analysis:")
    analysis = project.WfiAnalyses.Create(wordform)
    print(f"   Created analysis (HVO: {analysis.Hvo})")

    # Set category (part of speech)
    print("\n3. Set analysis category:")
    # Try to find a verb POS
    for pos in project.POS.GetAll():
        pos_name = pos.Name.BestAnalysisAlternative.Text
        if pos_name and "verb" in pos_name.lower():
            project.WfiAnalyses.SetCategory(analysis, pos)
            print(f"   Set category to: {pos_name}")
            break
    else:
        print("   No verb category found, skipping...")

    return analysis


def demo_wordform_glosses(project, analysis):
    """Demonstrate wordform gloss operations."""
    print("\n=== Wordform Gloss Operations ===\n")

    # Show existing glosses
    print("1. Existing glosses:")
    glosses = project.WfiAnalyses.GetGlosses(analysis)
    if glosses:
        for i, gloss in enumerate(glosses, 1):
            text = project.WfiGlosses.GetForm(gloss)
            approved = project.WfiGlosses.IsHumanApproved(gloss)
            status = "APPROVED" if approved else "parser guess"
            print(f"   {i}. [{status}] {text}")
    else:
        print("   No glosses yet")

    # Create a new gloss
    print("\n2. Create new gloss:")
    en_ws = project.WSHandle("en")
    gloss = project.WfiGlosses.Create(analysis, "example", en_ws)
    print(f"   Created gloss: {project.WfiGlosses.GetForm(gloss)}")

    return gloss


def demo_morpheme_bundles(project, analysis):
    """Demonstrate morpheme bundle operations."""
    print("\n=== Morpheme Bundle Operations ===\n")

    # Show existing bundles
    print("1. Existing morpheme bundles:")
    bundles = project.WfiAnalyses.GetMorphBundles(analysis)
    if bundles:
        for i, bundle in enumerate(bundles, 1):
            form = project.WfiMorphBundles.GetForm(bundle)
            sense = project.WfiMorphBundles.GetSense(bundle)
            if sense:
                gloss = project.Senses.GetGloss(sense)
                entry = sense.Entry
                headword = project.LexEntry.GetHeadword(entry)
                print(f"   {i}. {form} = {headword} ({gloss})")
            else:
                print(f"   {i}. {form} (not linked to lexicon)")
    else:
        print("   No morpheme bundles yet")

    # Create morpheme bundles (morphological breakdown)
    print("\n2. Create morpheme bundles:")
    # Create two bundles: stem + suffix
    stem = project.WfiMorphBundles.Create(analysis, "demo-")
    suffix = project.WfiMorphBundles.Create(analysis, "-suffix")
    print(f"   Created stem: {project.WfiMorphBundles.GetForm(stem)}")
    print(f"   Created suffix: {project.WfiMorphBundles.GetForm(suffix)}")

    # Try to link to lexicon
    print("\n3. Link morpheme to lexicon:")
    # Find first lexical entry with a sense
    for lex_entry in project.LexEntry.GetAll():
        if lex_entry.SensesOS.Count > 0:
            sense = lex_entry.SensesOS[0]
            headword = project.LexEntry.GetHeadword(lex_entry)
            gloss = project.Senses.GetGloss(sense)

            project.WfiMorphBundles.SetSense(stem, sense)
            print(f"   Linked stem to: {headword} ({gloss})")
            break
    else:
        print("   No lexical entries found to link")

    return [stem, suffix]


def demo_human_approval(project, wordform, analysis, gloss):
    """Demonstrate human approval workflow."""
    print("\n=== Human Approval Workflow ===\n")

    print("1. Approval distinguishes verified analyses from parser guesses")
    print("   Parser generates hypotheses → Linguist approves best analysis")

    # Check current approval
    print("\n2. Current approval status:")
    approved_analysis = project.Wordforms.GetApprovedAnalysis(wordform)
    if approved_analysis:
        print(f"   Wordform has approved analysis (HVO: {approved_analysis.Hvo})")
    else:
        print("   No approved analysis yet")

    # Approve the analysis
    print("\n3. Approve analysis:")
    project.WfiAnalyses.Approve(analysis)
    print(f"   Analysis approved (HVO: {analysis.Hvo})")

    # Verify approval
    print("\n4. Verify approval:")
    is_approved = project.WfiAnalyses.IsHumanApproved(analysis)
    print(f"   Analysis is approved: {is_approved}")

    # Also approve the gloss (implicitly approves analysis)
    print("\n5. Approve gloss:")
    project.WfiGlosses.Approve(gloss)
    print(f"   Gloss approved: {project.WfiGlosses.GetForm(gloss)}")


def demo_inventory_statistics(project):
    """Demonstrate inventory statistics and queries."""
    print("\n=== Inventory Statistics ===\n")

    print("1. Overall statistics:")
    total_wordforms = sum(1 for _ in project.Wordforms.GetAll())
    print(f"   Total wordforms: {total_wordforms}")

    # Count wordforms with/without analyses
    with_analyses = 0
    without_analyses = 0
    with_approved = 0
    total_analyses = 0

    for wf in project.Wordforms.GetAll():
        analyses = project.Wordforms.GetAnalyses(wf)
        if analyses:
            with_analyses += 1
            total_analyses += len(analyses)
            if project.Wordforms.GetApprovedAnalysis(wf):
                with_approved += 1
        else:
            without_analyses += 1

    print(f"   Wordforms with analyses: {with_analyses}")
    print(f"   Wordforms without analyses: {without_analyses}")
    print(f"   Wordforms with approved analyses: {with_approved}")
    print(f"   Total analyses: {total_analyses}")

    if with_analyses > 0:
        print(f"   Average analyses per wordform: {total_analyses / with_analyses:.2f}")
        print(f"   Approval rate: {with_approved / with_analyses * 100:.1f}%")


def demo_typical_workflow(project):
    """Demonstrate typical interlinear text workflow."""
    print("\n=== Typical Interlinear Text Workflow ===\n")

    print("This workflow shows how wordforms are used in interlinear text analysis:")
    print()
    print("1. Text import: Unique wordforms extracted → added to inventory")
    print("2. Parser analysis: Generates analyses with morpheme breakdowns")
    print("3. Human approval: Linguist reviews and approves best analysis")
    print("4. Lexicon linking: Morphemes linked to lexical entries")
    print("5. Parser training: Approved analyses train parser for better guesses")
    print()
    print("Key pattern: FindOrCreate() ensures no duplicate wordforms")
    print()

    # Simulate processing a word from text
    print("Example: Processing 'running' from text")
    test_word = "running-example"

    # Step 1: Find or create wordform
    wf = project.Wordforms.FindOrCreate(test_word)
    print(f"   ✓ Got wordform: {project.Wordforms.GetForm(wf)}")

    # Step 2: Create analysis (parser would do this)
    analysis = project.WfiAnalyses.Create(wf)
    print(f"   ✓ Created analysis")

    # Step 3: Add gloss
    gloss = project.WfiGlosses.Create(analysis, "running", project.WSHandle("en"))
    print(f"   ✓ Added gloss: {project.WfiGlosses.GetForm(gloss)}")

    # Step 4: Create morpheme breakdown
    stem = project.WfiMorphBundles.Create(analysis, "run")
    suffix = project.WfiMorphBundles.Create(analysis, "-ning")
    print(f"   ✓ Created morpheme bundles: run + -ning")

    # Step 5: Human approval
    project.WfiAnalyses.Approve(analysis)
    print(f"   ✓ Approved analysis")

    print("\n   This approved analysis now trains the parser for future texts!")


def main():
    """Main demo function."""
    # Get project name from command line or use default
    project_name = sys.argv[1] if len(sys.argv) > 1 else "Sena 3"

    print(f"===================================================")
    print(f"Wordform Inventory Operations Demo")
    print(f"MOST ACTIVE AREA: 727+ commits in 2024!")
    print(f"Project: {project_name}")
    print(f"===================================================")

    # Initialize project
    project = FLExProject()

    try:
        # Open project with write access
        print(f"\nOpening project: {project_name}...")
        project.OpenProject(project_name, writeEnabled=True)
        print("Project opened successfully!")

        # Run demonstrations
        wordform = demo_wordform_basics(project)
        analysis = demo_wordform_analyses(project, wordform)
        gloss = demo_wordform_glosses(project, analysis)
        bundles = demo_morpheme_bundles(project, analysis)
        demo_human_approval(project, wordform, analysis, gloss)
        demo_inventory_statistics(project)
        demo_typical_workflow(project)

        print("\n=== Demo Complete ===\n")
        print("Key Operations Demonstrated:")
        print("  ✓ Wordform FindOrCreate pattern")
        print("  ✓ Creating morphological analyses")
        print("  ✓ Adding glosses")
        print("  ✓ Morpheme bundles (lexicon linking)")
        print("  ✓ Human approval workflow")
        print("  ✓ Inventory statistics")
        print("  ✓ Typical interlinear text workflow")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Close project
        if project.project:
            print("\nClosing project...")
            project.CloseProject()
            print("Project closed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
