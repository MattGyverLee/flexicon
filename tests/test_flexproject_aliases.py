#
#   test_flexproject_aliases.py
#
#   Tests for the operation-namespace naming aliases (issue #200).
#
#   The alias table and generator live in the SIL-free
#   flexicon.code._op_aliases module, so the core behavior is verified here
#   without a FieldWorks install. A final live-skip test confirms the aliases
#   are actually attached to the real FLExProject when SIL is available.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys
import warnings

import pytest

from flexlibs2.code._op_aliases import (
    OP_NAMESPACE_ALIASES,
    install_op_namespace_aliases,
    make_op_namespace_alias,
)


# ---------------------------------------------------------------------------
# Alias table content
# ---------------------------------------------------------------------------
class TestAliasTable:
    def test_logged_singular_guesses_are_mapped(self):
        """The two AttributeErrors quoted in issue #200 must be covered."""
        assert OP_NAMESPACE_ALIASES["InflectionFeature"] == "InflectionFeatures"
        assert OP_NAMESPACE_ALIASES["MorphRule"] == "MorphRules"

    def test_no_alias_is_its_own_canonical(self):
        """An alias must never point at itself (would be a no-op / recursion)."""
        for alias, canonical in OP_NAMESPACE_ALIASES.items():
            assert alias != canonical, f"{alias} aliases itself"

    def test_canonical_targets_are_not_also_aliases(self):
        """Canonical targets must be terminal (no alias-to-alias chains)."""
        for alias, canonical in OP_NAMESPACE_ALIASES.items():
            assert canonical not in OP_NAMESPACE_ALIASES, (
                f"{alias} -> {canonical}, but {canonical} is itself an alias "
                "(chains break single-hop forwarding)"
            )


# ---------------------------------------------------------------------------
# Generator behavior against a fake class (no SIL required)
# ---------------------------------------------------------------------------
class _FakeProject:
    """Stand-in with a couple of canonical plural/singular accessors."""

    def __init__(self):
        self._morph_rules = "MORPH_RULES_OPS"
        self._inflection_features = "INFL_FEAT_OPS"
        self._lex_entry = "LEX_ENTRY_OPS"

    @property
    def MorphRules(self):
        return self._morph_rules

    @property
    def InflectionFeatures(self):
        return self._inflection_features

    @property
    def LexEntry(self):
        return self._lex_entry


class TestAliasGeneration:
    def _install(self, aliases):
        cls = type("FakeProject", (_FakeProject,), {})
        installed = install_op_namespace_aliases(cls, aliases)
        return cls, installed

    def test_singular_alias_forwards_to_canonical(self):
        cls, _ = self._install({"MorphRule": "MorphRules"})
        obj = cls()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert obj.MorphRule == "MORPH_RULES_OPS"
            assert obj.MorphRule is obj.MorphRules

    def test_plural_alias_forwards_to_singular_canonical(self):
        cls, _ = self._install({"LexEntries": "LexEntry"})
        obj = cls()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert obj.LexEntries == "LEX_ENTRY_OPS"

    def test_alias_emits_deprecation_warning_naming_canonical(self):
        cls, _ = self._install({"InflectionFeature": "InflectionFeatures"})
        obj = cls()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _ = obj.InflectionFeature
        assert len(caught) == 1
        assert issubclass(caught[0].category, DeprecationWarning)
        msg = str(caught[0].message)
        assert "InflectionFeature" in msg
        assert "InflectionFeatures" in msg  # names the canonical accessor

    def test_alias_appears_in_dir(self):
        """Generated aliases are real descriptors -> visible for autocomplete."""
        cls, _ = self._install({"MorphRule": "MorphRules"})
        assert "MorphRule" in dir(cls)

    def test_install_never_clobbers_real_accessor(self):
        """A canonical accessor must not be replaced by a generated alias."""
        # MorphRules is a real property; if it were (wrongly) an alias key,
        # install must leave the real one intact.
        cls, installed = self._install(
            {"MorphRules": "InflectionFeatures", "MorphRule": "MorphRules"}
        )
        obj = cls()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Real MorphRules still returns its own ops, not the alias target.
            assert obj.MorphRules == "MORPH_RULES_OPS"
        assert "MorphRules" not in installed  # skipped (already real)
        assert "MorphRule" in installed

    def test_install_raises_on_unknown_canonical(self):
        cls = type("FakeProject", (_FakeProject,), {})
        with pytest.raises(AttributeError):
            install_op_namespace_aliases(cls, {"Bogus": "DoesNotExist"})

    def test_make_alias_returns_property(self):
        prop = make_op_namespace_alias("MorphRule", "MorphRules")
        assert isinstance(prop, property)
        assert "MorphRules" in (prop.fget.__doc__ or "")


# ---------------------------------------------------------------------------
# Live check: the real FLExProject actually carries the aliases (skip w/o SIL)
# ---------------------------------------------------------------------------
class TestLiveFLExProjectAliases:
    def _flexproject(self):
        if "SIL.LCModel" not in sys.modules:
            try:
                from flexlibs2.code.FLExProject import FLExProject
            except Exception:
                pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
        from flexlibs2.code.FLExProject import FLExProject

        return FLExProject

    def test_every_alias_is_installed_and_canonical_exists(self):
        FLExProject = self._flexproject()
        for alias, canonical in OP_NAMESPACE_ALIASES.items():
            assert hasattr(FLExProject, canonical), (
                f"canonical accessor {canonical} missing on FLExProject"
            )
            assert hasattr(FLExProject, alias), (
                f"alias {alias} not installed on FLExProject"
            )

    def test_logged_singular_aliases_present(self):
        FLExProject = self._flexproject()
        assert hasattr(FLExProject, "InflectionFeature")
        assert hasattr(FLExProject, "MorphRule")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
