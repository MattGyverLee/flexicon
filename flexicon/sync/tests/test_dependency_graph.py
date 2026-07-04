"""
Unit tests for Dependency Graph - Phase 3.1

Tests graph construction, cycle detection, and topological sorting.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import unittest
from unittest.mock import Mock

from flexlibs2.sync.dependency_graph import DependencyGraph, DependencyType, DependencyNode, CircularDependencyError


class TestDependencyNode(unittest.TestCase):
    """Test DependencyNode dataclass."""

    def test_create_node(self):
        """Test creating a dependency node."""
        node = DependencyNode(guid="test-guid", object_type="LexEntry")

        self.assertEqual(node.guid, "test-guid")
        self.assertEqual(node.object_type, "LexEntry")
        self.assertIsNone(node.obj)
        self.assertEqual(len(node.dependencies), 0)
        self.assertEqual(len(node.dependents), 0)
        self.assertFalse(node.visited)
        self.assertFalse(node.in_progress)

    def test_node_with_object(self):
        """Test node with actual object."""
        mock_obj = Mock()
        node = DependencyNode(guid="test-guid", object_type="LexEntry", obj=mock_obj)

        self.assertEqual(node.obj, mock_obj)


class TestDependencyGraphBasic(unittest.TestCase):
    """Test basic dependency graph operations."""

    def test_create_empty_graph(self):
        """Test creating empty graph."""
        graph = DependencyGraph()

        self.assertEqual(len(graph), 0)
        self.assertEqual(len(graph.nodes), 0)

    def test_add_single_object(self):
        """Test adding single object."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")

        self.assertEqual(len(graph), 1)
        self.assertIn("entry-1", graph)
        self.assertEqual(graph.nodes["entry-1"].object_type, "LexEntry")

    def test_add_multiple_objects(self):
        """Test adding multiple objects."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("pos-1", "PartOfSpeech")

        self.assertEqual(len(graph), 3)

    def test_add_object_with_mock(self):
        """Test adding object with actual FLEx mock."""
        mock_obj = Mock()
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry", mock_obj)

        self.assertEqual(graph.nodes["entry-1"].obj, mock_obj)

    def test_update_existing_object(self):
        """Test updating existing object in graph."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")

        # Update with object
        mock_obj = Mock()
        graph.add_object("entry-1", "LexEntry", mock_obj)

        self.assertEqual(len(graph), 1)  # Still just one object
        self.assertEqual(graph.nodes["entry-1"].obj, mock_obj)


class TestDependencyGraphDependencies(unittest.TestCase):
    """Test dependency relationships."""

    def test_add_simple_dependency(self):
        """Test adding simple dependency."""
        graph = DependencyGraph()
        graph.add_object("sense-1", "LexSense")
        graph.add_object("entry-1", "LexEntry")

        # Sense depends on entry (entry must be imported first)
        graph.add_dependency("sense-1", "entry-1", DependencyType.OWNERSHIP)

        # Check forward dependency
        self.assertIn("entry-1", graph.nodes["sense-1"].dependencies)
        self.assertEqual(graph.nodes["sense-1"].dependency_types["entry-1"], DependencyType.OWNERSHIP)

        # Check reverse dependency
        self.assertIn("sense-1", graph.nodes["entry-1"].dependents)

    def test_add_multiple_dependencies(self):
        """Test adding multiple dependencies."""
        graph = DependencyGraph()
        graph.add_object("sense-1", "LexSense")
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("pos-1", "PartOfSpeech")
        graph.add_object("domain-1", "CmSemanticDomain")

        # Sense depends on entry, POS, and domain
        graph.add_dependency("sense-1", "entry-1", DependencyType.OWNERSHIP)
        graph.add_dependency("sense-1", "pos-1", DependencyType.REFERENCE)
        graph.add_dependency("sense-1", "domain-1", DependencyType.REFERENCE)

        self.assertEqual(len(graph.nodes["sense-1"].dependencies), 3)

    def test_remove_dependency(self):
        """Test removing dependency."""
        graph = DependencyGraph()
        graph.add_object("sense-1", "LexSense")
        graph.add_object("entry-1", "LexEntry")

        graph.add_dependency("sense-1", "entry-1")
        self.assertIn("entry-1", graph.nodes["sense-1"].dependencies)

        graph.remove_dependency("sense-1", "entry-1")
        self.assertNotIn("entry-1", graph.nodes["sense-1"].dependencies)
        self.assertNotIn("sense-1", graph.nodes["entry-1"].dependents)


class TestDependencyGraphTraversal(unittest.TestCase):
    """Test graph traversal operations."""

    def test_get_roots(self):
        """Test getting root nodes (no dependencies)."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")

        graph.add_dependency("sense-1", "entry-1")

        roots = graph.get_roots()
        self.assertEqual(len(roots), 1)
        self.assertIn("entry-1", roots)

    def test_get_leaves(self):
        """Test getting leaf nodes (no dependents)."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")

        graph.add_dependency("sense-1", "entry-1")

        leaves = graph.get_leaves()
        self.assertEqual(len(leaves), 1)
        self.assertIn("sense-1", leaves)

    def test_get_dependencies_non_recursive(self):
        """Test getting direct dependencies."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("example-1", "LexExampleSentence")

        graph.add_dependency("sense-1", "entry-1")
        graph.add_dependency("example-1", "sense-1")

        deps = graph.get_dependencies("sense-1", recursive=False)
        self.assertEqual(len(deps), 1)
        self.assertIn("entry-1", deps)

    def test_get_dependencies_recursive(self):
        """Test getting transitive dependencies."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("example-1", "LexExampleSentence")

        graph.add_dependency("sense-1", "entry-1")
        graph.add_dependency("example-1", "sense-1")

        # Example transitively depends on entry through sense
        deps = graph.get_dependencies("example-1", recursive=True)
        self.assertEqual(len(deps), 2)
        self.assertIn("sense-1", deps)
        self.assertIn("entry-1", deps)

    def test_get_dependents_recursive(self):
        """Test getting transitive dependents."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("example-1", "LexExampleSentence")

        graph.add_dependency("sense-1", "entry-1")
        graph.add_dependency("example-1", "sense-1")

        # Entry has sense and example as transitive dependents
        dependents = graph.get_dependents("entry-1", recursive=True)
        self.assertEqual(len(dependents), 2)
        self.assertIn("sense-1", dependents)
        self.assertIn("example-1", dependents)


class TestTopologicalSort(unittest.TestCase):
    """Test topological sorting."""

    def test_simple_linear_order(self):
        """Test simple linear dependency chain."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("example-1", "LexExampleSentence")

        # example depends on sense, sense depends on entry
        graph.add_dependency("example-1", "sense-1")
        graph.add_dependency("sense-1", "entry-1")

        order = graph.get_import_order()

        # Should be entry, then sense, then example
        guids = [guid for guid, _ in order]
        entry_idx = guids.index("entry-1")
        sense_idx = guids.index("sense-1")
        example_idx = guids.index("example-1")

        self.assertLess(entry_idx, sense_idx)
        self.assertLess(sense_idx, example_idx)

    def test_complex_hierarchy(self):
        """Test complex hierarchy import order."""
        graph = DependencyGraph()

        # Entry with 2 senses, each with examples
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("sense-2", "LexSense")
        graph.add_object("example-1", "LexExampleSentence")
        graph.add_object("example-2", "LexExampleSentence")
        graph.add_object("pos-1", "PartOfSpeech")

        # Dependencies
        graph.add_dependency("sense-1", "entry-1", DependencyType.OWNERSHIP)
        graph.add_dependency("sense-2", "entry-1", DependencyType.OWNERSHIP)
        graph.add_dependency("example-1", "sense-1", DependencyType.OWNERSHIP)
        graph.add_dependency("example-2", "sense-2", DependencyType.OWNERSHIP)
        graph.add_dependency("sense-1", "pos-1", DependencyType.REFERENCE)
        graph.add_dependency("sense-2", "pos-1", DependencyType.REFERENCE)

        order = graph.get_import_order()
        guids = [guid for guid, _ in order]

        # Entry and POS must come before senses
        entry_idx = guids.index("entry-1")
        pos_idx = guids.index("pos-1")
        sense1_idx = guids.index("sense-1")
        sense2_idx = guids.index("sense-2")

        self.assertLess(entry_idx, sense1_idx)
        self.assertLess(entry_idx, sense2_idx)
        self.assertLess(pos_idx, sense1_idx)
        self.assertLess(pos_idx, sense2_idx)

        # Senses must come before their examples
        example1_idx = guids.index("example-1")
        example2_idx = guids.index("example-2")

        self.assertLess(sense1_idx, example1_idx)
        self.assertLess(sense2_idx, example2_idx)

    def test_order_caching(self):
        """Test that import order is cached."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_dependency("sense-1", "entry-1")

        order1 = graph.get_import_order()
        order2 = graph.get_import_order()

        self.assertIs(order1, order2)  # Same object (cached)

    def test_cache_invalidation(self):
        """Test that cache is invalidated when graph changes."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")

        order1 = graph.get_import_order()

        # Add new dependency
        graph.add_dependency("sense-1", "entry-1")

        order2 = graph.get_import_order()

        self.assertIsNot(order1, order2)  # Different objects


class TestCycleDetection(unittest.TestCase):
    """Test circular dependency detection."""

    def test_no_cycle(self):
        """Test graph with no cycles."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_dependency("sense-1", "entry-1")

        cycles = graph.detect_cycles()
        self.assertEqual(len(cycles), 0)

    def test_simple_cycle(self):
        """Test detection of simple cycle."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("entry-2", "LexEntry")

        # Create cycle: entry-1 → entry-2 → entry-1
        graph.add_dependency("entry-1", "entry-2")
        graph.add_dependency("entry-2", "entry-1")

        cycles = graph.detect_cycles()
        self.assertGreater(len(cycles), 0)

        # Check cycle contains both entries
        cycle = cycles[0]
        self.assertIn("entry-1", cycle)
        self.assertIn("entry-2", cycle)

    def test_self_cycle(self):
        """Test detection of self-referencing cycle."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_dependency("entry-1", "entry-1")

        cycles = graph.detect_cycles()
        self.assertGreater(len(cycles), 0)

    def test_complex_cycle(self):
        """Test detection of cycle in complex graph."""
        graph = DependencyGraph()
        graph.add_object("a", "TypeA")
        graph.add_object("b", "TypeB")
        graph.add_object("c", "TypeC")
        graph.add_object("d", "TypeD")

        # Create cycle: a → b → c → d → b
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "d")
        graph.add_dependency("d", "b")  # Creates cycle

        cycles = graph.detect_cycles()
        self.assertGreater(len(cycles), 0)

    def test_get_import_order_raises_on_cycle(self):
        """Test that get_import_order raises error on cycle."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("entry-2", "LexEntry")

        graph.add_dependency("entry-1", "entry-2")
        graph.add_dependency("entry-2", "entry-1")

        with self.assertRaises(CircularDependencyError) as ctx:
            graph.get_import_order()

        self.assertIn("entry-1", str(ctx.exception))
        self.assertIn("entry-2", str(ctx.exception))


class TestSubgraph(unittest.TestCase):
    """Test subgraph extraction."""

    def test_extract_simple_subgraph(self):
        """Test extracting subgraph."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_object("example-1", "LexExampleSentence")
        graph.add_object("entry-2", "LexEntry")

        graph.add_dependency("sense-1", "entry-1")
        graph.add_dependency("example-1", "sense-1")

        # Extract subgraph for example-1
        subgraph = graph.get_subgraph(["example-1"])

        # Should include example, sense, and entry (transitive dependencies)
        self.assertEqual(len(subgraph), 3)
        self.assertIn("example-1", subgraph)
        self.assertIn("sense-1", subgraph)
        self.assertIn("entry-1", subgraph)
        self.assertNotIn("entry-2", subgraph)

    def test_subgraph_preserves_dependencies(self):
        """Test that subgraph preserves dependency relationships."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("sense-1", "LexSense")
        graph.add_dependency("sense-1", "entry-1", DependencyType.OWNERSHIP)

        subgraph = graph.get_subgraph(["sense-1"])

        # Check dependency is preserved
        self.assertIn("entry-1", subgraph.nodes["sense-1"].dependencies)
        self.assertEqual(subgraph.nodes["sense-1"].dependency_types["entry-1"], DependencyType.OWNERSHIP)


class TestGraphSummary(unittest.TestCase):
    """Test graph summary generation."""

    def test_summary_empty_graph(self):
        """Test summary of empty graph."""
        graph = DependencyGraph()
        summary = graph.summary()

        self.assertIn("Total objects: 0", summary)

    def test_summary_with_objects(self):
        """Test summary with objects."""
        graph = DependencyGraph()
        graph.add_object("entry-1", "LexEntry")
        graph.add_object("entry-2", "LexEntry")
        graph.add_object("sense-1", "LexSense")

        graph.add_dependency("sense-1", "entry-1", DependencyType.OWNERSHIP)

        summary = graph.summary()

        self.assertIn("Total objects: 3", summary)
        self.assertIn("LexEntry: 2", summary)
        self.assertIn("LexSense: 1", summary)
        self.assertIn("ownership", summary.lower())


if __name__ == "__main__":
    unittest.main()
