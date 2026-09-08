#
#   test_collection_cast_pattern.py
#
#   Class: TestCastAllHelper / TestCollectionCastSites /
#          TestComplexFormRoundTrip / TestSubPossibilityRecursion /
#          TestChartCellSubtypeFilters / TestGramCatGetAllRecursionClaim /
#          TestCollectionCastLive
#
#          Regression coverage for the COLLECTION half of the
#          base-interface casting bug class (issue #270).
#
#   Bug class:
#     The Pattern A sweep (295f613, issues #159/#166/#168) cast 14
#     `.Owner` return sites -- locked by the sibling file
#     tests/operations/test_owner_cast_pattern.py -- but never touched
#     COLLECTION returns. LCM collections are declared over a BASE
#     interface:
#
#       ILexEntryRef.ComponentLexemesRS  -> ICmObject
#       ILexReference.TargetsRS          -> ICmObject
#       ICmPossibilityList.PossibilitiesOS,
#       ICmPossibility.SubPossibilitiesOS -> ICmPossibility
#       IConstChartRow.CellsOS           -> IConstituentChartCellPart
#
#     pythonnet hands the elements back as that declared base, so:
#
#       * no subtype property is reachable (`comp.LexemeFormOA` ->
#         AttributeError; `item.SubPossibilitiesOS` -> AttributeError on
#         an ICmObject element),
#       * `isinstance(element, <its own concrete interface>)` is False,
#         which silently turns an isinstance FILTER into an empty list
#         and an isinstance GUARD into a false rejection,
#       * `hasattr(element, "XxxOS")` is False, which silently turns
#         recursion into a no-op,
#       * and the element therefore cannot be round-tripped back into
#         any other flexicon method.
#
#   The canonical fix is BaseOperations._GetTypedElements() (which
#   delegates to lcm_casting.cast_all -> cast_to_concrete per element),
#   plus ClassName-based discrimination anywhere isinstance was used to
#   filter or guard.
#
#   These tests lock the PATTERN, not just the instances:
#
#     1. Pure-Python behavioural tests of cast_all/_GetTypedElements with
#        a stubbed interface cache. No LCM needed.
#     2. Behavioural tests that model the real pythonnet semantics with
#        stubs -- an UNCAST element hides the subtype surface, a CAST one
#        exposes it -- so the pre-fix code genuinely fails them.
#     3. Static source checks over every fixed site.
#     4. Live behavioural checks, marked requires_live_project.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import json
import pathlib

import pytest

from flexicon.code import lcm_casting
from flexicon.code.BaseOperations import BaseOperations


# ---------------------------------------------------------------------------
# Stubs that model pythonnet's declared-interface behaviour.
#
# `_Raw` is what a collection element looks like BEFORE the cast: it
# carries only ICmObject surface (ClassName, Hvo). `_Concrete` is the
# proxy the cast produces: it adds the subtype surface. A test that
# asserts on `_Concrete`-only attributes therefore fails against the
# pre-fix `return list(collection)` implementations.
# ---------------------------------------------------------------------------


class _Raw:
    """An element as the base interface hands it over: ICmObject only."""

    def __init__(self, class_name, hvo, subtype_attrs=None, children=()):
        self.ClassName = class_name
        self.Hvo = hvo
        self._subtype_attrs = subtype_attrs or {}
        self._children = list(children)


class _FakeSeq(list):
    """Stand-in for an LcmOwningSequence / LcmReferenceSequence."""

    @property
    def Count(self):
        return len(self)

    def Add(self, item):
        self.append(item)


class _Concrete:
    """The proxy `cast_to_concrete()` produces: base + subtype surface."""

    def __init__(self, raw):
        self._raw = raw
        self.ClassName = raw.ClassName
        self.Hvo = raw.Hvo
        self.was_cast = True
        for name, value in raw._subtype_attrs.items():
            setattr(self, name, value)
        if raw._children:
            # Children are handed out RAW, exactly as LCM would: the
            # caller must cast them in turn or the hierarchy stops here.
            self.SubPossibilitiesOS = _FakeSeq(raw._children)


@pytest.fixture
def stub_cast(monkeypatch):
    """
    Replace lcm_casting's ClassName -> interface map with Python stubs.

    Deterministic in every environment (real FieldWorks, or a session
    where SIL is a MagicMock), and it lets a test observe whether each
    individual element went through the cast.
    """
    classes = (
        "LexEntry",
        "LexSense",
        "CmPossibility",
        "PartOfSpeech",
        "CmAnthroItem",
        "LexEntryType",
        "ConstChartTag",
        "ConstChartWordGroup",
        "ConstChartMovedTextMarker",
        "ConstChartClauseMarker",
        "ConstChartRow",
    )
    monkeypatch.setattr(
        lcm_casting, "_interface_cache", {name: _Concrete for name in classes}
    )
    monkeypatch.setattr(lcm_casting, "_interfaces_loaded", True)
    return classes


def _ops(cls, project=None):
    """Build an Operations instance without constructing an FLExProject."""
    instance = cls.__new__(cls)
    instance.project = project
    return instance


# ---------------------------------------------------------------------------
# 1. The helpers themselves
# ---------------------------------------------------------------------------


class TestCastAllHelper:
    """lcm_casting.cast_all and BaseOperations._GetTypedElements."""

    def test_cast_all_casts_every_element_in_order(self, stub_cast):
        raws = [_Raw("LexEntry", 1), _Raw("LexSense", 2), _Raw("LexEntry", 3)]
        result = lcm_casting.cast_all(raws)

        assert len(result) == 3, "cast_all changed the element count"
        assert [e.Hvo for e in result] == [1, 2, 3], "cast_all reordered elements"
        assert all(getattr(e, "was_cast", False) for e in result), (
            "cast_all did not cast every element -- a partial cast is the "
            "issue #270 bug in miniature."
        )

    def test_cast_all_passes_through_unknown_classnames(self, stub_cast):
        raw = _Raw("SomeClassLcmDoesNotMap", 9)
        (result,) = lcm_casting.cast_all([raw])
        assert result is raw, (
            "cast_all must be TOTAL: an unrecognised ClassName has to come "
            "back unchanged, otherwise applying it blanket-wise is unsafe."
        )

    def test_cast_all_tolerates_non_lcm_elements(self, stub_cast):
        assert lcm_casting.cast_all(["a", 1, None]) == ["a", 1, None]

    def test_cast_all_of_none_is_empty_list(self, stub_cast):
        assert lcm_casting.cast_all(None) == []

    def test_cast_all_accepts_a_generator(self, stub_cast):
        gen = (_Raw("LexEntry", i) for i in range(3))
        result = lcm_casting.cast_all(gen)
        assert [e.Hvo for e in result] == [0, 1, 2]

    def test_base_operations_helper_exists(self):
        assert hasattr(BaseOperations, "_GetTypedElements"), (
            "BaseOperations._GetTypedElements centralises the "
            "collection-element cast (issue #270), mirroring "
            "_GetTypedOwner for scalar .Owner returns. Removing it "
            "un-fixes every collection getter listed in #270."
        )

    def test_base_operations_helper_delegates_to_cast_all(self):
        src = inspect.getsource(BaseOperations._GetTypedElements)
        assert "cast_all" in src, (
            "_GetTypedElements must route through lcm_casting so the "
            "ClassName->interface map stays the single source of truth."
        )

    def test_base_operations_helper_returns_a_real_list(self, stub_cast):
        ops = _ops(BaseOperations)
        result = ops._GetTypedElements(_FakeSeq([_Raw("LexEntry", 1)]))
        assert isinstance(result, list), (
            "_GetTypedElements must return a sequence, not a generator: "
            "_needs_enumerable_wrap() leaves lists alone, so a generator "
            "here would silently change the GetAll contract."
        )
        assert ops._GetTypedElements(None) == []


class TestNoBlanketCastInEnumerableWrapper:
    """
    Architecture decision record (issue #270).

    The issue proposed a blanket cast inside
    EnumerableWrapper._ensure_list/__iter__. That was rejected:

      * It fixes almost nothing. Of the 26 sites #270 lists, 21 return a
        PLAIN PYTHON LIST, and _needs_enumerable_wrap() deliberately
        declines to wrap anything that is already a sequence -- so those
        21 never pass through the wrapper at all. Two more are scalar
        `.Owner` returns. Only 3 (generator bodies) would have been
        reached.
      * It would put a per-element ClassName lookup on every large
        GetAll* in the library, including callers that only want .Count.
      * It would change element identity for `x in wrapper` and `==`
        comparisons against an uncast object.

    This test pins the decision so a future "simplification" does not
    silently reintroduce the risk.
    """

    def test_ensure_list_does_not_cast(self):
        from flexicon.code.BaseOperations import EnumerableWrapper

        src = inspect.getsource(EnumerableWrapper)
        assert "cast_to_concrete" not in src and "cast_all" not in src, (
            "EnumerableWrapper must stay a pure shape adapter. Casting "
            "inside it would (a) miss the 21 of 26 issue-#270 sites that "
            "return plain lists, (b) add a per-element ClassName lookup "
            "to every GetAll*, and (c) change __contains__/== semantics "
            "for callers holding an uncast object. Casting belongs at the "
            "site, via BaseOperations._GetTypedElements()."
        )

    def test_plain_lists_are_not_wrapped(self):
        """The premise of the decision above, asserted directly."""
        from flexicon.code.BaseOperations import _needs_enumerable_wrap

        assert _needs_enumerable_wrap([1, 2, 3]) is False, (
            "If plain lists were wrapped, a wrapper-level cast would have "
            "covered most #270 sites. They are not."
        )
        assert _needs_enumerable_wrap(iter([1, 2, 3])) is True


# ---------------------------------------------------------------------------
# 2. Tier 1: Get/Add composability for complex-form components
# ---------------------------------------------------------------------------


def _fake_complex_entry(components):
    """A stub ILexEntry carrying one complex-form LexEntryRef."""
    from SIL.LCModel import LexEntryRefTags

    class _EntryRef:
        def __init__(self):
            self.RefType = LexEntryRefTags.krtComplexForm
            self.ComponentLexemesRS = _FakeSeq(components)
            self.PrimaryLexemesRS = _FakeSeq()
            self.ShowComplexFormsInRS = _FakeSeq()

    class _Entry:
        ClassName = "LexEntry"
        Hvo = 100

        def __init__(self):
            self.EntryRefsOS = [_EntryRef()]

    return _Entry()


class TestComplexFormRoundTrip:
    """
    GetComplexFormComponents -> AddComplexFormComponent must compose.

    Both halves were broken: the getter returned raw ICmObject, and the
    adder guarded with `isinstance(component, (ILexEntry, ILexSense))`,
    which is False for exactly those objects.
    """

    def test_getter_casts_every_component(self, stub_cast):
        from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = _ops(LexEntryOperations)
        entry = _fake_complex_entry(
            [
                _Raw("LexEntry", 1, {"LexemeFormOA": "kick"}),
                _Raw("LexSense", 2, {"SensesOS": []}),
            ]
        )

        components = ops.GetComplexFormComponents(entry)

        assert len(components) == 2
        assert all(getattr(c, "was_cast", False) for c in components), (
            "GetComplexFormComponents still returns raw ComponentLexemesRS "
            "elements. ComponentLexemesRS is declared over ICmObject, so "
            "the caller gets objects with no ILexEntry/ILexSense surface "
            "(issue #270 Tier 1)."
        )

    def test_returned_components_expose_concrete_properties(self, stub_cast):
        """The reported production AttributeError, asserted directly."""
        from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = _ops(LexEntryOperations)
        entry = _fake_complex_entry([_Raw("LexEntry", 1, {"LexemeFormOA": "kick"})])

        (component,) = ops.GetComplexFormComponents(entry)

        assert hasattr(component, "LexemeFormOA"), (
            "A component returned by GetComplexFormComponents does not "
            "expose ILexEntry surface. This is the reported production "
            "AttributeError (issue #270)."
        )

    def test_add_accepts_getter_output(self, stub_cast, monkeypatch):
        """Feed the getter's output straight back into the adder."""
        import contextlib

        from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

        class _Project:
            writeEnabled = True

        ops = _ops(LexEntryOperations, _Project())
        monkeypatch.setattr(
            ops, "_TransactionCM", lambda label: contextlib.nullcontext(), raising=False
        )

        source = _fake_complex_entry([_Raw("LexEntry", 1), _Raw("LexSense", 2)])
        components = ops.GetComplexFormComponents(source)

        target = _fake_complex_entry([])
        for component in components:
            # Pre-fix this raised FP_ParameterError("Component must be an
            # ILexEntry or ILexSense") for every element, because the
            # guard used isinstance against the concrete interface.
            ops.AddComplexFormComponent(target, component)

        landed = [c.Hvo for c in target.EntryRefsOS[0].ComponentLexemesRS]
        assert landed == [1, 2], (
            "Get/Add are still not composable: components returned by "
            "GetComplexFormComponents did not survive "
            "AddComplexFormComponent (issue #270)."
        )

    def test_add_still_rejects_a_wrong_class(self, stub_cast, monkeypatch):
        """The guard must stay a guard -- not be loosened into nothing."""
        import contextlib

        from flexicon.code.FLExProject import FP_ParameterError
        from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

        class _Project:
            writeEnabled = True

        ops = _ops(LexEntryOperations, _Project())
        monkeypatch.setattr(
            ops, "_TransactionCM", lambda label: contextlib.nullcontext(), raising=False
        )

        target = _fake_complex_entry([])
        with pytest.raises(FP_ParameterError):
            ops.AddComplexFormComponent(
                target, _Raw("MoStemAllomorph", 7)
            )

    def test_add_guard_does_not_use_isinstance(self):
        """
        The guard has to discriminate on ClassName.

        `isinstance` is a false negative for any object that has not been
        through cast_to_concrete -- including an HVO resolved by
        __ResolveObject -- so it rejected precisely the objects the
        matching getter produced.
        """
        src = _method_source(
            "flexicon.code.Lexicon.LexEntryOperations",
            "LexEntryOperations",
            "AddComplexFormComponent",
        )
        assert "isinstance(component, (ILexEntry, ILexSense))" not in src, (
            "AddComplexFormComponent still guards with isinstance against "
            "the concrete interfaces (issue #270)."
        )
        assert "ClassName" in src, (
            "AddComplexFormComponent must validate via ClassName, which is "
            "declared on ICmObject and therefore readable whether or not "
            "the object has been cast."
        )

    def test_docstring_example_does_not_use_isinstance(self):
        """
        The documented example told users to write
        `isinstance(comp, ILexEntry)`, which is False for every element
        the method returns and so silently skipped all of them.
        """
        from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

        doc = LexEntryOperations.__dict__["GetComplexFormComponents"].__doc__ or ""
        assert "isinstance(comp, ILexEntry)" not in doc, (
            "GetComplexFormComponents' docstring still shows the "
            "isinstance example. Even with the elements cast, an "
            "isinstance example is the fragile form -- the discriminator "
            "has to be ClassName (issue #270)."
        )
        assert 'comp.ClassName == "LexEntry"' in doc, (
            "The corrected example must branch on ClassName, matching the "
            "already-correct example in LexReferenceOperations.GetTargets."
        )


# ---------------------------------------------------------------------------
# 3. Possibility-hierarchy recursion (the silent-no-op shape)
# ---------------------------------------------------------------------------


class TestSubPossibilityRecursion:
    """
    Recursion guarded by `hasattr(child, "SubPossibilitiesOS")` over
    UNCAST children never descends -- it produces missing results rather
    than an error, so nothing failed loudly.

    The stub hierarchy below hands children out raw (no
    SubPossibilitiesOS until cast), exactly as LCM does.
    """

    @staticmethod
    def _hierarchy():
        grandchild = _Raw("CmPossibility", 3)
        child = _Raw("CmPossibility", 2, children=[grandchild])
        return _Concrete(_Raw("CmPossibility", 1, children=[child]))

    def test_gramcat_getsubcategories_descends(self, stub_cast):
        from flexicon.code.Grammar.GramCatOperations import GramCatOperations

        ops = _ops(GramCatOperations)
        result = ops.GetSubcategories(self._hierarchy())

        assert [r.Hvo for r in result] == [2, 3], (
            "GetSubcategories(recursive=True) did not reach the grandchild. "
            "Uncast children answer False to "
            'hasattr(child, "SubPossibilitiesOS"), so the recursion is a '
            "silent no-op and results go missing without an error "
            "(issue #270)."
        )

    def test_gramcat_getsubcategories_casts_direct_children(self, stub_cast):
        from flexicon.code.Grammar.GramCatOperations import GramCatOperations

        ops = _ops(GramCatOperations)
        result = ops.GetSubcategories(
            self._hierarchy(), recursive=False
        )
        assert [r.Hvo for r in result] == [2]
        assert all(getattr(r, "was_cast", False) for r in result)

    def test_possibilitylist_getsubitems_descends(self, stub_cast):
        from flexicon.code.Lists.PossibilityListOperations import (
            PossibilityListOperations,
        )

        ops = _ops(PossibilityListOperations)
        result = ops.GetSubitems(self._hierarchy())

        assert [r.Hvo for r in result] == [2, 3], (
            "GetSubitems(recursive=True) did not reach the grandchild "
            "(issue #270)."
        )

    def test_publication_getsubpublications_descends(self, stub_cast):
        from flexicon.code.Lists.PublicationOperations import PublicationOperations

        ops = _ops(PublicationOperations)
        result = ops.GetSubPublications(
            self._hierarchy()
        )
        assert [r.Hvo for r in result] == [2, 3]

    def test_anthropology_getsubitems_descends(self, stub_cast, monkeypatch):
        from flexicon.code.Notebook.AnthropologyOperations import (
            AnthropologyOperations,
        )

        ops = _ops(AnthropologyOperations)
        hierarchy = self._hierarchy()
        # __GetItemObject already casts via ICmAnthroItem(...); bypass it
        # so the test stays pure-Python and targets the element cast.
        monkeypatch.setattr(
            ops,
            "_AnthropologyOperations__GetItemObject",
            lambda item_or_hvo: item_or_hvo,
            raising=False,
        )
        result = ops.GetSubitems(hierarchy)
        assert [r.Hvo for r in result] == [2, 3]


class TestPossibilityItemResolverCasts:
    """
    PossibilityItemOperations.__ResolveObject returned
    FLExProject.Object()'s bare ICmObject. Every subclass method that
    then guarded on `hasattr(obj, "SubPossibilitiesOS")` -- e.g.
    PublicationOperations.GetDivisions / GetSubPublications -- silently
    returned [] when handed an HVO.
    """

    def test_hvo_resolution_is_cast(self, stub_cast):
        from flexicon.code.Lists.PublicationOperations import PublicationOperations

        raw_child = _Raw("CmPossibility", 2)
        raw_parent = _Raw("CmPossibility", 1, children=[raw_child])

        class _Project:
            @staticmethod
            def Object(hvo):
                return raw_parent

        ops = _ops(PublicationOperations, _Project())
        divisions = ops.GetDivisions(1)

        assert [d.Hvo for d in divisions] == [2], (
            "GetDivisions(hvo) returned nothing. The HVO resolved to a "
            'bare ICmObject, hasattr(obj, "SubPossibilitiesOS") was False, '
            "and the method silently reported no divisions (issue #270)."
        )


# ---------------------------------------------------------------------------
# 4. Chart cell parts: isinstance filters over a base-typed collection
# ---------------------------------------------------------------------------


class TestChartCellSubtypeFilters:
    """
    `[c for c in row.CellsOS if isinstance(c, IConstChartTag)]` matched
    nothing, because CellsOS elements arrive as the declared
    IConstituentChartCellPart. The filter returned an empty list instead
    of raising, so it looked like "this row has no tags".
    """

    @staticmethod
    def _row():
        class _Row:
            ClassName = "ConstChartRow"
            Hvo = 50
            CellsOS = _FakeSeq(
                [
                    _Raw("ConstChartTag", 1, {"ColumnRA": None}),
                    _Raw("ConstChartWordGroup", 2, {"BeginSegmentRA": None}),
                    _Raw("ConstChartTag", 3, {"ColumnRA": None}),
                    _Raw("ConstChartMovedTextMarker", 4),
                ]
            )

        return _Row()

    def test_cell_tag_getall_finds_tags(self, stub_cast):
        from flexicon.code.Discourse.ConstChartCellTagOperations import (
            ConstChartCellTagOperations,
        )

        ops = _ops(ConstChartCellTagOperations)
        result = ops.GetAll(self._row())

        assert [r.Hvo for r in result] == [1, 3], (
            "ConstChartCellTagOperations.GetAll did not find the row's "
            "tags. isinstance() over CellsOS matches nothing because the "
            "elements arrive as the declared base "
            "IConstituentChartCellPart, so this silently returned [] for "
            "every row (issue #270 Tier 4)."
        )
        assert all(getattr(r, "was_cast", False) for r in result)

    def test_word_group_getters_return_only_word_groups(self, stub_cast):
        from flexicon.code.Discourse.ConstChartRowOperations import (
            ConstChartRowOperations,
        )
        from flexicon.code.Discourse.ConstChartWordGroupOperations import (
            ConstChartWordGroupOperations,
        )

        row_ops = _ops(ConstChartRowOperations)
        wg_ops = _ops(ConstChartWordGroupOperations)

        for label, result in (
            (
                "ConstChartRowOperations.GetWordGroups",
                row_ops.GetWordGroups(self._row()),
            ),
            (
                "ConstChartWordGroupOperations.GetAll",
                wg_ops.GetAll(self._row()),
            ),
        ):
            assert [r.Hvo for r in result] == [2], (
                f"{label} returned {[r.Hvo for r in result]}. It promises "
                "IConstChartWordGroup objects but was returning every "
                "cell-part subtype in CellsOS, uncast (issue #270 Tier 4)."
            )
            assert all(getattr(r, "was_cast", False) for r in result)

    def test_discourse_getcells_returns_every_subtype_cast(self, stub_cast, monkeypatch):
        from flexicon.code.TextsWords.DiscourseOperations import DiscourseOperations

        ops = _ops(DiscourseOperations)
        monkeypatch.setattr(
            ops,
            "_DiscourseOperations__GetRowObject",
            lambda row_or_hvo: row_or_hvo,
            raising=False,
        )
        result = ops.GetCells(self._row())

        assert [r.Hvo for r in result] == [1, 2, 3, 4], (
            "GetCells deliberately returns EVERY cell-part subtype; it "
            "must not filter."
        )
        assert all(getattr(r, "was_cast", False) for r in result), (
            "GetCells elements are still uncast, so callers cannot reach "
            "any subtype's surface (issue #270 Tier 4)."
        )


# ---------------------------------------------------------------------------
# 5. Static source coverage over every fixed site
# ---------------------------------------------------------------------------


def _method_source(import_path, class_name, method_name):
    """Source text of an Operations method, peeling descriptor layers."""
    import importlib

    module = importlib.import_module(import_path)
    cls = getattr(module, class_name)

    obj = None
    for klass in cls.__mro__:
        if method_name in klass.__dict__:
            obj = klass.__dict__[method_name]
            break
    assert obj is not None, f"{class_name} has no method {method_name}"

    seen = set()
    while id(obj) not in seen:
        seen.add(id(obj))
        if hasattr(obj, "func") and not inspect.isfunction(obj):
            obj = obj.func
        elif hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
        else:
            break
    return inspect.getsource(obj)


# (label, import_path, class, method, the base-typed collection it reads)
_FIXED_SITES = [
    ("LexEntryOperations.GetComplexFormComponents",
     "flexicon.code.Lexicon.LexEntryOperations",
     "LexEntryOperations", "GetComplexFormComponents", "ComponentLexemesRS"),
    ("VariantOperations.GetComponentLexemes",
     "flexicon.code.Lexicon.VariantOperations",
     "VariantOperations", "GetComponentLexemes", "ComponentLexemesRS"),
    ("LexReferenceOperations.GetTargets",
     "flexicon.code.Lexicon.LexReferenceOperations",
     "LexReferenceOperations", "GetTargets", "TargetsRS"),
    ("PossibilityListOperations.GetItems",
     "flexicon.code.Lists.PossibilityListOperations",
     "PossibilityListOperations", "GetItems", "PossibilitiesOS"),
    ("PossibilityListOperations.GetSubitems",
     "flexicon.code.Lists.PossibilityListOperations",
     "PossibilityListOperations", "GetSubitems", "SubPossibilitiesOS"),
    ("PossibilityItemOperations.GetAll",
     "flexicon.code.Lists.possibility_item_base",
     "PossibilityItemOperations", "GetAll", "PossibilitiesOS"),
    ("PublicationOperations.GetAll",
     "flexicon.code.Lists.PublicationOperations",
     "PublicationOperations", "GetAll", "PossibilitiesOS"),
    ("PublicationOperations.GetDivisions",
     "flexicon.code.Lists.PublicationOperations",
     "PublicationOperations", "GetDivisions", "SubPossibilitiesOS"),
    ("PublicationOperations.GetSubPublications",
     "flexicon.code.Lists.PublicationOperations",
     "PublicationOperations", "GetSubPublications", "SubPossibilitiesOS"),
    ("AnthropologyOperations.GetSubitems",
     "flexicon.code.Notebook.AnthropologyOperations",
     "AnthropologyOperations", "GetSubitems", "SubPossibilitiesOS"),
    ("DataNotebookOperations.GetAllRecordTypes",
     "flexicon.code.Notebook.DataNotebookOperations",
     "DataNotebookOperations", "GetAllRecordTypes", "PossibilitiesOS"),
    ("DataNotebookOperations.GetAllStatuses",
     "flexicon.code.Notebook.DataNotebookOperations",
     "DataNotebookOperations", "GetAllStatuses", "PossibilitiesOS"),
    ("GramCatOperations.GetSubcategories",
     "flexicon.code.Grammar.GramCatOperations",
     "GramCatOperations", "GetSubcategories", "SubPossibilitiesOS"),
    ("VariantOperations.GetAllTypes",
     "flexicon.code.Lexicon.VariantOperations",
     "VariantOperations", "GetAllTypes", "PossibilitiesOS"),
    ("ConstChartMarkerOperations.GetAll",
     "flexicon.code.Discourse.ConstChartMarkerOperations",
     "ConstChartMarkerOperations", "GetAll", "WalkMarkers"),
    ("ConstChartRowOperations.GetWordGroups",
     "flexicon.code.Discourse.ConstChartRowOperations",
     "ConstChartRowOperations", "GetWordGroups", "CellsOS"),
    ("ConstChartWordGroupOperations.GetAll",
     "flexicon.code.Discourse.ConstChartWordGroupOperations",
     "ConstChartWordGroupOperations", "GetAll", "CellsOS"),
    ("ConstChartCellTagOperations.GetAll",
     "flexicon.code.Discourse.ConstChartCellTagOperations",
     "ConstChartCellTagOperations", "GetAll", "CellsOS"),
    ("DiscourseOperations.GetCells",
     "flexicon.code.TextsWords.DiscourseOperations",
     "DiscourseOperations", "GetCells", "CellsOS"),
]


class TestCollectionCastSites:
    """Every site #270 confirmed broken must route elements through the cast."""

    @pytest.mark.parametrize(
        "label,import_path,class_name,method_name,collection", _FIXED_SITES
    )
    def test_site_casts_its_elements(
        self, label, import_path, class_name, method_name, collection
    ):
        src = _method_source(import_path, class_name, method_name)
        assert "_GetTypedElements" in src or "cast_to_concrete" in src, (
            f"{label} does not cast its elements. {collection} is declared "
            f"over a BASE interface, so the raw elements expose no subtype "
            f"surface, fail isinstance against their own interface, and "
            f"cannot be round-tripped back into flexicon (issue #270). "
            f"Use self._GetTypedElements(...)."
        )

    @pytest.mark.parametrize(
        "label,import_path,class_name,method_name,collection", _FIXED_SITES
    )
    def test_site_has_no_bare_list_return(
        self, label, import_path, class_name, method_name, collection
    ):
        """`return list(<base-typed collection>)` is the bug signature."""
        src = _method_source(import_path, class_name, method_name)
        for holder in ("", "entry_ref.", "lex_ref.", "row.", "item.", "cat.",
                       "poss_list.", "list_obj.", "publication."):
            bad = f"return list({holder}{collection})"
            assert bad not in src, (
                f"{label} still contains `{bad}` -- the issue #270 bug "
                f"signature. Route it through self._GetTypedElements()."
            )

    def test_owner_sites_use_the_owner_helper(self):
        """Tier 2: the three `.Owner` returns the Pattern A sweep missed."""
        for import_path, class_name, method_name in (
            ("flexicon.code.Notebook.NoteOperations", "NoteOperations", "GetOwner"),
            ("flexicon.code.Shared.MediaOperations", "MediaOperations", "GetOwners"),
        ):
            src = _method_source(import_path, class_name, method_name)
            assert "_GetTypedOwner" in src, (
                f"{class_name}.{method_name} still returns a raw .Owner. "
                "The Pattern A sweep (#159/#166/#168) missed it; route it "
                "through self._GetTypedOwner() (issue #270 Tier 2)."
            )

    def test_annotation_owner_property_casts(self):
        from flexicon.code.Notebook.annotation import Annotation

        src = inspect.getsource(Annotation.owner.fget)
        assert "cast_to_concrete" in src, (
            "Annotation.owner still returns a raw ICmObject .Owner "
            "(issue #270 Tier 2). It is a wrapper property, not an "
            "Operations method, so it calls cast_to_concrete directly."
        )

    def test_cast_registry_covers_the_new_subtypes(self):
        """
        The cast is only as good as the ClassName -> interface map.

        Tier 3/4 needed possibility subtypes and the four chart cell-part
        subtypes registered in lcm_casting; without them cast_to_concrete
        is a no-op at exactly the sites #270 reports.
        """
        src = inspect.getsource(lcm_casting._ensure_interfaces)
        for class_name in (
            "CmSemanticDomain",
            "CmLocation",
            "CmPerson",
            "MoMorphType",
            "CmAnnotationDefn",
            "LexEntryType",
            "ConstChartRow",
            "ConstChartTag",
            "ConstChartWordGroup",
            "ConstChartMovedTextMarker",
            "ConstChartClauseMarker",
        ):
            assert f'"{class_name}"' in src, (
                f"lcm_casting no longer registers {class_name}. "
                f"cast_to_concrete() silently degrades to a no-op for that "
                f"ClassName, which re-breaks the issue #270 sites that "
                f"depend on it."
            )


# ---------------------------------------------------------------------------
# 6. The one #270 claim that does NOT hold: GramCatOperations.GetAll
# ---------------------------------------------------------------------------


_BASELINE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "contract"
    / "snapshots"
    / "liblcm_baseline.json"
)


class TestGramCatGetAllRecursionClaim:
    """
    Issue #270 reports GramCatOperations.GetAll's
    `hasattr(cat, "SubPossibilitiesOS")` guard as a casting bug. It is a
    real silent no-op, but NOT a casting one, and casting cannot fix it.

    GetAll walks `lp.MsFeatureSystemOA.TypesOC`, whose elements are
    IFsFeatStrucType. Per the checked-in LCM reflection baseline,
    IFsFeatStrucType is not an ICmPossibility and has no
    SubPossibilitiesOS at all, so the guard is CORRECTLY False and the
    recursion is unreachable no matter how the element is cast. Fixing it
    means deciding what a "grammatical category" is (a feature-struc-type
    or a possibility) -- a data-model decision, tracked separately.

    This test pins the finding so nobody "fixes" GetAll by adding a cast
    that does nothing, and fails loudly if a future LCM makes
    IFsFeatStrucType a possibility (at which point the recursion becomes
    real and GetAll must be revisited).
    """

    def test_fsfeatstructype_has_no_subpossibilities(self):
        types = json.loads(_BASELINE.read_text(encoding="utf-8"))["types"]
        entry = types.get("IFsFeatStrucType")
        assert entry and entry.get("found"), (
            "IFsFeatStrucType missing from the LCM baseline snapshot; "
            "regenerate tests/contract/snapshots/liblcm_baseline.json."
        )
        assert "SubPossibilitiesOS" not in entry["properties"], (
            "IFsFeatStrucType now exposes SubPossibilitiesOS. "
            "GramCatOperations.GetAll's recursion over "
            "MsFeatureSystemOA.TypesOC was dead code precisely because it "
            "did not -- revisit GetAll (issue #270 'bonus' claim)."
        )
        assert "SIL.LCModel.ICmPossibility" not in entry["interfaces"]

    def test_getall_recursion_is_documented_as_unreachable(self):
        """
        GetAll must not pretend to be fixed by a cast that is a no-op for
        FsFeatStrucType. If someone adds one, this test asks them to
        resolve the data-model question instead.
        """
        src = _method_source(
            "flexicon.code.Grammar.GramCatOperations",
            "GramCatOperations",
            "GetAll",
        )
        assert "MsFeatureSystemOA" in src, (
            "GramCatOperations.GetAll no longer reads MsFeatureSystemOA -- "
            "the data-model question this test documents has moved. "
            "Update the test alongside it."
        )


# ---------------------------------------------------------------------------
# 7. Live behavioural coverage (requires a real FLEx project)
#
# Run with:
#   $env:FLEXLIBS_REQUIRE_LIVE = "1"
#   python -m pytest tests/operations/test_collection_cast_pattern.py \
#       -m requires_live_project -q
# ---------------------------------------------------------------------------


@pytest.mark.requires_live_project
class TestCollectionCastLive:
    """
    Behavioural verification of the outcomes, not the source shapes.

    Sandbox flavour throughout (target_sandbox / sena3_sandbox), so a
    failure mid-test cannot touch the user's real projects.
    """

    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_complex_form_component_round_trip(self, target_sandbox):
        """
        Pre-state:  a TEST_ complex entry with one TEST_ component.
        Action:     GetComplexFormComponents -> AddComplexFormComponent
                    on a SECOND complex entry, with no unwrapping.
        Post-state: re-query the second entry's components from the LCM
                    and confirm the component's Hvo is present.
        """
        entries = target_sandbox.LexEntry
        created = []
        try:
            component = entries.Create(lexeme_form="TEST_270_component")
            first = entries.Create(lexeme_form="TEST_270_complex_a")
            second = entries.Create(lexeme_form="TEST_270_complex_b")
            created = [component, first, second]

            entries.AddComplexFormComponent(first, component)

            fetched = list(entries.GetComplexFormComponents(first))
            assert fetched, "pre-state: the component did not attach"

            # The round trip: straight back in, uncast by the caller.
            for comp in fetched:
                assert comp.ClassName in ("LexEntry", "LexSense")
                # Concrete-surface proof: unreachable before the fix.
                assert hasattr(comp, "LexemeFormOA") or hasattr(comp, "SensesOS")
                entries.AddComplexFormComponent(second, comp)

            # Post-state read back from the LCM, not from `fetched`.
            reread = [c.Hvo for c in entries.GetComplexFormComponents(second)]
            assert component.Hvo in reread, (
                f"post-state: component Hvo {component.Hvo} not in {reread}"
            )
        finally:
            for obj in reversed(created):
                try:
                    entries.Delete(obj)
                except Exception:
                    pass

    @pytest.mark.live_phase("PossibilityListOperations", "read")
    def test_possibility_items_expose_subtype_surface(self, sena3_sandbox):
        """
        Pre-state:  the Parts of Speech list, whose items are really
                    PartOfSpeech (not bare CmPossibility).
        Post-state: every item answers ClassName == "PartOfSpeech" AND
                    exposes IPartOfSpeech-only surface
                    (DefaultInflectionClassRA), which a bare
                    ICmPossibility element does not.
        """
        pos_list = sena3_sandbox.lp.PartsOfSpeechOA
        if pos_list is None:
            pytest.skip("Sena 3 has no PartsOfSpeech list")

        items = list(sena3_sandbox.PossibilityLists.GetItems(pos_list, recursive=False))
        assert items, "pre-state: Parts of Speech list is empty"
        for item in items:
            assert item.ClassName == "PartOfSpeech"
            assert hasattr(item, "DefaultInflectionClassRA"), (
                "GetItems element does not expose IPartOfSpeech surface -- "
                "it is still a bare ICmPossibility (issue #270 Tier 3)."
            )

    @pytest.mark.live_phase("PossibilityListOperations", "read")
    def test_subitem_recursion_reaches_grandchildren(self, sena3_sandbox):
        """
        Pre-state:  a semantic domain with at least two hierarchy levels.
        Post-state: GetSubitems(recursive=True) returns strictly more
                    items than GetSubitems(recursive=False), proving the
                    recursion is no longer a silent no-op.
        """
        sem_list = sena3_sandbox.lp.SemanticDomainListOA
        if sem_list is None:
            pytest.skip("Sena 3 has no semantic domain list")

        lists = sena3_sandbox.PossibilityLists
        for top in lists.GetItems(sem_list, recursive=False):
            direct = list(lists.GetSubitems(top, recursive=False))
            deep = list(lists.GetSubitems(top, recursive=True))
            if direct and len(deep) > len(direct):
                assert set(i.Hvo for i in direct) <= set(i.Hvo for i in deep)
                return
        pytest.skip("No multi-level semantic domain found to exercise recursion")

    @pytest.mark.live_phase("ConstChartCellTagOperations", "read")
    def test_chart_cell_tag_getall_is_not_empty_when_tags_exist(self, sena3_sandbox):
        """
        Pre-state:  a chart row whose CellsOS contains a ConstChartTag
                    (established by reading ClassName directly off
                    CellsOS, which needs no cast).
        Post-state: ConstChartCellTagOperations.GetAll(row) returns
                    exactly those tags. Before the fix the isinstance
                    filter matched nothing and this was always [].
        """
        charts = list(sena3_sandbox.ConstChart.GetAll())
        if not charts:
            pytest.skip("Sena 3 has no constituent charts")

        for chart in charts:
            for row in sena3_sandbox.ConstChartRows.GetAll(chart):
                expected = [
                    c.Hvo for c in row.CellsOS if c.ClassName == "ConstChartTag"
                ]
                if not expected:
                    continue
                actual = [t.Hvo for t in sena3_sandbox.ConstChartCellTags.GetAll(row)]
                assert actual == expected, (
                    f"GetAll returned {actual}, expected {expected}. The "
                    "isinstance filter over CellsOS matched nothing "
                    "(issue #270 Tier 4)."
                )
                return
        pytest.skip("No chart row with a ConstChartTag found in Sena 3")
