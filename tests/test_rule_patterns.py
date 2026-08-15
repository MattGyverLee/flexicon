#
#   test_rule_patterns.py
#
#   Unit tests for the pattern-element dataclasses (Seg, NC, Boundary)
#   used by PhonologicalRuleOperations.WireRule. These are pure-Python
#   dataclasses that do not require SIL.LCModel to be loaded — they're
#   inert descriptors that the composer translates into LCM
#   simple-context objects.
#
#   Platform: Python (standard library only — no SIL.LCModel dep)
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from dataclasses import FrozenInstanceError

import pytest

from flexicon.code.Shared.rule_patterns import Seg, NC, Boundary


class TestSegDataclass:
    """Coverage for the Seg pattern element."""

    def test_seg_frozen_dataclass(self):
        """Seg('p') instantiates; attempting to mutate raises FrozenInstanceError."""
        seg = Seg("p")
        assert seg.phoneme == "p"
        with pytest.raises(FrozenInstanceError):
            seg.phoneme = "q"

    def test_seg_no_plus_minus_fields(self):
        """Seg has no plus/minus fields — alpha-feature constraints are NC-only."""
        with pytest.raises(TypeError):
            Seg("p", plus=[1])


class TestNCDataclass:
    """Coverage for the NC (natural-class) pattern element."""

    def test_nc_default_empty_tuples(self):
        """NC defaults plus/minus to empty TUPLES (immutable), not lists."""
        nc = NC("nc_v")
        assert nc.plus == ()
        assert nc.minus == ()
        # Explicitly verify they're tuples, not lists. Frozen dataclasses
        # require hashable defaults, and tuples are correct here.
        assert isinstance(nc.plus, tuple)
        assert isinstance(nc.minus, tuple)

    def test_nc_accepts_constraint_tuples(self):
        """NC.plus round-trips a tuple of stand-in constraint objects."""
        c1 = object()
        c2 = object()
        nc = NC("nc_v", plus=(c1, c2))
        assert nc.plus == (c1, c2)
        # Identity matters for alpha-variable sharing — verify same objects.
        assert nc.plus[0] is c1
        assert nc.plus[1] is c2


class TestBoundaryDataclass:
    """Coverage for the Boundary pattern element."""

    def test_boundary_default_marker_hash(self):
        """Boundary() defaults marker to '#' (word boundary)."""
        b = Boundary()
        assert b.marker == "#"

    def test_boundary_explicit_marker(self):
        """Boundary('+') stores the explicit marker."""
        b = Boundary("+")
        assert b.marker == "+"


class TestDataclassHashability:
    """Frozen dataclasses must be hashable so they can be used in sets/dicts."""

    def test_dataclasses_hashable(self):
        """Seg, NC, and Boundary are all hashable (frozen=True implies __hash__)."""
        # Seg
        assert hash(Seg("p")) == hash(Seg("p"))
        # NC with default empty tuples
        assert hash(NC("nc_v")) == hash(NC("nc_v"))
        # Boundary
        assert hash(Boundary()) == hash(Boundary("#"))


class TestTopLevelImports:
    """The dataclasses must be exported at the top level of the flexicon package."""

    def test_top_level_imports_work(self):
        """The inner flexicon package's __init__.py exposes Seg, NC, Boundary.

        Notes:
            The project has a root-level ``__init__.py`` (legacy
            ``__version__ = "2.4.0-dev"`` stub) that pytest treats as the
            package ``flexicon`` during test collection — masking the real
            package at ``flexicon/__init__.py``. We verify the
            public-API export by parsing the real package's __init__.py
            source so we don't depend on pytest's import resolution.
        """
        import ast
        import os

        # Locate the REAL inner package __init__.py.
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(here)
        inner_init = os.path.join(repo_root, "flexicon", "__init__.py")
        assert os.path.exists(inner_init), (
            f"Expected real flexicon package at {inner_init}; layout changed"
        )

        with open(inner_init, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        # Collect all names imported at module level (these are the public
        # API symbols available via `from flexicon import X`).
        top_level_names = set()
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    top_level_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top_level_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        top_level_names.add(target.id)

        for name in ("Seg", "NC", "Boundary"):
            assert name in top_level_names, (
                f"flexicon/__init__.py does not export {name!r} at module "
                f"top level (so `from flexicon import {name}` would fail)"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
