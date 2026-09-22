#
#   test_allomorph_owner.py
#
#   Class: TestAllomorphGetOwningEntry / TestAllomorphGetOwningEntryNullOwner
#          Offline unit coverage for AllomorphOperations.GetOwningEntry --
#          the allomorph -> owning entry walk.
#
#          This closes one of the three read gaps left untested by CP2a
#          (parser-check R-08, FR-008). The data model exposed the
#          relationship; the script library never wrapped it until CP2a,
#          and CP2a shipped it without a test.
#
#          TWO THINGS ARE AT RISK AND THEY ARE DIFFERENT THINGS.
#
#          (1) THE NULL-OWNER BRANCH. OwnerOfClass answers null when no
#          ancestor of the requested class exists (liblcm CmObject.cs:3349).
#          GetOwningEntry must return None there rather than casting. The
#          implementation's own comment says "the null guard runs BEFORE the
#          ILexEntry cast, because casting a null result is the crash this
#          guard exists to prevent" -- so the ordering, not merely the
#          outcome, is what needs pinning. A cast-then-guard version would
#          still return None for the *mocked* null case while crashing
#          against real pythonnet, which is precisely the kind of defect a
#          mock-based test can wave through. TestAllomorphGetOwningEntry-
#          NullOwner therefore uses a cast recorder that FAILS if it is
#          ever handed None, so guard-after-cast is caught here and not in
#          production.
#
#          (2) THE WALK IS NOT A SINGLE .Owner HOP. An IMoForm reached
#          through an affix-form chain does not necessarily sit directly
#          under its entry, so one hop can land on the wrong object. The
#          implementation deliberately uses OwnerOfClass (the recursive
#          walk) and its docstring names the one-hop GetOwningEntry
#          implementations on EtymologyOperations, PronunciationOperations
#          and VariantOperations as valid for their own shapes and
#          explicitly NOT the template here (D-A8). That is a live
#          confusion -- four classes in this library carry a method of the
#          same name with two different semantics -- so the nested case is
#          exercised directly rather than assumed.
#
#          These tests use plain Python stand-ins and patch the module's
#          ILexEntry with a pass-through recorder, so the real pythonnet
#          cast is never attempted. No FieldWorks is required.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon import AllomorphOperations as allomorph_module
from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations


# ---------------------------------------------------------------------------
# Minimal LCM stand-ins -- no FieldWorks required
# ---------------------------------------------------------------------------

class _FakeEntry:
    """Stand-in for ILexEntry as reached through OwnerOfClass (ICmObject)."""

    ClassName = "LexEntry"

    def __init__(self, hvo=1, headword="run"):
        self.Hvo = hvo
        self.Headword = headword


class _FakeAllomorph:
    """
    Stand-in for IMoForm / IMoStemAllomorph / IMoAffixAllomorph.

    `OwnerOfClass` is modelled as the RECURSIVE walk the real one is, not
    as a single hop, so a one-hop reimplementation fails here.
    """

    ClassName = "MoStemAllomorph"

    def __init__(self, hvo=10, owner=None):
        self.Hvo = hvo
        self.Owner = owner
        self.owner_of_class_calls = []

    def OwnerOfClass(self, class_id):
        self.owner_of_class_calls.append(class_id)
        node = self.Owner
        while node is not None:
            if isinstance(node, _FakeEntry):
                return node
            node = getattr(node, "Owner", None)
        return None


class _FakeIntermediate:
    """
    A non-entry object sitting between an allomorph and its entry.

    This is the shape that makes the difference between OwnerOfClass and a
    single `.Owner` hop observable.
    """

    ClassName = "MoAffixForm"

    def __init__(self, hvo=20, owner=None):
        self.Hvo = hvo
        self.Owner = owner


class _Ops(AllomorphOperations):
    """AllomorphOperations with parameter validation and resolution stubbed."""

    def __init__(self, allomorph):
        self._allomorph = allomorph
        self.validated = []

    def _ValidateParam(self, value, name):
        self.validated.append(name)
        if value is None:
            raise ValueError(f"{name} must not be None")

    def _AllomorphOperations__GetAllomorphObject(self, allomorph_or_hvo):
        return self._allomorph


@pytest.fixture
def cast_recorder(monkeypatch):
    """
    Replace the module-level ILexEntry with a pass-through recorder.

    The real symbol is a pythonnet interface whose call is a CLR cast; it
    cannot run without FieldWorks. The recorder stands in for it AND
    enforces the property that matters: it refuses None. If the null guard
    were ever moved to after the cast, the implementation would hand None
    to this recorder and the test fails loudly -- which is the whole point,
    since a permissive stub would let guard-after-cast pass here and crash
    in production.
    """
    calls = []

    def _record(obj):
        if obj is None:
            raise AssertionError(
                "ILexEntry(...) was called with None. GetOwningEntry must "
                "check for a null owner BEFORE casting -- casting a null "
                "OwnerOfClass result is the crash the guard exists to "
                "prevent, and it is not reproducible against a mock that "
                "tolerates None."
            )
        calls.append(obj)
        return obj

    monkeypatch.setattr(allomorph_module, "ILexEntry", _record)
    return calls


# ---------------------------------------------------------------------------


class TestAllomorphGetOwningEntry:
    """The found-an-owner path."""

    def test_returns_the_owning_entry(self, cast_recorder):
        """The round trip GetAll walks the other way (FR-008)."""
        entry = _FakeEntry(hvo=1, headword="run")
        allomorph = _FakeAllomorph(hvo=10, owner=entry)

        owner = _Ops(allomorph).GetOwningEntry(allomorph)

        assert owner is entry
        assert cast_recorder == [entry], (
            "The owning entry must be passed through the ILexEntry cast. "
            "Raw OwnerOfClass output is typed ICmObject, and pythonnet "
            "surfaces ILexEntry members only after the explicit cast."
        )

    def test_walks_past_an_intermediate_owner(self, cast_recorder):
        """
        The nested case -- the one a single `.Owner` hop gets wrong.

        An IMoForm reached through an affix-form chain does not sit
        directly under its entry. A one-hop implementation would return the
        intermediate object here (or None after the class check), which is
        why this case is exercised rather than assumed. Three sibling
        classes in this library carry a same-named one-hop method, so the
        wrong template is close at hand.
        """
        entry = _FakeEntry(hvo=1, headword="unhappiness")
        intermediate = _FakeIntermediate(hvo=20, owner=entry)
        allomorph = _FakeAllomorph(hvo=10, owner=intermediate)

        owner = _Ops(allomorph).GetOwningEntry(allomorph)

        assert owner is entry, (
            f"GetOwningEntry returned {owner!r} for an allomorph two hops "
            f"below its entry. It must climb the ownership chain "
            f"(OwnerOfClass), not take a single .Owner hop -- the one-hop "
            f"implementations on Etymology/Pronunciation/Variant are valid "
            f"for their own owner shapes and are not the template here."
        )
        assert owner is not intermediate

    def test_asks_owner_of_class_exactly_once(self, cast_recorder):
        """One resolution per call; no repeated climbing."""
        entry = _FakeEntry()
        allomorph = _FakeAllomorph(owner=entry)

        _Ops(allomorph).GetOwningEntry(allomorph)

        assert len(allomorph.owner_of_class_calls) == 1

    def test_validates_its_parameter(self, cast_recorder):
        """The null guard on the argument is the resolver's, and it runs."""
        entry = _FakeEntry()
        allomorph = _FakeAllomorph(owner=entry)
        ops = _Ops(allomorph)

        ops.GetOwningEntry(allomorph)

        assert "allomorph_or_hvo" in ops.validated


class TestAllomorphGetOwningEntryNullOwner:
    """
    The null-owner branch -- returns None, and does so WITHOUT casting.

    `cast_recorder` raises if it is ever handed None, so these tests fail
    on a guard-after-cast implementation rather than quietly passing.
    """

    def test_no_owning_entry_returns_none(self, cast_recorder):
        """Documented: None rather than raising, when no entry is above."""
        orphan = _FakeAllomorph(hvo=10, owner=None)

        owner = _Ops(orphan).GetOwningEntry(orphan)

        assert owner is None, (
            "GetOwningEntry must answer None when no ILexEntry ancestor "
            "exists. OwnerOfClass returns null in that case (liblcm "
            "CmObject.cs:3349) and callers are documented to handle None."
        )

    def test_owner_chain_without_an_entry_returns_none(self, cast_recorder):
        """A chain that never reaches an entry is still the null case."""
        top = _FakeIntermediate(hvo=30, owner=None)
        middle = _FakeIntermediate(hvo=20, owner=top)
        allomorph = _FakeAllomorph(hvo=10, owner=middle)

        owner = _Ops(allomorph).GetOwningEntry(allomorph)

        assert owner is None

    def test_null_owner_is_never_passed_to_the_cast(self, cast_recorder):
        """
        The ordering assertion, stated directly.

        The recorder raises on None, so reaching this line at all proves
        the guard ran first; the empty-call assertion then proves no cast
        was attempted on the null path.
        """
        orphan = _FakeAllomorph(owner=None)

        _Ops(orphan).GetOwningEntry(orphan)

        assert cast_recorder == [], (
            "ILexEntry(...) was called on the null-owner path. The guard "
            "must short-circuit before the cast."
        )
