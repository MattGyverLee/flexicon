#
#   test_276_pos_getparent.py
#
#   Class: TestPOSGetParent / TestPOSGetParentGuardShape
#          Offline unit coverage for issue #276, task T2: the
#          POSOperations.GetParent backfill.
#
#          #276 ruled that "grammatical category" at list level IS the
#          Part of Speech list (IPartOfSpeech in
#          lp.PartsOfSpeechOA.PossibilitiesOS), so project.GramCat becomes
#          a deprecated alias onto POSOperations. GramCatOperations owned a
#          GetParent that POSOperations lacked; the capability is relocated
#          here before the TypesOC implementation is stripped.
#
#          The relocated implementation is deliberately NOT a copy of
#          GramCatOperations.GetParent, whose owner guard reads
#          `except (AttributeError, System.InvalidCastException)` while
#          that module never imports `System` -- the except clause would
#          raise NameError if it were ever reached. POSOperations.GetParent
#          discriminates on ClassName instead, matching __ResolveObject's
#          ClassName-gated shape (contract C2), so no cast failure is ever
#          relied upon for control flow. TestPOSGetParentGuardShape pins
#          that.
#
#          These tests use plain Python stand-ins and patch the module's
#          IPartOfSpeech with a pass-through recorder, so the real
#          pythonnet cast is not attempted. The live half of the
#          contract -- GetParent round-tripping against AddSubcategory on
#          a real project -- is task T11, not this file.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import os
import sys
from unittest.mock import Mock

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tests.operations import mock_flex_project  # noqa: F401


# ---------------------------------------------------------------------------
# Minimal LCM stand-ins -- no FieldWorks required
# ---------------------------------------------------------------------------


class _FakePos:
    """Stand-in for IPartOfSpeech reached as ICmObject."""

    ClassName = "PartOfSpeech"

    def __init__(self, hvo=1, owner=None, name="POS"):
        self.Hvo = hvo
        self.Owner = owner
        self.Name = name
        self.SubPossibilitiesOS = []


class _FakePossibilityList:
    """
    Stand-in for the ICmPossibilityList at lp.PartsOfSpeechOA -- the owner
    of every TOP-LEVEL POS. It is not a possibility, so it is not a parent
    category, and GetParent must report None for anything it owns.
    """

    ClassName = "CmPossibilityList"

    def __init__(self, hvo=99):
        self.Hvo = hvo
        self.Owner = None
        self.PossibilitiesOS = []


def _attach(parent, child):
    """Wire a subcategory to its parent the way the LCM does."""
    parent.SubPossibilitiesOS.append(child)
    child.Owner = parent
    return child


@pytest.fixture
def cast_recorder(monkeypatch):
    """
    Replace POSOperations' module-level IPartOfSpeech with a pass-through
    recorder. The real symbol is a pythonnet interface whose call is a CLR
    cast; it rejects plain Python objects. Patching it keeps the genuine
    __ResolveObject / GetParent control flow intact while letting the test
    assert that the owner really was routed through the cast.
    """
    import flexicon.code.Grammar.POSOperations as pos_module

    recorder = Mock(side_effect=lambda obj: obj)
    monkeypatch.setattr(pos_module, "IPartOfSpeech", recorder)
    return recorder


@pytest.fixture
def pos_ops(mock_flex_project, cast_recorder):
    """POSOperations bound to a mock project, with the CLR cast neutered."""
    from flexicon.code.Grammar.POSOperations import POSOperations

    return POSOperations(mock_flex_project)


class TestPOSGetParent:
    """Behaviour of the T2 backfill POSOperations.GetParent."""

    def test_subcategory_returns_its_parent(self, pos_ops):
        """A POS owned by another POS reports that POS as its parent."""
        noun = _FakePos(hvo=10, owner=_FakePossibilityList(), name="Noun")
        proper = _attach(noun, _FakePos(hvo=11, name="Proper Noun"))

        assert pos_ops.GetParent(proper) is noun

    def test_nested_subcategory_returns_immediate_parent(self, pos_ops):
        """GetParent climbs exactly one level, not to the root."""
        noun = _FakePos(hvo=10, owner=_FakePossibilityList(), name="Noun")
        proper = _attach(noun, _FakePos(hvo=11, name="Proper Noun"))
        place = _attach(proper, _FakePos(hvo=12, name="Place Name"))

        assert pos_ops.GetParent(place) is proper
        assert pos_ops.GetParent(pos_ops.GetParent(place)) is noun

    def test_top_level_pos_returns_none(self, pos_ops):
        """
        A top-level POS is owned by the PartsOfSpeechOA possibility LIST,
        which is not a possibility -- so it has no parent category.
        """
        pos_list = _FakePossibilityList()
        noun = _FakePos(hvo=10, owner=pos_list, name="Noun")
        pos_list.PossibilitiesOS.append(noun)

        assert pos_ops.GetParent(noun) is None

    def test_pos_with_null_owner_returns_none(self, pos_ops):
        """A detached POS (no Owner at all) reports no parent, not a crash."""
        orphan = _FakePos(hvo=10, owner=None, name="Detached")

        assert pos_ops.GetParent(orphan) is None

    def test_owner_without_classname_returns_none(self, pos_ops):
        """
        The guard is total: an owner exposing no ClassName is reported as
        'no parent category' rather than raising. GramCatOperations'
        version reached for System.InvalidCastException here, in a module
        that never imports System.
        """

        class _Opaque:
            pass

        orphan = _FakePos(hvo=10, owner=_Opaque(), name="Odd")

        assert pos_ops.GetParent(orphan) is None

    def test_parent_is_routed_through_the_ipartofspeech_cast(
        self, pos_ops, cast_recorder
    ):
        """
        `.Owner` yields a bare ICmObject; the returned parent must be cast
        so subtype-only members (Abbreviation, SubPossibilitiesOS, ...) are
        reachable on it.
        """
        noun = _FakePos(hvo=10, owner=_FakePossibilityList(), name="Noun")
        proper = _attach(noun, _FakePos(hvo=11, name="Proper Noun"))

        result = pos_ops.GetParent(proper)

        assert result is noun
        assert noun in [call.args[0] for call in cast_recorder.call_args_list]

    def test_hvo_input_is_resolved_before_the_owner_lookup(
        self, pos_ops, mock_flex_project
    ):
        """GetParent accepts an HVO, matching every sibling POS method."""
        noun = _FakePos(hvo=10, owner=_FakePossibilityList(), name="Noun")
        proper = _attach(noun, _FakePos(hvo=11, name="Proper Noun"))
        mock_flex_project.Object = Mock(return_value=proper)

        result = pos_ops.GetParent(11)

        mock_flex_project.Object.assert_called_once_with(11)
        assert result is noun

    def test_none_input_raises_null_parameter_error(self, pos_ops):
        """None is rejected by _ValidateParam, per house style."""
        from flexicon.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            pos_ops.GetParent(None)

    def test_getparent_inverts_getsubcategories(self, pos_ops):
        """
        The stated contract: for any subcategory s of p returned by
        GetSubcategories(p), GetParent(s) is p.
        """
        noun = _FakePos(hvo=10, owner=_FakePossibilityList(), name="Noun")
        for hvo, name in ((11, "Proper Noun"), (12, "Common Noun")):
            _attach(noun, _FakePos(hvo=hvo, name=name))

        subcats = list(pos_ops.GetSubcategories(noun, recursive=False))

        assert len(subcats) == 2
        for subcat in subcats:
            assert pos_ops.GetParent(subcat) is noun


class TestPOSGetParentGuardShape:
    """
    Static pins on the shape of the backfill, independent of any LCM.

    These lock the T2 requirement that the broken GramCatOperations guard
    was not copied across, and that the stub advertises the method.
    """

    def _source(self):
        from flexicon.code.Grammar.POSOperations import POSOperations

        # GetParent is wrapped in the OperationsMethod descriptor, which
        # keeps the raw function on .func.
        descriptor = POSOperations.__dict__["GetParent"]
        return inspect.getsource(descriptor.func)

    def test_method_exists_on_posoperations(self, mock_flex_project):
        from flexicon.code.Grammar.POSOperations import POSOperations

        assert "GetParent" in POSOperations.__dict__
        assert callable(POSOperations(mock_flex_project).GetParent)

    def test_guard_does_not_reference_system_invalidcastexception(self):
        """
        GramCatOperations.GetParent catches System.InvalidCastException in a
        module with no `import System` -- the handler would raise NameError.
        The relocated version must not carry that defect over.
        """
        source = self._source()

        assert "InvalidCastException" not in source, (
            "GetParent must not depend on catching a CLR cast failure; "
            "discriminate the owner on ClassName instead (see #276 T2)."
        )

    def test_guard_discriminates_on_classname(self):
        """The owner check is explicit, not exception-driven."""
        source = self._source()

        assert "ClassName" in source
        assert "PartOfSpeech" in source

    def test_stub_declares_getparent(self):
        """The .pyi must advertise the method it now genuinely has."""
        stub_path = os.path.join(
            _project_root, "flexicon", "code", "Grammar", "POSOperations.pyi"
        )
        with open(stub_path, "r", encoding="utf-8") as handle:
            stub = handle.read()

        assert "def GetParent(self, pos_or_hvo: Any) -> Optional[Any]" in stub
