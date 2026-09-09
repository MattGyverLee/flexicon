#
#   test_276_gramcat_pos_alias.py
#
#   Class: TestGramCatIsPOSAlias
#          TestGramCatGetAllYieldsPartsOfSpeech
#          TestPOSGetParentRoundTrip
#          TestGramCatCreateRaisesAndWritesNothing
#
#          Live LCM verification for issue #276, task T11.
#
#          #276 ruled that a list-level "grammatical category" IS a Part
#          of Speech -- IPartOfSpeech in LangProject.PartsOfSpeechOA --
#          and is NEVER an IFsFeatStrucType in
#          LangProject.MsFeatureSystemOA.TypesOC. The old
#          GramCatOperations walked TypesOC, so recursive=True silently
#          truncated, GetSubcategories/Create(parent=) could not work,
#          and Create() added a stray feature-structure type to the
#          feature system on every call.
#
#          THE RULING ON THE spec.md CONTRADICTION (repo owner, and the
#          reason demonstration 1 below reads the way it does). spec.md
#          section 4 wanted GramCat.Create to raise a helpful
#          FP_ParameterError; sections 2/3 wanted
#          `project.GramCat is project.POS`. Those are mutually
#          exclusive -- if GramCat IS POS, the raising override is never
#          reached and a legacy one-argument caller gets a bare TypeError
#          about a missing 'abbreviation' instead of a migration pointer.
#          The ruling: KEEP THE RAISING OVERRIDE REACHABLE, DROP THE
#          LITERAL `is` IDENTITY. FLExProject.GramCat therefore returns a
#          distinct, lazily-cached GramCatOperations (a subclass of
#          POSOperations) rather than self.POS.
#
#          "Alias" consequently means addresses-the-same-list, not
#          same-object. That is the stronger claim anyway, and it is what
#          demonstration 1 checks: identity of Python objects proves
#          nothing about which LCM collection they read.
#
#          What landed, and what this file verifies against a real LCM:
#            1. FLExProject.GramCat is a distinct cached GramCatOperations
#               that addresses the same list as project.POS, and whose
#               Create is the raising override.
#            2. GetAll() yields IPartOfSpeech, and recursive=True really
#               descends the SubPossibilitiesOS hierarchy.
#            3. POSOperations.GetParent (the T2 backfill) round-trips
#               against AddSubcategory, and is None for a top-level POS.
#            4. GramCatOperations.Create raises FP_ParameterError and
#               writes NOTHING -- the regression that matters most,
#               because the old Create is what corrupted feature systems.
#               Verified on BOTH routes: through project.GramCat (the
#               route a legacy caller actually takes, demonstration 1)
#               and on a directly-instantiated GramCatOperations
#               (demonstration 4).
#
#          Every post-write assertion RE-READS the value from the LCM
#          (re-querying the object by Hvo through GetAll, or re-reading
#          TypesOC.Count off lp) rather than asserting on the object the
#          write returned. Asserting on the value you passed in proves
#          nothing -- CLAUDE.md, "Live LCM Verification".
#
#          Fixture choice: target_sandbox (a tempdir copy of the Target
#          .fwbackup) for everything, rather than target_project. Three
#          of the four demonstrations create categories, and one
#          deliberately provokes a raise on a write path, so a mid-test
#          failure must not be able to touch the user's real Target. The
#          sandbox is also immune to the Target being locked by an open
#          FieldWorks. The one Sena 3 test uses sena3_sandbox for the
#          same reason, though it only reads.
#
#          Run (T11's sanctioned invocation -- never bare pytest):
#
#              python scripts/restore_target.py
#              $env:FLEXLIBS_REQUIRE_LIVE = "1"
#              python -m pytest \
#                  tests/operations/test_276_gramcat_pos_alias.py \
#                  -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import warnings

import pytest

from flexicon import GramCatOperations, POSOperations
from flexicon.code.FLExProject import FP_ParameterError


pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


# ---------------------------------------------------------------------------
# LCM read helpers -- every one of these goes back to the live cache
# ---------------------------------------------------------------------------


def _raw_pos_hvos(project):
    """
    Walk lp.PartsOfSpeechOA directly and return every POS Hvo, depth-first.

    Deliberately does NOT go through POSOperations: it is the independent
    reading that GetAll's output is checked against, so a bug in GetAll
    cannot hide by also corrupting the expectation.
    """
    pos_list = project.lp.PartsOfSpeechOA
    if pos_list is None:
        return []

    hvos = []

    def walk(collection):
        for raw in collection:
            hvos.append(raw.Hvo)
            subs = getattr(raw, "SubPossibilitiesOS", None)
            if subs is not None and subs.Count > 0:
                walk(subs)

    walk(pos_list.PossibilitiesOS)
    return hvos


def _feature_type_state(project):
    """
    Snapshot lp.MsFeatureSystemOA.TypesOC -- the collection the old
    GramCat.Create wrote its strays into.

    Returns a dict with 'present' (is there a feature system at all),
    'count' (TypesOC.Count as read off the LCM) and 'hvos' (a sorted
    tuple, so a same-count swap is still caught).
    """
    feat_system = getattr(project.lp, "MsFeatureSystemOA", None)
    if feat_system is None:
        return {"present": False, "count": 0, "hvos": ()}

    types_oc = feat_system.TypesOC
    return {
        "present": True,
        "count": types_oc.Count,
        "hvos": tuple(sorted(t.Hvo for t in types_oc)),
    }


def _reread_pos_by_hvo(pos_ops, hvo):
    """
    Re-query a POS from the LCM by Hvo via GetAll(recursive=True).

    Used instead of reusing the object Create/AddSubcategory returned:
    finding it in a fresh walk of the list is itself evidence that the
    write reached the LCM and landed in PartsOfSpeechOA.
    """
    for pos in pos_ops.GetAll(recursive=True):
        if pos.Hvo == hvo:
            return pos
    return None


def _describe(pos_ops, pos):
    """Short 'Name (Hvo, ClassName)' string for assertion messages."""
    if pos is None:
        return "None"
    try:
        name = pos_ops.GetName(pos)
    except Exception as exc:  # pragma: no cover - diagnostics only
        name = f"<GetName failed: {exc}>"
    return (
        f"{name!r} (Hvo={getattr(pos, 'Hvo', '?')}, "
        f"ClassName={getattr(pos, 'ClassName', '?')!r})"
    )


def _delete_pos_quietly(pos_ops, hvo):
    """Best-effort cleanup of a TEST_ category by Hvo; never raises."""
    if hvo is None:
        return
    try:
        pos = _reread_pos_by_hvo(pos_ops, hvo)
        if pos is not None:
            pos_ops.Delete(pos)
    except Exception:  # pragma: no cover - sandbox teardown is disposable
        pass


# ---------------------------------------------------------------------------
# T11 demonstration 1 -- the alias addresses the POS list
# ---------------------------------------------------------------------------


def _alias_deprecation_warnings(records):
    """Filter warning records down to the GramCatOperations alias warning."""
    return [
        w
        for w in records
        if issubclass(w.category, DeprecationWarning)
        and "deprecated alias for POSOperations" in str(w.message)
    ]


class TestGramCatIsPOSAlias:
    """
    project.GramCat aliases project.POS -- same list, not the same object.

    Per the ruling recorded in the module header, the alias is a distinct
    cached GramCatOperations so that its raising Create override stays
    reachable. What "alias" has to mean, therefore, is that both spellings
    address lp.PartsOfSpeechOA and nothing else.
    """

    @pytest.mark.live_phase("FLExProject", "read")
    def test_gramcat_property_addresses_the_same_list_as_pos(self, target_sandbox):
        """
        Project: Target (tempdir sandbox copy).

        `project.GramCat is project.POS` is deliberately NOT asserted --
        see the ruling in the module header. Three things are asserted in
        its place, and they are what the identity claim was ever a proxy
        for:

          1. TYPE -- GramCat is a GramCatOperations, hence a POSOperations,
             so the whole inherited CRUD surface is present; and its Create
             resolves to the raising override rather than POSOperations'.
          2. SAME LIST -- GramCat.GetAll() and POS.GetAll() agree on the
             Hvo set, AND that set equals an independent direct walk of
             lp.PartsOfSpeechOA. The third reading matters: two wrappers
             agreeing with each other would prove nothing if both read the
             wrong collection.
          3. CACHED -- project.GramCat is project.GramCat, so the
             DeprecationWarning fires once per project rather than on every
             attribute access.
        """
        assert target_sandbox.writeEnabled is True, (
            "target_sandbox yielded a read-only project; the T11 write-path "
            "demonstrations cannot run against it."
        )
        assert getattr(target_sandbox, "project", None) is not None, (
            "target_sandbox has no underlying LCM cache -- this is a mock, "
            "not a live project, and proves nothing about #276."
        )

        # --- 1. type, and which Create the alias will actually run -------
        # First touch constructs the alias, so it must announce itself.
        with pytest.warns(
            DeprecationWarning, match="deprecated alias for POSOperations"
        ):
            gramcat = target_sandbox.GramCat

        pos = target_sandbox.POS

        assert isinstance(gramcat, GramCatOperations), (
            "project.GramCat returned a "
            f"{type(gramcat).__name__}, not a GramCatOperations. The ruling "
            "requires a distinct deprecated subclass so that its raising "
            "Create override stays reachable; returning self.POS makes the "
            "migration pointer dead code (spec.md section 4)."
        )
        assert isinstance(gramcat, POSOperations), (
            "project.GramCat is a "
            f"{type(gramcat).__name__}, which is not a POSOperations. #276 "
            "ruled the category inventory is the POS list, so the alias must "
            "inherit the POSOperations surface rather than reimplement one."
        )
        assert gramcat is not pos, (
            "project.GramCat returned the very same object as project.POS. "
            "That is the arrangement the ruling rejected: with one object, "
            "GramCatOperations.Create is unreachable and a legacy "
            "one-argument caller gets a bare TypeError about a missing "
            "'abbreviation' instead of the FP_ParameterError that names the "
            "replacement calls."
        )
        # Which class in the MRO actually supplies Create. Resolved through
        # __dict__ rather than getattr: OperationsMethod is a descriptor
        # whose __get__ builds a fresh closure on every class-level access,
        # so `type(x).Create is GramCatOperations.Create` is False even when
        # the override is the one that will run.
        create_owner = next(
            (klass for klass in type(gramcat).__mro__ if "Create" in klass.__dict__),
            None,
        )
        assert create_owner is GramCatOperations, (
            "project.GramCat.Create resolves to "
            f"{getattr(create_owner, '__name__', None)}.Create, not the "
            "GramCatOperations override. The raising override is the "
            "migration signpost; if attribute lookup does not land on it, "
            "the pointer never fires and the caller gets POSOperations' "
            "TypeError instead."
        )
        assert gramcat.project is pos.project, (
            "project.GramCat and project.POS are bound to different "
            "FLExProject objects, so they could be addressing different "
            "databases entirely."
        )

        # --- 2. same list, anchored to the LCM, not to the wrappers ------
        gramcat_hvos = sorted(p.Hvo for p in gramcat.GetAll(recursive=True))
        pos_hvos = sorted(p.Hvo for p in pos.GetAll(recursive=True))
        raw_hvos = sorted(_raw_pos_hvos(target_sandbox))

        assert gramcat_hvos == pos_hvos, (
            "project.GramCat and project.POS disagree about the category "
            f"inventory. GramCat.GetAll returned {len(gramcat_hvos)} Hvos "
            f"{gramcat_hvos}; POS.GetAll returned {len(pos_hvos)} "
            f"{pos_hvos}. An alias that reads a different list is not an "
            "alias -- it is the second CRUD surface #276 removed."
        )
        assert gramcat_hvos == raw_hvos, (
            "Both wrappers agree with each other but not with the LCM. A "
            "direct depth-first walk of lp.PartsOfSpeechOA found "
            f"{len(raw_hvos)} Hvos {raw_hvos}; GetAll returned "
            f"{len(gramcat_hvos)} {gramcat_hvos}."
        )

        feature_types = _feature_type_state(target_sandbox)
        overlap = set(gramcat_hvos) & set(feature_types["hvos"])
        assert not overlap, (
            f"project.GramCat.GetAll returned Hvos {sorted(overlap)} that "
            "are also in lp.MsFeatureSystemOA.TypesOC -- the alias is still "
            "reading the feature system."
        )

        # --- 3. cached, so the deprecation warning fires once ------------
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            again = target_sandbox.GramCat
            once_more = target_sandbox.GramCat

        assert again is gramcat and once_more is gramcat, (
            "project.GramCat is rebuilt on every access "
            f"(first={id(gramcat)}, second={id(again)}, third="
            f"{id(once_more)}). The property must cache its "
            "GramCatOperations on the project."
        )
        assert not _alias_deprecation_warnings(caught), (
            "project.GramCat emitted the deprecation warning again on a "
            "cached access: "
            f"{[str(w.message) for w in _alias_deprecation_warnings(caught)]}. "
            "Once per project is the contract; per-access is noise a caller "
            "will silence wholesale."
        )

    @pytest.mark.live_phase("GramCatOperations", "add")
    def test_gramcat_create_via_the_alias_raises_parameter_error(
        self, target_sandbox
    ):
        """
        Project: Target (tempdir sandbox copy).

        The migration signpost, reached the way a real legacy caller
        reaches it -- through the `project.GramCat` property, not by
        instantiating GramCatOperations by hand.

        This is the half of the ruling that the dropped `is` identity was
        paying for: `project.GramCat.Create(name)` must raise
        FP_ParameterError naming BOTH replacement calls, not a bare
        TypeError about a missing 'abbreviation'. (Before the ruling this
        test asserted exactly that TypeError; the raising override was
        unreachable through the alias.)

        The write-nothing property still has to hold on this route, so
        lp.MsFeatureSystemOA.TypesOC and the lp.PartsOfSpeechOA Hvo set
        are both captured before and RE-READ from the LCM after.
        """
        with pytest.warns(
            DeprecationWarning, match="deprecated alias for POSOperations"
        ):
            gramcat = target_sandbox.GramCat

        before_pos = _raw_pos_hvos(target_sandbox)
        before_types = _feature_type_state(target_sandbox)

        with pytest.raises(FP_ParameterError) as excinfo:
            gramcat.Create(f"{TEST_PREFIX}276_alias_create")

        message = str(excinfo.value)
        assert "project.POS.Create" in message, (
            "The alias route must name project.POS.Create(name, "
            f"abbreviation) as the replacement for a top-level category; "
            f"got: {message}"
        )
        assert "project.POS.AddSubcategory" in message, (
            "The alias route must name project.POS.AddSubcategory(parent, "
            "name, abbreviation) for the former parent= use case; got: "
            f"{message}"
        )

        after_pos = _raw_pos_hvos(target_sandbox)
        after_types = _feature_type_state(target_sandbox)

        assert after_pos == before_pos, (
            "lp.PartsOfSpeechOA changed across a raising "
            f"project.GramCat.Create: {len(before_pos)} categories "
            f"{before_pos} -> {len(after_pos)} categories {after_pos}. The "
            "call must raise before any write."
        )
        assert after_types == before_types, (
            "lp.MsFeatureSystemOA.TypesOC changed across a raising "
            f"project.GramCat.Create: {before_types} -> {after_types}. This "
            "is the exact #276 defect -- a stray IFsFeatStrucType in the "
            "feature system."
        )


# ---------------------------------------------------------------------------
# T11 demonstration 2 -- GetAll yields IPartOfSpeech and really recurses
# ---------------------------------------------------------------------------


class TestGramCatGetAllYieldsPartsOfSpeech:
    """
    GetAll walks lp.PartsOfSpeechOA, not lp.MsFeatureSystemOA.TypesOC.

    The project used by each test is stated in its docstring so the
    evidence file can record it (T11 asks for this explicitly).
    """

    @pytest.mark.live_phase("POSOperations", "read")
    def test_getall_elements_are_partofspeech_not_featstructype(
        self, target_sandbox
    ):
        """
        Project: Target (tempdir sandbox copy of tests/fixtures/Target*.fwbackup).

        Every element GetAll yields is a PartOfSpeech, the set matches an
        independent direct walk of lp.PartsOfSpeechOA, and none of it comes
        from the feature system.
        """
        gramcat = target_sandbox.GramCat

        got = list(gramcat.GetAll(recursive=True))
        expected_hvos = _raw_pos_hvos(target_sandbox)
        feature_types = _feature_type_state(target_sandbox)

        bad = [
            (getattr(p, "Hvo", "?"), getattr(p, "ClassName", None))
            for p in got
            if getattr(p, "ClassName", None) != "PartOfSpeech"
        ]
        assert not bad, (
            "GramCat.GetAll yielded non-PartOfSpeech elements "
            f"{bad}. #276 ruled a list-level grammatical category IS an "
            "IPartOfSpeech; an 'FsFeatStrucType' here means GetAll is still "
            "walking lp.MsFeatureSystemOA.TypesOC."
        )

        assert sorted(p.Hvo for p in got) == sorted(expected_hvos), (
            "GramCat.GetAll does not match a direct depth-first walk of "
            f"lp.PartsOfSpeechOA. GetAll returned {len(got)} Hvos "
            f"{sorted(p.Hvo for p in got)}; the direct walk found "
            f"{len(expected_hvos)} {sorted(expected_hvos)}."
        )

        overlap = set(p.Hvo for p in got) & set(feature_types["hvos"])
        assert not overlap, (
            f"GramCat.GetAll returned Hvos {sorted(overlap)} that are also in "
            "lp.MsFeatureSystemOA.TypesOC -- it is still reading the feature "
            "system, contradicting the #276 ruling that an IFsFeatStrucType "
            "is never a grammatical category."
        )

    @pytest.mark.live_phase("POSOperations", "add")
    def test_recursive_descends_below_top_level_on_created_nesting(
        self, target_sandbox
    ):
        """
        Project: Target (tempdir sandbox copy). The Target is mostly blank
        and may carry no nested categories of its own, so this test CREATES
        a two-deep TEST_ hierarchy, re-reads it from the LCM, and then
        compares recursive=True against recursive=False. The Sena 3 sibling
        test below covers naturally-occurring nesting.

        recursive=True must return strictly more categories than
        recursive=False, and must include the descendants by Hvo. The old
        TypesOC implementation could never do this: IFsFeatStrucType has no
        SubPossibilitiesOS, so recursion silently truncated.
        """
        pos_ops = target_sandbox.POS
        baseline = len(_raw_pos_hvos(target_sandbox))

        root_hvo = sub_hvo = grandchild_hvo = None
        try:
            root = pos_ops.Create(f"{TEST_PREFIX}276_Root_A", "T276rA")
            root_hvo = root.Hvo
            sub = pos_ops.AddSubcategory(root, f"{TEST_PREFIX}276_Sub_A", "T276sA")
            sub_hvo = sub.Hvo
            grandchild = pos_ops.AddSubcategory(
                sub, f"{TEST_PREFIX}276_Grandchild_A", "T276gA"
            )
            grandchild_hvo = grandchild.Hvo

            # Re-read everything from the LCM; nothing below relies on the
            # objects the writes returned.
            flat_hvos = [p.Hvo for p in pos_ops.GetAll(recursive=False)]
            deep_hvos = [p.Hvo for p in pos_ops.GetAll(recursive=True)]

            assert root_hvo in flat_hvos, (
                f"The created top-level category (Hvo={root_hvo}) is absent "
                "from GetAll(recursive=False) -- the write did not reach "
                "lp.PartsOfSpeechOA.PossibilitiesOS."
            )
            assert sub_hvo not in flat_hvos and grandchild_hvo not in flat_hvos, (
                "GetAll(recursive=False) leaked descendants: sub="
                f"{sub_hvo}, grandchild={grandchild_hvo}, flat={flat_hvos}. "
                "recursive=False must yield top-level categories only."
            )
            assert sub_hvo in deep_hvos and grandchild_hvo in deep_hvos, (
                "GetAll(recursive=True) did not descend: expected sub="
                f"{sub_hvo} and grandchild={grandchild_hvo} in {deep_hvos}. "
                "This is exactly the truncation #276 identified -- recursion "
                "only works because IPartOfSpeech has SubPossibilitiesOS."
            )
            assert len(deep_hvos) > len(flat_hvos), (
                f"recursive=True returned {len(deep_hvos)} categories and "
                f"recursive=False returned {len(flat_hvos)}; on a project "
                "with nested categories the recursive walk must return "
                "strictly more."
            )
            assert len(deep_hvos) == baseline + 3, (
                f"Expected {baseline} + 3 categories after creating a root, "
                f"a subcategory and a grandchild; the LCM reports "
                f"{len(deep_hvos)}."
            )
        finally:
            _delete_pos_quietly(pos_ops, root_hvo)

        restored = len(_raw_pos_hvos(target_sandbox))
        assert restored == baseline, (
            f"[NOTE] cleanup check (not part of the #276 ruling): expected "
            f"{baseline} categories after deleting the TEST_ root, found "
            f"{restored}. Deleting a parent should remove its subtree."
        )

    @pytest.mark.live_phase("POSOperations", "read")
    def test_recursive_descends_on_sena3_natural_nesting(self, sena3_sandbox):
        """
        Project: Sena 3 (tempdir sandbox copy of
        tests/fixtures/Sena 3*.fwbackup). Read-only.

        Same claim as the test above, but against nesting that already
        exists in a populated project rather than nesting this file made.

        SKIPS if Sena 3 turns out to have no nested categories -- in that
        case the created-nesting test on the Target is the demonstration of
        record, and the evidence file should say so.
        """
        pos_ops = sena3_sandbox.POS

        flat = list(pos_ops.GetAll(recursive=False))
        deep = list(pos_ops.GetAll(recursive=True))

        nested_parents = [
            p for p in flat if p.SubPossibilitiesOS.Count > 0
        ]
        if not nested_parents:
            pytest.skip(
                "[NOTE] Sena 3 has no top-level category with "
                "subcategories, so strictly-more cannot be demonstrated "
                "here. Rely on "
                "test_recursive_descends_below_top_level_on_created_nesting."
            )

        expected_children = sorted(
            c.Hvo for c in nested_parents[0].SubPossibilitiesOS
        )
        deep_hvos = sorted(p.Hvo for p in deep)

        assert len(deep) > len(flat), (
            f"recursive=True returned {len(deep)} categories and "
            f"recursive=False returned {len(flat)}, yet Sena 3 has "
            f"{len(nested_parents)} top-level categories with children. "
            "The recursive walk is truncating."
        )
        missing = [h for h in expected_children if h not in deep_hvos]
        assert not missing, (
            f"GetAll(recursive=True) omitted the known subcategories "
            f"{missing} of "
            f"{_describe(pos_ops, nested_parents[0])}."
        )


# ---------------------------------------------------------------------------
# T11 demonstration 3 -- GetParent round-trips against AddSubcategory
# ---------------------------------------------------------------------------


class TestPOSGetParentRoundTrip:
    """The T2 backfill, exercised against a live LCM rather than stand-ins."""

    @pytest.mark.live_phase("POSOperations", "add")
    def test_getparent_returns_the_owning_category_after_addsubcategory(
        self, target_sandbox
    ):
        """
        Project: Target (tempdir sandbox copy).

        AddSubcategory then GetParent must round-trip. The subcategory is
        RE-QUERIED from the LCM by Hvo before GetParent is called -- the
        object AddSubcategory returned is deliberately not reused, so the
        parent link is read out of the database rather than out of Python.
        """
        pos_ops = target_sandbox.POS
        baseline = len(_raw_pos_hvos(target_sandbox))

        root_hvo = None
        try:
            root = pos_ops.Create(f"{TEST_PREFIX}276_Parent_B", "T276pB")
            root_hvo = root.Hvo
            child_hvo = pos_ops.AddSubcategory(
                root, f"{TEST_PREFIX}276_Child_B", "T276cB"
            ).Hvo

            reread_child = _reread_pos_by_hvo(pos_ops, child_hvo)
            assert reread_child is not None, (
                f"The subcategory (Hvo={child_hvo}) could not be found by "
                "re-walking GetAll(recursive=True) -- AddSubcategory did not "
                "reach the LCM, or GetAll is not descending."
            )

            parent = pos_ops.GetParent(reread_child)

            assert parent is not None, (
                "POS.GetParent returned None for "
                f"{_describe(pos_ops, reread_child)}, which was just added "
                f"under Hvo={root_hvo}. #276 T2 requires GetParent to return "
                "the owning IPartOfSpeech for a subcategory."
            )
            assert parent.Hvo == root_hvo, (
                "POS.GetParent returned the wrong owner: got "
                f"{_describe(pos_ops, parent)}, expected the category at "
                f"Hvo={root_hvo}."
            )
            assert getattr(parent, "ClassName", None) == "PartOfSpeech", (
                "POS.GetParent returned an object whose ClassName is "
                f"{getattr(parent, 'ClassName', None)!r}, not 'PartOfSpeech'. "
                "The owner must be cast to IPartOfSpeech so subtype-only "
                "members are reachable; .Owner alone hands back a bare "
                "ICmObject."
            )
            # Subtype-only member: proves the cast, not just the ClassName.
            assert parent.SubPossibilitiesOS.Count >= 1, (
                "The returned parent exposes no SubPossibilitiesOS entries, "
                "yet it owns the subcategory just created."
            )
            assert pos_ops.GetName(parent) == f"{TEST_PREFIX}276_Parent_B", (
                "Name read back from the LCM for the parent is "
                f"{pos_ops.GetName(parent)!r}, expected "
                f"{TEST_PREFIX + '276_Parent_B'!r}."
            )

            # The stated inverse contract: GetParent inverts GetSubcategories.
            subcats = pos_ops.GetSubcategories(parent, recursive=False)
            assert [s.Hvo for s in subcats] == [child_hvo], (
                "GetSubcategories(parent) returned "
                f"{[s.Hvo for s in subcats]}, expected exactly [{child_hvo}]."
            )
            for subcat in subcats:
                assert pos_ops.GetParent(subcat).Hvo == parent.Hvo, (
                    "GetParent does not invert GetSubcategories for "
                    f"{_describe(pos_ops, subcat)}."
                )
        finally:
            _delete_pos_quietly(pos_ops, root_hvo)

        restored = len(_raw_pos_hvos(target_sandbox))
        assert restored == baseline, (
            f"[NOTE] cleanup check (not part of the #276 ruling): expected "
            f"{baseline} categories after cleanup, found {restored}."
        )

    @pytest.mark.live_phase("POSOperations", "add")
    def test_getparent_returns_none_for_a_top_level_category(
        self, target_sandbox
    ):
        """
        Project: Target (tempdir sandbox copy).

        A top-level POS is owned by the ICmPossibilityList at
        lp.PartsOfSpeechOA, which is not a possibility and therefore not a
        parent category. GetParent must report None -- not the list, and not
        an exception. The category is re-queried from the LCM first.
        """
        pos_ops = target_sandbox.POS
        baseline = len(_raw_pos_hvos(target_sandbox))

        top_hvo = None
        try:
            top_hvo = pos_ops.Create(f"{TEST_PREFIX}276_Top_C", "T276tC").Hvo

            reread_top = _reread_pos_by_hvo(pos_ops, top_hvo)
            assert reread_top is not None, (
                f"The created top-level category (Hvo={top_hvo}) is not in "
                "GetAll -- Create did not reach lp.PartsOfSpeechOA."
            )

            owner_class = getattr(
                getattr(reread_top, "Owner", None), "ClassName", None
            )
            parent = pos_ops.GetParent(reread_top)

            assert parent is None, (
                "POS.GetParent returned "
                f"{_describe(pos_ops, parent)} for the top-level category "
                f"{_describe(pos_ops, reread_top)}, whose LCM Owner has "
                f"ClassName {owner_class!r}. #276 T2 requires None here: the "
                "owning CmPossibilityList is not a category."
            )
        finally:
            _delete_pos_quietly(pos_ops, top_hvo)

        restored = len(_raw_pos_hvos(target_sandbox))
        assert restored == baseline, (
            f"[NOTE] cleanup check (not part of the #276 ruling): expected "
            f"{baseline} categories after cleanup, found {restored}."
        )


# ---------------------------------------------------------------------------
# T11 demonstration 4 -- the regression that matters most
# ---------------------------------------------------------------------------


class TestGramCatCreateRaisesAndWritesNothing:
    """
    GramCatOperations.Create must raise and write NOTHING.

    The retired implementation added an IFsFeatStrucType to
    lp.MsFeatureSystemOA.TypesOC on every call -- a stray that shows up in
    FLEx under Grammar > Features and is indistinguishable from legitimate
    TypeCreate output. This class captures TypesOC before the call and
    re-reads it after, so a resurrected write cannot pass unnoticed.

    Note the deprecated class is instantiated DIRECTLY here. Under the
    ruling (see the module header) project.GramCat returns a distinct
    GramCatOperations, so the override is reachable BOTH ways; the alias
    route -- the one a legacy caller actually takes -- is covered by
    TestGramCatIsPOSAlias.test_gramcat_create_via_the_alias_raises_parameter_error.
    This class additionally pins the old parent= shape.
    """

    @pytest.mark.live_phase("GramCatOperations", "add")
    def test_create_raises_parameter_error_and_writes_nothing(
        self, target_sandbox
    ):
        """
        Project: Target (tempdir sandbox copy).

        Both the old one-argument shape and the old parent= shape must
        raise FP_ParameterError, and neither may change
        lp.MsFeatureSystemOA.TypesOC or lp.PartsOfSpeechOA.
        """
        with pytest.warns(
            DeprecationWarning, match="deprecated alias for POSOperations"
        ):
            gramcat_ops = GramCatOperations(target_sandbox)

        before_types = _feature_type_state(target_sandbox)
        before_pos = _raw_pos_hvos(target_sandbox)

        # --- shape 1: GramCat.Create(name) -------------------------------
        with pytest.raises(FP_ParameterError) as excinfo_plain:
            gramcat_ops.Create(f"{TEST_PREFIX}276_gramcat_create")

        message = str(excinfo_plain.value)
        assert "project.POS.Create" in message, (
            "FP_ParameterError must name project.POS.Create(name, "
            f"abbreviation) as the replacement; got: {message}"
        )
        assert "project.POS.AddSubcategory" in message, (
            "FP_ParameterError must name project.POS.AddSubcategory(parent, "
            f"name, abbreviation) for the parent= use case; got: {message}"
        )

        mid_types = _feature_type_state(target_sandbox)
        assert mid_types == before_types, (
            "GramCat.Create(name) mutated the feature system despite "
            f"raising. lp.MsFeatureSystemOA.TypesOC went {before_types} -> "
            f"{mid_types}. This is the exact #276 defect: the call must "
            "raise BEFORE any write, never add an IFsFeatStrucType."
        )

        # --- shape 2: GramCat.Create(name, parent=...) -------------------
        # parent is accepted and ignored; the raise must precede any
        # resolution of it, so an existing POS is used when one is present
        # and a deliberately bogus value otherwise.
        parent_arg = before_pos[0] if before_pos else f"{TEST_PREFIX}no_such_parent"

        with pytest.raises(FP_ParameterError) as excinfo_parent:
            gramcat_ops.Create(
                f"{TEST_PREFIX}276_gramcat_create_child", parent=parent_arg
            )

        assert "project.POS.AddSubcategory" in str(excinfo_parent.value), (
            "The parent= shape must point the caller at "
            "project.POS.AddSubcategory; got: "
            f"{excinfo_parent.value}"
        )

        # --- re-read both collections from the LCM -----------------------
        after_types = _feature_type_state(target_sandbox)
        after_pos = _raw_pos_hvos(target_sandbox)

        assert after_types["count"] == before_types["count"], (
            "lp.MsFeatureSystemOA.TypesOC.Count changed across two raising "
            f"GramCat.Create calls: {before_types['count']} -> "
            f"{after_types['count']}. #276 requires the count to be "
            "identical; a stray IFsFeatStrucType is precisely the corruption "
            "this change removes."
        )
        assert after_types == before_types, (
            "lp.MsFeatureSystemOA.TypesOC changed identity across two "
            f"raising GramCat.Create calls: {before_types} -> {after_types}."
        )
        assert after_pos == before_pos, (
            "lp.PartsOfSpeechOA changed across two raising GramCat.Create "
            f"calls: {len(before_pos)} categories {before_pos} -> "
            f"{len(after_pos)} categories {after_pos}. A raising Create must "
            "not create a category either."
        )
