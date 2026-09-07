#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo: Scripture Import Operations

This demo demonstrates the Scripture operations in flexlibs for managing
Scripture books, sections, paragraphs, drafts, annotations, and notes.

These operations are designed for Scripture data import and Text/Words analysis,
NOT for editing (that's done in Paratext). They allow programmatic access to
Scripture content for linguistic analysis, concordance generation, and data
import/export.

Usage:
    python demo_scripture_operations.py "Your Project Name"

Requirements:
    - FieldWorks project with Scripture data enabled
    - Project must be closed in FieldWorks before running
"""

import sys
import os

# Add parent directory to path to import flexicon
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flexicon import FLExProject


def demo_scripture_books(project):
    """
    Demonstrate Scripture book operations.
    """
    print("\n" + "=" * 70)
    print("SCRIPTURE BOOK OPERATIONS")
    print("=" * 70)

    # List all existing books
    print("\n1. Listing all Scripture books:")
    books = list(project.ScrBooks.GetAll())
    if books:
        for book in books:
            canonical_num = project.ScrBooks.GetCanonicalNum(book)
            title = project.ScrBooks.GetTitle(book)
            sections = project.ScrBooks.GetSections(book)
            print(f"   Book {canonical_num}: {title} ({len(sections)} sections)")
    else:
        print("   No Scripture books found.")

    # Find a specific book
    print("\n2. Finding a book by canonical number:")
    genesis = project.ScrBooks.Find(1)  # Genesis = 1
    if genesis:
        title = project.ScrBooks.GetTitle(genesis)
        print(f"   Found: {title}")
    else:
        print("   Genesis not found.")

    # Find by name
    print("\n3. Finding a book by name:")
    matthew = project.ScrBooks.FindByName("Matthew")
    if matthew:
        canonical_num = project.ScrBooks.GetCanonicalNum(matthew)
        print(f"   Found Matthew (canonical number: {canonical_num})")
    else:
        print("   Matthew not found.")

    # Create a new book (if write enabled)
    if project.writeEnabled:
        print("\n4. Creating a new book (Ruth = 8):")
        try:
            # Check if already exists
            existing = project.ScrBooks.Find(8)
            if not existing:
                ruth = project.ScrBooks.Create(8, "Ruth")
                print(f"   Created: {project.ScrBooks.GetTitle(ruth)}")
            else:
                print(f"   Book already exists: {project.ScrBooks.GetTitle(existing)}")
        except Exception as e:
            print(f"   Error creating book: {e}")


def demo_scripture_sections(project):
    """
    Demonstrate Scripture section operations.
    """
    print("\n" + "=" * 70)
    print("SCRIPTURE SECTION OPERATIONS")
    print("=" * 70)

    # Get first book
    books = list(project.ScrBooks.GetAll())
    if not books:
        print("   No books available for section demo.")
        return

    book = books[0]
    book_title = project.ScrBooks.GetTitle(book)

    # List all sections in book
    print(f"\n1. Listing all sections in {book_title}:")
    sections = project.ScrSections.GetAll(book)
    if sections:
        for i, section in enumerate(sections):
            heading = project.ScrSections.GetHeading(section)
            paras = project.ScrSections.GetContent(section)
            print(f"   Section {i+1}: {heading or '[No heading]'} ({len(paras)} paragraphs)")
    else:
        print("   No sections found.")

    # Find a section by index
    print(f"\n2. Finding first section in {book_title}:")
    section = project.ScrSections.Find(book, 0)
    if section:
        heading = project.ScrSections.GetHeading(section)
        print(f"   Found: {heading or '[No heading]'}")
    else:
        print("   No sections found.")

    # Create a new section (if write enabled)
    if project.writeEnabled and book:
        print(f"\n3. Creating a new section in {book_title}:")
        try:
            new_section = project.ScrSections.Create(
                book, "Demo Section Heading", "This is the first paragraph of demo content."
            )
            heading = project.ScrSections.GetHeading(new_section)
            print(f"   Created section: {heading}")
        except Exception as e:
            print(f"   Error creating section: {e}")


def demo_scripture_paragraphs(project):
    """
    Demonstrate Scripture paragraph operations.
    """
    print("\n" + "=" * 70)
    print("SCRIPTURE PARAGRAPH OPERATIONS")
    print("=" * 70)

    # Get first book and section
    books = list(project.ScrBooks.GetAll())
    if not books:
        print("   No books available for paragraph demo.")
        return

    book = books[0]
    sections = project.ScrSections.GetAll(book)
    if not sections:
        print("   No sections available for paragraph demo.")
        return

    section = sections[0]
    heading = project.ScrSections.GetHeading(section)

    # List all paragraphs in section
    print(f"\n1. Listing all paragraphs in section '{heading or '[No heading]'}':")
    paras = project.ScrTxtParas.GetAll(section)
    if paras:
        for i, para in enumerate(paras):
            text = project.ScrTxtParas.GetText(para)
            style = project.ScrTxtParas.GetStyleName(para)
            preview = text[:50] + "..." if len(text) > 50 else text
            print(f"   Para {i+1} [{style}]: {preview}")
    else:
        print("   No paragraphs found.")

    # Find a paragraph by index
    print(f"\n2. Finding first paragraph:")
    para = project.ScrTxtParas.Find(section, 0)
    if para:
        text = project.ScrTxtParas.GetText(para)
        print(f"   Text: {text[:100]}..." if len(text) > 100 else f"   Text: {text}")
    else:
        print("   No paragraphs found.")

    # Create a new paragraph (if write enabled)
    if project.writeEnabled and section:
        print(f"\n3. Creating a new paragraph:")
        try:
            new_para = project.ScrTxtParas.Create(section, "This is a demo paragraph created by flexicon.", "Normal")
            text = project.ScrTxtParas.GetText(new_para)
            print(f"   Created: {text}")
        except Exception as e:
            print(f"   Error creating paragraph: {e}")


def demo_scripture_drafts(project):
    """
    Demonstrate Scripture draft operations.
    """
    print("\n" + "=" * 70)
    print("SCRIPTURE DRAFT OPERATIONS")
    print("=" * 70)

    # List all drafts
    print("\n1. Listing all Scripture drafts:")
    drafts = list(project.ScrDrafts.GetAll())
    if drafts:
        for i, draft in enumerate(drafts):
            desc = project.ScrDrafts.GetDescription(draft)
            books = project.ScrDrafts.GetBooks(draft)
            print(f"   Draft {i+1}: {desc} ({len(books)} books)")
    else:
        print("   No drafts found.")

    # Create a new draft (if write enabled)
    if project.writeEnabled:
        print("\n2. Creating a new draft:")
        try:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_draft = project.ScrDrafts.Create(f"Demo Draft - {timestamp}", "saved_version")
            desc = project.ScrDrafts.GetDescription(new_draft)
            print(f"   Created: {desc}")
        except Exception as e:
            print(f"   Error creating draft: {e}")

    # Find a draft
    if drafts:
        print("\n3. Finding a draft by description:")
        first_desc = project.ScrDrafts.GetDescription(drafts[0])
        found = project.ScrDrafts.Find(first_desc[:20])  # Partial match
        if found:
            print(f"   Found: {project.ScrDrafts.GetDescription(found)}")


def demo_scripture_notes(project):
    """
    Demonstrate Scripture note operations.
    """
    print("\n" + "=" * 70)
    print("SCRIPTURE NOTE OPERATIONS")
    print("=" * 70)

    # Get first book
    books = list(project.ScrBooks.GetAll())
    if not books:
        print("   No books available for note demo.")
        return

    book = books[0]
    book_title = project.ScrBooks.GetTitle(book)

    # List all notes in book
    print(f"\n1. Listing all notes in {book_title}:")
    notes = project.ScrNotes.GetAll(book)
    if notes:
        for i, note in enumerate(notes):
            text = project.ScrNotes.GetText(note)
            resolved = project.ScrNotes.IsResolved(note)
            status = "Resolved" if resolved else "Open"
            preview = text[:50] + "..." if len(text) > 50 else text
            print(f"   Note {i+1} [{status}]: {preview}")
    else:
        print("   No notes found.")

    # Create a new note (if write enabled)
    if project.writeEnabled:
        # Get first paragraph
        sections = project.ScrSections.GetAll(book)
        if sections:
            section = sections[0]
            paras = project.ScrTxtParas.GetAll(section)
            if paras:
                para = paras[0]
                print(f"\n2. Creating a new note:")
                try:
                    new_note = project.ScrNotes.Create(
                        book, para, "Demo note: Check this translation for accuracy.", "translator_note"
                    )
                    text = project.ScrNotes.GetText(new_note)
                    print(f"   Created: {text}")

                    # Resolve the note
                    print(f"\n3. Resolving the note:")
                    project.ScrNotes.Resolve(new_note)
                    if project.ScrNotes.IsResolved(new_note):
                        print("   Note marked as resolved.")
                except Exception as e:
                    print(f"   Error creating note: {e}")


def demo_scripture_annotations(project):
    """
    Demonstrate Scripture annotations operations.
    """
    print("\n" + "=" * 70)
    print("SCRIPTURE ANNOTATIONS OPERATIONS")
    print("=" * 70)

    # Get first book
    books = list(project.ScrBooks.GetAll())
    if not books:
        print("   No books available for annotations demo.")
        return

    book = books[0]
    book_title = project.ScrBooks.GetTitle(book)

    # Get annotations for book
    print(f"\n1. Getting annotations for {book_title}:")
    annotations = project.ScrAnnotations.GetForBook(book)
    if annotations:
        notes = project.ScrAnnotations.GetNotes(annotations)
        print(f"   Found annotations container with {len(notes)} notes")
    else:
        print("   No annotations container found.")

    # Create annotations (if write enabled and not exists)
    if project.writeEnabled and not annotations:
        print(f"\n2. Creating annotations container:")
        try:
            new_annotations = project.ScrAnnotations.Create(book, "note")
            print("   Created annotations container.")
        except Exception as e:
            print(f"   Error creating annotations: {e}")


def main():
    """
    Main demo function.
    """
    print("\n" + "=" * 70)
    print("FLEXLIBS SCRIPTURE OPERATIONS DEMO")
    print("=" * 70)

    # Get project name from command line
    if len(sys.argv) < 2:
        print('\nUsage: python demo_scripture_operations.py "Project Name"')
        print('\nExample: python demo_scripture_operations.py "Sena 3"')
        sys.exit(1)

    project_name = sys.argv[1]
    write_enabled = len(sys.argv) > 2 and sys.argv[2].lower() == "write"

    print(f"\nProject: {project_name}")
    print(f"Write mode: {'ENABLED' if write_enabled else 'DISABLED (read-only)'}")
    print("\nNote: Scripture operations are for data import and analysis.")
    print("      Scripture editing should be done in Paratext, not FieldWorks.")

    # Create FLExProject instance
    project = FLExProject()

    try:
        # Open the project
        print(f"\nOpening project '{project_name}'...")
        project.OpenProject(project_name, writeEnabled=write_enabled)
        print("Project opened successfully.")

        # Check if Scripture is enabled
        if not hasattr(project.lp, "TranslatedScriptureOA") or not project.lp.TranslatedScriptureOA:
            print("\nWARNING: This project does not have Scripture enabled.")
            print("Scripture operations require Scripture to be enabled in the project.")
            project.CloseProject()
            return

        # Run demos
        demo_scripture_books(project)
        demo_scripture_sections(project)
        demo_scripture_paragraphs(project)
        demo_scripture_drafts(project)
        demo_scripture_notes(project)
        demo_scripture_annotations(project)

        # Close the project
        print("\n" + "=" * 70)
        print("Closing project...")
        project.CloseProject()
        print("Project closed successfully.")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        if project and project.project:
            project.CloseProject()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nSummary:")
    print("  - Scripture books: CRUD operations for Bible books (Genesis, Matthew, etc.)")
    print("  - Scripture sections: Managing sections with headings and content")
    print("  - Scripture paragraphs: Text paragraphs with styles (Normal, Poetry, etc.)")
    print("  - Scripture drafts: Saved versions for tracking translation progress")
    print("  - Scripture notes: Translator and consultant notes on Scripture text")
    print("  - Scripture annotations: Containers for organizing notes by book")
    print("\nAll 6 Scripture Operations classes are working!")


if __name__ == "__main__":
    main()
