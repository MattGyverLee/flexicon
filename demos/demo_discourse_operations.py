"""
Demo script for Discourse Analysis Operations in flexicon.

This script demonstrates the complete workflow for constituent chart analysis
in FieldWorks Language Explorer projects using the flexlibs library.

Demonstrates:
- Creating constituent charts for discourse analysis
- Managing chart rows and labels
- Creating word groups linked to text segments
- Marking moved text (preposed/postposed)
- Using chart tags for discourse annotation
- Creating clause markers with dependencies

Requirements:
- FieldWorks project with analyzed texts
- Python.NET and flexlibs installed
- Write access to project
"""

from flexicon import FLExProject


def demo_constituent_charts(project):
    """
    Demonstrate constituent chart operations.

    Shows how to create and manage discourse analysis charts.
    """
    print("\n" + "=" * 60)
    print("DEMO: Constituent Chart Operations")
    print("=" * 60)

    # Create a new constituent chart
    print("\n1. Creating a constituent chart...")
    chart = project.ConstCharts.Create("Demo Discourse Analysis")
    print(f"   Created chart: {project.ConstCharts.GetName(chart)}")

    # Set chart name
    print("\n2. Updating chart name...")
    project.ConstCharts.SetName(chart, "Genesis 1:1 - Constituent Analysis")
    print(f"   Updated chart name: {project.ConstCharts.GetName(chart)}")

    # List all charts
    print("\n3. Listing all constituent charts...")
    chart_count = 0
    for c in project.ConstCharts.GetAll():
        name = project.ConstCharts.GetName(c)
        row_count = len(project.ConstCharts.GetRows(c))
        print(f"   - {name} ({row_count} rows)")
        chart_count += 1
    print(f"   Total charts: {chart_count}")

    return chart


def demo_chart_rows(project, chart):
    """
    Demonstrate chart row operations.

    Shows how to create and manage rows in a constituent chart.
    """
    print("\n" + "=" * 60)
    print("DEMO: Chart Row Operations")
    print("=" * 60)

    # Create rows
    print("\n1. Creating chart rows...")
    row1 = project.ConstChartRows.Create(chart, label="Verse 1a", notes="Subject clause")
    print(f"   Created row 1: {project.ConstChartRows.GetLabel(row1)}")

    row2 = project.ConstChartRows.Create(chart, label="Verse 1b", notes="Predicate clause")
    print(f"   Created row 2: {project.ConstChartRows.GetLabel(row2)}")

    row3 = project.ConstChartRows.Create(chart, label="Verse 1c", notes="Object clause")
    print(f"   Created row 3: {project.ConstChartRows.GetLabel(row3)}")

    # Update row properties
    print("\n2. Updating row properties...")
    project.ConstChartRows.SetLabel(row1, "Verse 1a - Temporal")
    project.ConstChartRows.SetNotes(row1, "Temporal setting clause")
    print(f"   Updated row 1: {project.ConstChartRows.GetLabel(row1)}")
    print(f"   Notes: {project.ConstChartRows.GetNotes(row1)}")

    # List all rows
    print("\n3. Listing all rows in chart...")
    rows = project.ConstChartRows.GetAll(chart)
    for i, row in enumerate(rows):
        label = project.ConstChartRows.GetLabel(row)
        notes = project.ConstChartRows.GetNotes(row)
        print(f"   Row {i}: {label}")
        if notes:
            print(f"          Notes: {notes}")

    # Move a row
    print("\n4. Reordering rows...")
    print(f"   Moving row 3 to position 1...")
    project.ConstChartRows.MoveTo(row3, chart, 1)
    print("   New row order:")
    for i, row in enumerate(project.ConstChartRows.GetAll(chart)):
        label = project.ConstChartRows.GetLabel(row)
        print(f"   Row {i}: {label}")

    return row1, row2, row3


def demo_word_groups(project, chart, row1):
    """
    Demonstrate word group operations.

    Shows how to create word groups linked to text segments.
    Note: This requires an actual text with segments in the project.
    """
    print("\n" + "=" * 60)
    print("DEMO: Word Group Operations")
    print("=" * 60)

    print("\n1. Checking for texts in project...")
    texts = list(project.TextCatalog())
    if not texts:
        print("   No texts found in project.")
        print("   Skipping word group demo (requires analyzed text).")
        return None

    # Get first text and its segments
    text = texts[0]
    print(f"   Found text: {text.Name.BestAnalysisAlternative.Text}")

    if not text.ContentsOA or text.ContentsOA.ParagraphsOS.Count == 0:
        print("   Text has no paragraphs.")
        print("   Skipping word group demo.")
        return None

    para = text.ContentsOA.ParagraphsOS[0]
    segments = list(para.SegmentsOS)

    if len(segments) < 3:
        print(f"   Not enough segments ({len(segments)} found, need at least 3).")
        print("   Skipping word group demo.")
        return None

    print(f"   Found {len(segments)} segments in first paragraph")

    # Create word groups
    print("\n2. Creating word groups...")
    wg1 = project.ConstChartWordGroups.Create(row1, segments[0], segments[0])
    print(f"   Created word group 1 (segment 0-0)")

    if len(segments) >= 2:
        wg2 = project.ConstChartWordGroups.Create(row1, segments[1], segments[2])
        print(f"   Created word group 2 (segments 1-2)")

    # List word groups
    print("\n3. Listing word groups in row...")
    word_groups = project.ConstChartWordGroups.GetAll(row1)
    for i, wg in enumerate(word_groups):
        begin = project.ConstChartWordGroups.GetBeginSegment(wg)
        end = project.ConstChartWordGroups.GetEndSegment(wg)
        if begin and end:
            print(f"   Word group {i}: segments {begin.Hvo} to {end.Hvo}")

    return wg1 if word_groups else None


def demo_moved_text(project, chart, word_group):
    """
    Demonstrate moved text marker operations.

    Shows how to mark text as preposed or postposed.
    """
    print("\n" + "=" * 60)
    print("DEMO: Moved Text Marker Operations")
    print("=" * 60)

    if not word_group:
        print("\n   No word group available for moved text demo.")
        return

    # Create moved text marker
    print("\n1. Marking word group as preposed...")
    marker = project.ConstChartMovedText.Create(word_group, preposed=True)
    print(f"   Created moved text marker")
    print(f"   Is preposed: {project.ConstChartMovedText.IsPreposed(marker)}")

    # Change to postposed
    print("\n2. Changing to postposed...")
    project.ConstChartMovedText.SetPreposed(marker, False)
    print(f"   Is preposed: {project.ConstChartMovedText.IsPreposed(marker)}")
    print(f"   Is postposed: {not project.ConstChartMovedText.IsPreposed(marker)}")

    # List all moved text markers
    print("\n3. Listing all moved text markers in chart...")
    markers = project.ConstChartMovedText.GetAll(chart)
    print(f"   Found {len(markers)} moved text markers")
    for i, m in enumerate(markers):
        is_preposed = project.ConstChartMovedText.IsPreposed(m)
        movement_type = "preposed" if is_preposed else "postposed"
        print(f"   Marker {i}: {movement_type}")


def demo_chart_tags(project, chart):
    """
    Demonstrate chart tag operations.

    Shows how to create and manage tags for discourse annotation.
    """
    print("\n" + "=" * 60)
    print("DEMO: Chart Tag Operations")
    print("=" * 60)

    # Create tags
    print("\n1. Creating discourse tags...")
    tag1 = project.ConstChartTags.Create(chart, "Topic")
    project.ConstChartTags.SetDescription(tag1, "Marks the topic of the clause")
    print(f"   Created tag: {project.ConstChartTags.GetName(tag1)}")

    tag2 = project.ConstChartTags.Create(chart, "Focus")
    project.ConstChartTags.SetDescription(tag2, "Marks the focus element")
    print(f"   Created tag: {project.ConstChartTags.GetName(tag2)}")

    tag3 = project.ConstChartTags.Create(chart, "Tail")
    project.ConstChartTags.SetDescription(tag3, "Marks tail material")
    print(f"   Created tag: {project.ConstChartTags.GetName(tag3)}")

    # List all tags
    print("\n2. Listing all tags in chart...")
    tags = project.ConstChartTags.GetAll(chart)
    for tag in tags:
        name = project.ConstChartTags.GetName(tag)
        desc = project.ConstChartTags.GetDescription(tag)
        print(f"   - {name}: {desc}")

    # Update a tag
    print("\n3. Updating tag...")
    project.ConstChartTags.SetName(tag1, "Theme")
    project.ConstChartTags.SetDescription(tag1, "Marks the theme of the clause")
    print(f"   Updated tag: {project.ConstChartTags.GetName(tag1)}")
    print(f"   New description: {project.ConstChartTags.GetDescription(tag1)}")


def demo_clause_markers(project, row1, word_group):
    """
    Demonstrate clause marker operations.

    Shows how to create clause markers with dependencies.
    """
    print("\n" + "=" * 60)
    print("DEMO: Clause Marker Operations")
    print("=" * 60)

    if not word_group:
        print("\n   No word group available for clause marker demo.")
        return

    # Get word groups for the row
    word_groups = project.ConstChartWordGroups.GetAll(row1)
    if len(word_groups) < 2:
        print("\n   Not enough word groups for clause marker demo.")
        return

    # Create clause markers
    print("\n1. Creating clause markers...")
    marker1 = project.ConstChartClauseMarkers.Create(row1, word_groups[0])
    print(f"   Created main clause marker")

    marker2 = project.ConstChartClauseMarkers.Create(row1, word_groups[1])
    print(f"   Created dependent clause marker")

    # Add dependency
    print("\n2. Adding dependent clause relationship...")
    project.ConstChartClauseMarkers.AddDependentClause(marker1, marker2)
    print(f"   Marker 2 is now dependent on marker 1")

    # List dependencies
    print("\n3. Checking clause dependencies...")
    dependents = project.ConstChartClauseMarkers.GetDependentClauses(marker1)
    print(f"   Marker 1 has {len(dependents)} dependent clauses")

    # List all markers
    print("\n4. Listing all clause markers in row...")
    markers = project.ConstChartClauseMarkers.GetAll(row1)
    for i, marker in enumerate(markers):
        wg = project.ConstChartClauseMarkers.GetWordGroup(marker)
        deps = project.ConstChartClauseMarkers.GetDependentClauses(marker)
        print(f"   Marker {i}: word group {wg.Hvo if wg else 'None'}")
        print(f"             {len(deps)} dependent clauses")


def cleanup_demo_data(project, chart):
    """
    Clean up demo data (optional).

    Removes the demo chart created during the demonstration.
    """
    print("\n" + "=" * 60)
    print("CLEANUP: Removing Demo Data")
    print("=" * 60)

    print("\nDo you want to delete the demo chart? (y/n): ", end="")
    response = input().strip().lower()

    if response == "y":
        chart_name = project.ConstCharts.GetName(chart)
        project.ConstCharts.Delete(chart)
        print(f"   Deleted chart: {chart_name}")
    else:
        print("   Demo chart preserved.")


def main():
    """
    Main demo function.

    Runs through all discourse analysis operations demonstrations.
    """
    print("=" * 60)
    print("FLEXLIBS DISCOURSE ANALYSIS OPERATIONS DEMO")
    print("=" * 60)
    print("\nThis demo demonstrates constituent chart analysis features.")
    print("It will create charts, rows, word groups, and markers.")

    # Get project name from user
    project_name = input("\nEnter FieldWorks project name: ").strip()
    if not project_name:
        print("Error: Project name required")
        return

    # Open project
    print(f"\nOpening project '{project_name}'...")
    project = FLExProject()

    try:
        project.OpenProject(project_name, writeEnabled=True)
        print(f"Successfully opened: {project.ProjectName()}")

        # Run demonstrations
        chart = demo_constituent_charts(project)
        row1, row2, row3 = demo_chart_rows(project, chart)
        word_group = demo_word_groups(project, chart, row1)
        demo_moved_text(project, chart, word_group)
        demo_chart_tags(project, chart)
        demo_clause_markers(project, row1, word_group)

        # Optional cleanup
        cleanup_demo_data(project, chart)

        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nAll discourse analysis operations demonstrated successfully!")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Close project
        print("\nClosing project...")
        project.CloseProject()
        print("Project closed.")


if __name__ == "__main__":
    main()
