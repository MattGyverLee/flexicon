#
#   test_annotation_wrappers.py
#
#   Tests for AnnotationCollection wrapper class
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Unit tests for AnnotationCollection.

Tests cover:
- AnnotationCollection filtering by type, author, date, content
- Type-aware display and breakdown
- Chained filtering
- Convenience type filters
- Collection operations (iteration, indexing)

Note: Full Annotation wrapper tests are integration tests that require
the complete FLEx/LCM environment. These tests use mock objects to
validate collection filtering logic.
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Try the real flexicon first (works when FieldWorks is installed). Only
# fall back to mocking SIL.* if that fails (CI / no-FW environment).
try:
    import flexicon  # noqa: F401
except Exception:
    sys.modules["SIL"] = MagicMock()
    sys.modules["SIL.LCModel"] = MagicMock()
    sys.modules["SIL.LCModel.Core"] = MagicMock()
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = MagicMock()
    sys.modules["SIL.LCModel.Core.Text"] = MagicMock()


# DateTime mock for testing
class DateTime:
    def __init__(self, year, month, day, hour=0, minute=0, second=0):
        self.dt = datetime(year, month, day, hour, minute, second)

    def AddDays(self, days):
        result = DateTime(self.dt.year, self.dt.month, self.dt.day)
        import datetime as dt_module

        result.dt = self.dt + dt_module.timedelta(days=days)
        return result

    @classmethod
    def Now(cls):
        now = datetime.now()
        return cls(now.year, now.month, now.day, now.hour, now.minute, now.second)

    def __lt__(self, other):
        if not isinstance(other, DateTime):
            return NotImplemented
        return self.dt < other.dt

    def __le__(self, other):
        if not isinstance(other, DateTime):
            return NotImplemented
        return self.dt <= other.dt

    def __gt__(self, other):
        if not isinstance(other, DateTime):
            return NotImplemented
        return self.dt > other.dt

    def __ge__(self, other):
        if not isinstance(other, DateTime):
            return NotImplemented
        return self.dt >= other.dt

    def __eq__(self, other):
        if isinstance(other, DateTime):
            return self.dt == other.dt
        return False

    def __repr__(self):
        return f"{self.dt.year}-{self.dt.month:02d}-{self.dt.day:02d}"


from flexicon.code.Notebook.annotation_collection import AnnotationCollection


class MockAnnotation:
    """Simple mock annotation for testing collection behavior."""

    def __init__(self, annotation_type="", author="", content="", date=None, has_replies=False):
        self.annotation_type = annotation_type
        self.author = author
        self.content = content
        self.date_created = date or DateTime.Now()
        self.has_replies = has_replies

    @property
    def is_scripture(self):
        return "scripture" in self.annotation_type.lower() or "scr" in self.annotation_type.lower()

    @property
    def is_translator(self):
        return "translator" in self.annotation_type.lower()

    @property
    def is_consultant(self):
        return "consultant" in self.annotation_type.lower()

    @property
    def is_todo(self):
        return self.annotation_type.lower() == "to do"

    @property
    def is_question(self):
        return "question" in self.annotation_type.lower() or "query" in self.annotation_type.lower()


class TestAnnotationCollection(unittest.TestCase):
    """Test suite for AnnotationCollection class."""

    def setUp(self):
        """Set up test fixtures."""
        self.date_1 = DateTime(2025, 1, 10)
        self.date_2 = DateTime(2025, 1, 20)
        self.date_3 = DateTime(2025, 2, 1)

    def test_empty_collection(self):
        """Test creating empty collection."""
        collection = AnnotationCollection()
        self.assertEqual(len(collection), 0)
        self.assertEqual(list(collection), [])

    def test_collection_with_items(self):
        """Test collection with items."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        collection = AnnotationCollection([anno1, anno2])

        self.assertEqual(len(collection), 2)
        items = list(collection)
        self.assertEqual(len(items), 2)

    def test_filter_by_type(self):
        """Test filtering by annotation type."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        anno3 = MockAnnotation(annotation_type="To Do")
        collection = AnnotationCollection([anno1, anno2, anno3])

        todos = collection.by_type("To Do")
        self.assertEqual(len(todos), 2)

    def test_filter_by_author(self):
        """Test filtering by author."""
        anno1 = MockAnnotation(author="John")
        anno2 = MockAnnotation(author="Jane")
        anno3 = MockAnnotation(author="John")
        collection = AnnotationCollection([anno1, anno2, anno3])

        john_notes = collection.by_author("John")
        self.assertEqual(len(john_notes), 2)

    def test_filter_by_date_since(self):
        """Test filtering by creation date (since)."""
        anno1 = MockAnnotation(date=self.date_1)
        anno2 = MockAnnotation(date=self.date_2)
        anno3 = MockAnnotation(date=self.date_3)
        collection = AnnotationCollection([anno1, anno2, anno3])

        cutoff = DateTime(2025, 1, 15)
        recent = collection.created_since(cutoff)
        self.assertEqual(len(recent), 2)

    def test_filter_by_date_until(self):
        """Test filtering by creation date (until)."""
        anno1 = MockAnnotation(date=self.date_1)
        anno2 = MockAnnotation(date=self.date_2)
        anno3 = MockAnnotation(date=self.date_3)
        collection = AnnotationCollection([anno1, anno2, anno3])

        cutoff = DateTime(2025, 1, 25)
        old = collection.created_until(cutoff)
        self.assertEqual(len(old), 2)

    def test_filter_by_content(self):
        """Test filtering by content contains."""
        anno1 = MockAnnotation(content="Check etymology")
        anno2 = MockAnnotation(content="Verify pronunciation")
        anno3 = MockAnnotation(content="Check definition")
        collection = AnnotationCollection([anno1, anno2, anno3])

        check_notes = collection.filter(content_contains="Check")
        self.assertEqual(len(check_notes), 2)

    def test_filter_chaining(self):
        """Test chaining multiple filters."""
        anno1 = MockAnnotation(annotation_type="To Do", author="John", date=self.date_1)
        anno2 = MockAnnotation(annotation_type="To Do", author="Jane", date=self.date_2)
        anno3 = MockAnnotation(annotation_type="Question", author="John", date=self.date_3)
        collection = AnnotationCollection([anno1, anno2, anno3])

        result = collection.by_type("To Do").by_author("John")
        self.assertEqual(len(result), 1)

    def test_filter_custom_where(self):
        """Test custom where filter."""
        anno1 = MockAnnotation(annotation_type="To Do", author="John")
        anno2 = MockAnnotation(annotation_type="Question", author="Jane")
        anno3 = MockAnnotation(annotation_type="To Do", author="Jane")
        collection = AnnotationCollection([anno1, anno2, anno3])

        result = collection.filter(where=lambda a: (a.annotation_type == "To Do" or a.author == "Jane"))
        self.assertEqual(len(result), 3)

    def test_scripture_filter(self):
        """Test scripture convenience filter."""
        anno1 = MockAnnotation(annotation_type="ScrScriptureNote")
        anno2 = MockAnnotation(annotation_type="To Do")
        anno3 = MockAnnotation(annotation_type="ScrComment")
        collection = AnnotationCollection([anno1, anno2, anno3])

        scripture = collection.scripture()
        self.assertEqual(len(scripture), 2)

    def test_translator_filter(self):
        """Test translator convenience filter."""
        anno1 = MockAnnotation(annotation_type="TranslatorNote")
        anno2 = MockAnnotation(annotation_type="ConsultantNote")
        anno3 = MockAnnotation(annotation_type="Translator Comment")
        collection = AnnotationCollection([anno1, anno2, anno3])

        translator = collection.translator()
        self.assertEqual(len(translator), 2)

    def test_consultant_filter(self):
        """Test consultant convenience filter."""
        anno1 = MockAnnotation(annotation_type="TranslatorNote")
        anno2 = MockAnnotation(annotation_type="ConsultantNote")
        anno3 = MockAnnotation(annotation_type="ConsultantReview")
        collection = AnnotationCollection([anno1, anno2, anno3])

        consultant = collection.consultant()
        self.assertEqual(len(consultant), 2)

    def test_todos_filter(self):
        """Test todos convenience filter."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Done")
        anno3 = MockAnnotation(annotation_type="To Do")
        collection = AnnotationCollection([anno1, anno2, anno3])

        todos = collection.todos()
        self.assertEqual(len(todos), 2)

    def test_questions_filter(self):
        """Test questions convenience filter."""
        anno1 = MockAnnotation(annotation_type="Question")
        anno2 = MockAnnotation(annotation_type="To Do")
        anno3 = MockAnnotation(annotation_type="Query")
        collection = AnnotationCollection([anno1, anno2, anno3])

        questions = collection.questions()
        self.assertEqual(len(questions), 2)

    def test_with_replies_filter(self):
        """Test filtering for annotations with replies."""
        anno1 = MockAnnotation(annotation_type="To Do", has_replies=True)
        anno2 = MockAnnotation(annotation_type="Question", has_replies=False)
        anno3 = MockAnnotation(annotation_type="To Do", has_replies=True)
        collection = AnnotationCollection([anno1, anno2, anno3])

        threaded = collection.with_replies()
        self.assertEqual(len(threaded), 2)

    def test_get_types(self):
        """Test getting unique types in collection."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        anno3 = MockAnnotation(annotation_type="To Do")
        collection = AnnotationCollection([anno1, anno2, anno3])

        types = collection.get_types()
        self.assertEqual(len(types), 2)
        self.assertIn("To Do", types)
        self.assertIn("Question", types)

    def test_get_authors(self):
        """Test getting unique authors in collection."""
        anno1 = MockAnnotation(author="John")
        anno2 = MockAnnotation(author="Jane")
        anno3 = MockAnnotation(author="John")
        collection = AnnotationCollection([anno1, anno2, anno3])

        authors = collection.get_authors()
        self.assertEqual(len(authors), 2)
        self.assertIn("John", authors)
        self.assertIn("Jane", authors)

    def test_get_types_empty(self):
        """Test get_types on empty collection."""
        collection = AnnotationCollection()
        types = collection.get_types()
        self.assertEqual(len(types), 0)

    def test_get_authors_empty(self):
        """Test get_authors on empty collection."""
        collection = AnnotationCollection()
        authors = collection.get_authors()
        self.assertEqual(len(authors), 0)

    def test_str_representation(self):
        """Test string representation showing type breakdown."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="To Do")
        anno3 = MockAnnotation(annotation_type="Question")
        collection = AnnotationCollection([anno1, anno2, anno3])

        str_repr = str(collection)
        self.assertIn("AnnotationCollection", str_repr)
        self.assertIn("3 total", str_repr)
        self.assertIn("To Do", str_repr)
        self.assertIn("Question", str_repr)

    def test_str_representation_empty(self):
        """Test string representation for empty collection."""
        collection = AnnotationCollection()
        str_repr = str(collection)
        self.assertIn("AnnotationCollection", str_repr)
        self.assertIn("0 total", str_repr)

    def test_repr(self):
        """Test brief representation."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        collection = AnnotationCollection([anno1, anno2])

        repr_str = repr(collection)
        self.assertIn("AnnotationCollection", repr_str)
        self.assertIn("2 items", repr_str)

    def test_iteration(self):
        """Test iterating over collection."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        collection = AnnotationCollection([anno1, anno2])

        count = 0
        for anno in collection:
            self.assertIsNotNone(anno)
            count += 1

        self.assertEqual(count, 2)

    def test_indexing(self):
        """Test indexing collection."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        collection = AnnotationCollection([anno1, anno2])

        self.assertEqual(collection[0], anno1)
        self.assertEqual(collection[1], anno2)

    def test_slicing(self):
        """Test slicing collection."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        anno3 = MockAnnotation(annotation_type="To Do")
        collection = AnnotationCollection([anno1, anno2, anno3])

        sliced = collection[0:2]
        self.assertIsInstance(sliced, AnnotationCollection)
        self.assertEqual(len(sliced), 2)

    def test_multiple_filters_and(self):
        """Test multiple criteria in single filter (AND logic)."""
        anno1 = MockAnnotation(annotation_type="To Do", author="John", content="Check this")
        anno2 = MockAnnotation(annotation_type="To Do", author="Jane", content="Check that")
        anno3 = MockAnnotation(annotation_type="Question", author="John", content="Why?")
        collection = AnnotationCollection([anno1, anno2, anno3])

        # Should match only anno1: To Do AND John AND has "Check"
        result = collection.filter(annotation_type="To Do", author="John", content_contains="Check")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], anno1)

    def test_filter_returns_new_collection(self):
        """Test that filters return new collections (don't modify original)."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        original = AnnotationCollection([anno1, anno2])

        filtered = original.by_type("To Do")

        self.assertEqual(len(original), 2)
        self.assertEqual(len(filtered), 1)

    def test_empty_filter_result(self):
        """Test filtering that results in empty collection."""
        anno1 = MockAnnotation(annotation_type="To Do")
        anno2 = MockAnnotation(annotation_type="Question")
        collection = AnnotationCollection([anno1, anno2])

        no_match = collection.by_type("Nonexistent")
        self.assertEqual(len(no_match), 0)
        self.assertIsInstance(no_match, AnnotationCollection)

    def test_type_breakdown_display(self):
        """Test that type breakdown is accurate in string display."""
        # Create collection with known type distribution
        annos = [
            MockAnnotation(annotation_type="To Do"),
            MockAnnotation(annotation_type="To Do"),
            MockAnnotation(annotation_type="To Do"),
            MockAnnotation(annotation_type="Question"),
            MockAnnotation(annotation_type="Question"),
        ]
        collection = AnnotationCollection(annos)

        str_repr = str(collection)
        # Should show 60% for To Do (3/5) and 40% for Question (2/5)
        self.assertIn("To Do: 3 (60%)", str_repr)
        self.assertIn("Question: 2 (40%)", str_repr)


if __name__ == "__main__":
    unittest.main()
