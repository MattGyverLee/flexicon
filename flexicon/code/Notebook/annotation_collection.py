#
#   annotation_collection.py
#
#   Class: AnnotationCollection
#          Smart collection for annotations with type-aware filtering
#          and unified access across definition-based types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for annotations.

This module provides AnnotationCollection, a smart collection that manages
annotations while showing type diversity and supporting unified operations
across different annotation types.

Problem:
    GetAll() returns annotations with different types (defined by AnnotationDefn).
    Users need to:
    - See which types are represented
    - Filter by type if they want to
    - Work with all types together without manual type checking
    - Filter by metadata (author, date range, content)

Solution:
    AnnotationCollection provides:
    - __str__() showing type breakdown by AnnotationDefn
    - by_type() filtering to specific annotation types
    - filter() for common criteria (annotation_type, author, date_created)
    - Convenience methods (scripture_annotations(), translator_notes(), etc.)
    - Chainable filtering: annos.scripture().filter(author='John')

Example::

    from flexlibs2.code.Notebook.annotation_collection import AnnotationCollection

    # GetAll() returns AnnotationCollection
    annos = noteOps.GetAll(entry)
    print(annos)  # Shows type breakdown
    # AnnotationCollection (12 total)
    #   To Do: 5 (42%)
    #   Question: 4 (33%)
    #   ScrScriptureNote: 3 (25%)

    # Filter by type
    todos = annos.by_type("To Do")
    print(len(todos))  # 5

    # Filter by author
    john_notes = annos.filter(author="John")

    # Filter by date
    from System import DateTime
    one_week_ago = DateTime.Now.AddDays(-7)
    recent = annos.filter(since=one_week_ago)

    # Chain filters
    john_todos = annos.by_type("To Do").filter(author="John")

    # Use convenience methods
    scripture = annos.scripture()
    translator = annos.translator()

    # Iterate
    for anno in annos:
        print(f"{anno.annotation_type}: {anno.content}")
"""

from ..Shared.smart_collection import SmartCollection
from .annotation import Annotation

try:
    from System import DateTime
except ImportError:
    # Mock for testing
    from datetime import datetime

    class DateTime:
        def __init__(self, year=2025, month=1, day=1, hour=0, minute=0, second=0):
            self.dt = datetime(year, month, day, hour, minute, second)

        def AddDays(self, days):
            result = DateTime()
            import datetime as dt_module

            result.dt = self.dt + dt_module.timedelta(days=days)
            return result

        @classmethod
        def Now(cls):
            now = datetime.now()
            return cls(now.year, now.month, now.day, now.hour, now.minute, now.second)

        def __lt__(self, other):
            return self.dt < other.dt

        def __le__(self, other):
            return self.dt <= other.dt

        def __gt__(self, other):
            return self.dt > other.dt

        def __ge__(self, other):
            return self.dt >= other.dt

        def __eq__(self, other):
            if isinstance(other, DateTime):
                return self.dt == other.dt
            return False


class AnnotationCollection(SmartCollection):
    """
    Smart collection for annotations with type-aware filtering.

    Manages collections of annotation (Annotation wrapper objects) with
    type-aware display and filtering capabilities. Supports filtering by
    annotation type, author, date, and custom predicates.

    Attributes:
        _items: List of Annotation wrapper objects

    Example::

        annos = noteOps.GetAll(entry)  # Returns AnnotationCollection
        print(annos)  # Shows type breakdown
        todos = annos.by_type("To Do")  # Filter to To Do
        john = annos.filter(author="John")  # Filter by author
        both = annos.by_type("To Do").filter(author="John")  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize an AnnotationCollection.

        Args:
            items: Iterable of Annotation objects, or None for empty.

        Example::

            collection = AnnotationCollection()
            collection = AnnotationCollection([anno1, anno2, anno3])
        """
        super().__init__(items)

    def filter(self, annotation_type=None, author=None, since=None, until=None, content_contains=None, where=None):
        """
        Filter the collection by annotation properties.

        Supports filtering by properties that work across all annotation types
        (annotation_type, author, date range, content). For complex filtering,
        use where().

        Args:
            annotation_type (str, optional): Filter to annotations with this type.
                Case-sensitive match of AnnotationDefn.Name.
            author (str, optional): Filter to annotations by this author.
                Case-sensitive match of Source property.
            since (System.DateTime, optional): Filter to annotations created
                on or after this date.
            until (System.DateTime, optional): Filter to annotations created
                on or before this date.
            content_contains (str, optional): Filter to annotations whose content
                contains this string (case-sensitive).
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored. Receives Annotation wrapper object.

        Returns:
            AnnotationCollection: New collection with filtered items.

        Example::

            # Filter by annotation type
            todos = annos.filter(annotation_type="To Do")

            # Filter by author
            john_notes = annos.filter(author="John")

            # Filter by date range
            from System import DateTime
            start = DateTime(2025, 1, 1)
            end = DateTime(2025, 12, 31)
            year_notes = annos.filter(since=start, until=end)

            # Filter by content
            etymology = annos.filter(content_contains="etymology")

            # Custom filtering
            recent_todos = annos.where(
                lambda a: a.annotation_type == "To Do" and
                a.date_created and
                a.date_created > DateTime.Now.AddDays(-7)
            )

            # Chain filters
            john_todos = annos.filter(author="John").filter(annotation_type="To Do")

        Notes:
            - All criteria are AND-ed together if multiple provided
            - String comparisons are case-sensitive
            - where() takes precedence over other criteria
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        # If custom predicate provided, use it
        if where is not None:
            filtered = [a for a in self._items if where(a)]
            return AnnotationCollection(filtered)

        # Apply criteria filters
        filtered = []
        for anno in self._items:
            # Check annotation_type
            if annotation_type is not None:
                if anno.annotation_type != annotation_type:
                    continue

            # Check author
            if author is not None:
                if anno.author != author:
                    continue

            # Check since (created on or after)
            if since is not None:
                if anno.date_created is None or anno.date_created < since:
                    continue

            # Check until (created on or before)
            if until is not None:
                if anno.date_created is None or anno.date_created > until:
                    continue

            # Check content contains
            if content_contains is not None:
                if content_contains not in anno.content:
                    continue

            # All criteria passed
            filtered.append(anno)

        return AnnotationCollection(filtered)

    def by_type(self, annotation_type):
        """
        Filter the collection to a specific annotation type.

        Returns a new collection containing only annotations of the specified type.

        Args:
            annotation_type (str): The annotation type name to filter by.
                Case-sensitive match of AnnotationDefn.Name.

        Returns:
            AnnotationCollection: New collection with filtered items.

        Example::

            todos = annos.by_type("To Do")
            print(len(todos))  # Number of To Do annotations

            questions = annos.by_type("Question")

        Notes:
            - Type comparison is case-sensitive
            - Returns empty collection if no matching types
            - Equivalent to filter(annotation_type=type_name)
        """
        return self.filter(annotation_type=annotation_type)

    def by_author(self, author):
        """
        Filter the collection to annotations by a specific author.

        Returns a new collection containing only annotations with the specified author.

        Args:
            author (str): The author name to filter by.
                Case-sensitive match of Source property.

        Returns:
            AnnotationCollection: New collection with filtered items.

        Example::

            john_notes = annos.by_author("John")
            print(len(john_notes))  # Number of annotations by John

        Notes:
            - Author comparison is case-sensitive
            - Returns empty collection if no matching authors
            - Equivalent to filter(author=author_name)
        """
        return self.filter(author=author)

    def created_since(self, date):
        """
        Filter the collection to annotations created on or after a date.

        Args:
            date (System.DateTime): The cutoff date (inclusive).

        Returns:
            AnnotationCollection: New collection with filtered items.

        Example::

            from System import DateTime
            one_week_ago = DateTime.Now.AddDays(-7)
            recent = annos.created_since(one_week_ago)

        Notes:
            - Date comparison is inclusive (>= date)
            - Returns annotations without DateCreated in results
        """
        return self.filter(since=date)

    def created_until(self, date):
        """
        Filter the collection to annotations created on or before a date.

        Args:
            date (System.DateTime): The cutoff date (inclusive).

        Returns:
            AnnotationCollection: New collection with filtered items.

        Example::

            from System import DateTime
            end_of_year = DateTime(2025, 12, 31)
            old_notes = annos.created_until(end_of_year)

        Notes:
            - Date comparison is inclusive (<= date)
        """
        return self.filter(until=date)

    # ========== Convenience Type Filters ==========

    def scripture(self):
        """
        Filter to Scripture annotations.

        Returns a new collection containing only Scripture-type annotations
        (types containing 'Scripture' or 'Scr').

        Returns:
            AnnotationCollection: New collection with Scripture annotations.

        Example::

            scripture_notes = annos.scripture()
            print(len(scripture_notes))  # Number of Scripture notes

        Notes:
            - Uses the Annotation.is_scripture property
            - Case-insensitive type matching
        """
        filtered = [a for a in self._items if a.is_scripture]
        return AnnotationCollection(filtered)

    def translator(self):
        """
        Filter to translator notes.

        Returns a new collection containing only translator-type annotations
        (types containing 'Translator').

        Returns:
            AnnotationCollection: New collection with translator notes.

        Example::

            translator_notes = annos.translator()
            print(len(translator_notes))  # Number of translator notes

        Notes:
            - Uses the Annotation.is_translator property
            - Case-insensitive type matching
        """
        filtered = [a for a in self._items if a.is_translator]
        return AnnotationCollection(filtered)

    def consultant(self):
        """
        Filter to consultant notes.

        Returns a new collection containing only consultant-type annotations
        (types containing 'Consultant').

        Returns:
            AnnotationCollection: New collection with consultant notes.

        Example::

            consultant_notes = annos.consultant()
            print(len(consultant_notes))  # Number of consultant notes

        Notes:
            - Uses the Annotation.is_consultant property
            - Case-insensitive type matching
        """
        filtered = [a for a in self._items if a.is_consultant]
        return AnnotationCollection(filtered)

    def todos(self):
        """
        Filter to "To Do" annotations.

        Returns a new collection containing only "To Do" type annotations.

        Returns:
            AnnotationCollection: New collection with To Do annotations.

        Example::

            todos = annos.todos()
            print(len(todos))  # Number of To Do items

        Notes:
            - Uses the Annotation.is_todo property
            - Case-insensitive type matching
        """
        filtered = [a for a in self._items if a.is_todo]
        return AnnotationCollection(filtered)

    def questions(self):
        """
        Filter to question annotations.

        Returns a new collection containing only question-type annotations
        (types containing 'Question' or 'Query').

        Returns:
            AnnotationCollection: New collection with question annotations.

        Example::

            questions = annos.questions()
            print(len(questions))  # Number of questions

        Notes:
            - Uses the Annotation.is_question property
            - Case-insensitive type matching
        """
        filtered = [a for a in self._items if a.is_question]
        return AnnotationCollection(filtered)

    def with_replies(self):
        """
        Filter to annotations that have replies.

        Returns a new collection containing only annotations with at least one reply.

        Returns:
            AnnotationCollection: New collection with annotations that have replies.

        Example::

            threaded = annos.with_replies()
            print(len(threaded))  # Number of annotations with discussion threads

        Notes:
            - Uses the Annotation.has_replies property
        """
        filtered = [a for a in self._items if a.has_replies]
        return AnnotationCollection(filtered)

    # ========== Collection Information ==========

    def get_types(self):
        """
        Get all unique annotation types in the collection.

        Returns:
            list: List of unique annotation type names (strings).

        Example::

            types = annos.get_types()
            for type_name in types:
                print(f"Type: {type_name}")
            # Type: To Do
            # Type: Question
            # Type: ScrScriptureNote

        Notes:
            - Returns unique type names only
            - Order is based on first appearance in collection
        """
        seen = set()
        types = []
        for anno in self._items:
            anno_type = anno.annotation_type
            if anno_type and anno_type not in seen:
                seen.add(anno_type)
                types.append(anno_type)
        return types

    def get_authors(self):
        """
        Get all unique authors in the collection.

        Returns:
            list: List of unique author names (strings).

        Example::

            authors = annos.get_authors()
            for author in authors:
                print(f"Author: {author}")

        Notes:
            - Returns unique author names only
            - Includes empty strings if any annotations have no author set
            - Order is based on first appearance in collection
        """
        seen = set()
        authors = []
        for anno in self._items:
            author = anno.author
            if author and author not in seen:
                seen.add(author)
                authors.append(author)
        return authors

    def __str__(self):
        """
        String representation showing annotation type breakdown.

        Shows the total count and breakdown by annotation type.

        Returns:
            str: Multi-line string showing type distribution.

        Example::

            print(annos)
            # AnnotationCollection (12 total)
            #   To Do: 5 (42%)
            #   Question: 4 (33%)
            #   ScrScriptureNote: 3 (25%)

        Notes:
            - Shows percentage of each type
            - Types are sorted by count (highest first)
            - Empty collection shows "(0 total)"
        """
        if not self._items:
            return "AnnotationCollection (0 total)"

        # Count by type
        type_counts = {}
        for anno in self._items:
            anno_type = anno.annotation_type
            if not anno_type:
                anno_type = "[Untyped]"
            type_counts[anno_type] = type_counts.get(anno_type, 0) + 1

        # Sort by count (highest first)
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

        # Build display string
        lines = [f"AnnotationCollection ({len(self._items)} total)"]
        for anno_type, count in sorted_types:
            percentage = (count * 100) // len(self._items) if self._items else 0
            lines.append(f"  {anno_type}: {count} ({percentage}%)")

        return "\n".join(lines)

    def __repr__(self):
        """Brief representation."""
        if not self._items:
            return "AnnotationCollection()"
        return f"AnnotationCollection({len(self._items)} items, types: {', '.join(self.get_types()[:3])}{'...' if len(self.get_types()) > 3 else ''})"
