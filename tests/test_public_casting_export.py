#
#   test_public_casting_export.py
#
#   Unit tests locking the PUBLIC export of `cast_to_concrete` (issue #271).
#
#   `cast_to_concrete` is the remedy for the whole
#   `'ICmObject' object has no attribute 'X'` failure class. It shipped in
#   the wheel for several releases while being documented as internal-only,
#   so downstream consumers reached into the private module path or guessed
#   at public names that never existed (`from flexicon import
#   CastingOperations`). These tests lock:
#
#     1. The documented public import path works.
#     2. All reachable paths are the SAME function object (identity matters
#        for consumers that compare or monkeypatch it).
#     3. The TOTALITY guarantee -- an unrecognised ClassName, a missing
#        ClassName, and a failing cast each return the object UNCHANGED.
#        This is the property that makes it preferable to the hand-rolled
#        `ILexEntry(x)` workaround, which throws on a legitimately-
#        `ILexSense` element of a polymorphic collection.
#
#   Platform: Python (standard library only -- no SIL.LCModel dep). The
#             import surface and the totality paths are all reachable
#             without FieldWorks, because lcm_casting defers every
#             SIL.LCModel import into a lazy `_ensure_interfaces()` call.
#
#   Copyright 2026
#

import flexicon
import flexicon.code
from flexicon import cast_to_concrete
from flexicon.code import lcm_casting


class TestPublicImportPath:
    """The documented public surface for issue #271."""

    def test_top_level_import_works(self):
        """`from flexicon import cast_to_concrete` -- the documented path."""
        assert callable(cast_to_concrete)

    def test_top_level_attribute_present(self):
        """It is reachable as an attribute of the package, too."""
        assert flexicon.cast_to_concrete is cast_to_concrete

    def test_same_object_as_private_module_path(self):
        """Public export and the long-standing private path are IDENTICAL.

        Consumers migrating off `flexicon.code.lcm_casting.cast_to_concrete`
        must not end up with two distinct functions.
        """
        assert cast_to_concrete is lcm_casting.cast_to_concrete

    def test_same_object_via_code_subpackage(self):
        """`flexicon.code.cast_to_concrete` is the same object as well."""
        assert flexicon.code.cast_to_concrete is lcm_casting.cast_to_concrete

    def test_listed_in_code_subpackage_all(self):
        """It is advertised in `flexicon.code.__all__`."""
        assert "cast_to_concrete" in flexicon.code.__all__

    def test_casting_operations_still_does_not_exist(self):
        """The name downstream guessed at is NOT silently introduced.

        FlexToolsMCP hints named `CastingOperations.cast_to_concrete`.
        #271 fixes that by exporting the real symbol, deliberately NOT by
        inventing the guessed one.
        """
        assert not hasattr(flexicon, "CastingOperations")

    def test_lcm_object_wrapper_not_exported(self):
        """`LCMObjectWrapper` is deliberately left unexported by #271."""
        assert not hasattr(flexicon, "LCMObjectWrapper")


class TestTotalityGuarantee:
    """`cast_to_concrete` never raises for input it cannot cast."""

    def test_unrecognised_class_name_returns_object_unchanged(self):
        """An unknown ClassName yields the SAME object, not an error."""

        class Unknown:
            ClassName = "NoSuchLcmClassZZZ"

        obj = Unknown()
        assert cast_to_concrete(obj) is obj

    def test_missing_class_name_returns_object_unchanged(self):
        """An object with no ClassName at all is returned as-is."""

        class NoClassName:
            pass

        obj = NoClassName()
        assert cast_to_concrete(obj) is obj

    def test_failing_cast_returns_object_unchanged(self, monkeypatch):
        """A cast that raises inside the CLR degrades to the original.

        Simulated by seeding the interface cache with a "constructor" that
        throws, which is how a wrong-type pythonnet cast presents.
        """

        def exploding_interface(_obj):
            raise TypeError("value cannot be converted")

        class Bogus:
            ClassName = "TestBogusClass271"

        monkeypatch.setattr(lcm_casting, "_interfaces_loaded", True)
        monkeypatch.setitem(
            lcm_casting._interface_cache, "TestBogusClass271", exploding_interface
        )

        obj = Bogus()
        assert cast_to_concrete(obj) is obj

    def test_none_is_returned_unchanged(self):
        """None has no ClassName, so it round-trips rather than raising."""
        assert cast_to_concrete(None) is None


class TestImportSafety:
    """Exporting it must not make `import flexicon` need FieldWorks."""

    def test_lcm_casting_has_no_module_scope_sil_import(self):
        """SIL.LCModel imports stay inside the lazy `_ensure_interfaces()`.

        Locks the property that justifies the EAGER top-level export in
        `flexicon/__init__.py`: were an `import SIL.LCModel` to move to
        module scope here, importing flexicon would break on machines with
        no FieldWorks installed.
        """
        import ast
        import inspect

        tree = ast.parse(inspect.getsource(lcm_casting))
        module_scope_imports = [
            node
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        offenders = []
        for node in module_scope_imports:
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("SIL"):
                    offenders.append(node.module)
            else:
                for alias in node.names:
                    if alias.name.startswith("SIL"):
                        offenders.append(alias.name)
        assert offenders == [], f"module-scope SIL imports: {offenders}"
