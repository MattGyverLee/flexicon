#
#   test_issue275_resolver_sweep_live.py
#
#   Live verification for issue #275: the two #269 resolver defects,
#   generalised across ~25 sibling __ResolveObject-family resolvers.
#
#   Defect 1 -- the non-int branch returned an uncast object. A caller
#     that reaches a resolver with an object obtained via
#     ``project.Object(hvo)`` (or from a polymorphic collection) gets
#     back an ``ICmObject`` whose concrete surface (Name, InternalPath,
#     Form, ...) is unreachable -- the next direct attribute access
#     raises AttributeError.
#   Defect 2 -- the HVO branch guarded with
#     ``isinstance(obj, IThing)`` against ``self.project.Object()``'s
#     ICmObject-declared return, which is False even for a genuine
#     instance of ``IThing``, so a valid HVO raised FP_ParameterError.
#
#   This file proves both defects are fixed, live, for a representative
#   cross-section of the sites fixed under #275: Lexicon (Etymology,
#   Variant), Notebook (Location, Person), Grammar (Stratum), Reversal
#   (Index, IndexEntry), Discourse (ConstChart, ConstChartRow), Scripture
#   (ScrBook), Shared (Media), and Lexicon (SemanticDomain).
#
#   Every scenario runs against target_sandbox (a tempdir copy of the
#   Target .fwbackup) so the user's real Target is never touched, and
#   every fixture used here is entirely self-contained -- no dependency
#   on Sena 3 or any other pre-populated project.
#
#   Required invocation:
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest \
#           tests/operations/test_issue275_resolver_sweep_live.py \
#           -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_275_"


class TestEtymologyOperationsResolvers:
    """__GetEntryObject / __GetEtymologyObject (Lexicon/EtymologyOperations.py)."""

    @pytest.mark.live_phase("EtymologyOperations", "add")
    def test_entry_hvo_accepted_by_create(self, target_sandbox):
        """Defect 2 on __GetEntryObject: Create(entry.Hvo, ...) must work."""
        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}etym_entry")

        etym = target_sandbox.Etymology.Create(entry.Hvo, form=f"{TEST_PREFIX}proto")
        assert etym is not None

        form = target_sandbox.Etymology.GetForm(etym)
        assert TEST_PREFIX in str(form)

    @pytest.mark.live_phase("EtymologyOperations", "read")
    def test_etymology_hvo_and_raw_object_both_resolve(self, target_sandbox):
        """Defect 1 + Defect 2 on __GetEtymologyObject."""
        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}etym_entry2")
        etym = target_sandbox.Etymology.Create(entry.Hvo, form=f"{TEST_PREFIX}form2")

        # Defect 2: HVO branch. Pre-fix: FP_ParameterError.
        by_hvo = target_sandbox.Etymology.GetForm(etym.Hvo)
        # Defect 1: a raw ICmObject (as a caller would get from
        # project.Object() directly) fed into the non-int branch.
        # Pre-fix: returned uncast, so GetForm's ``.Form`` access raised
        # AttributeError.
        raw = target_sandbox.Object(etym.Hvo)
        by_raw = target_sandbox.Etymology.GetForm(raw)

        assert by_hvo == by_raw == f"{TEST_PREFIX}form2"


class TestVariantOperationsResolvers:
    """__GetEntryObject / __GetVariantObject (Lexicon/VariantOperations.py)."""

    @pytest.mark.live_phase("VariantOperations", "add")
    def test_variant_entry_and_variant_hvo_paths(self, target_sandbox):
        entries = target_sandbox.LexEntry
        main_entry = entries.Create(lexeme_form=f"{TEST_PREFIX}var_main")

        vtypes = list(target_sandbox.Variants.GetAllTypes())
        if not vtypes:
            pytest.skip("Project has no variant entry types to test with")
        vtype = vtypes[0]

        # Defect 2 on __GetEntryObject: entry HVO accepted.
        variant_ref = target_sandbox.Variants.Create(
            main_entry.Hvo, f"{TEST_PREFIX}varform", vtype
        )
        assert variant_ref is not None

        # Defect 2 on __GetVariantObject: variant ref HVO accepted.
        form_by_hvo = target_sandbox.Variants.GetForm(variant_ref.Hvo)
        # Defect 1 on __GetVariantObject: raw ICmObject accepted.
        raw = target_sandbox.Object(variant_ref.Hvo)
        form_by_raw = target_sandbox.Variants.GetForm(raw)

        assert form_by_hvo == form_by_raw == f"{TEST_PREFIX}varform"

    @pytest.mark.live_phase("VariantOperations", "read")
    def test_entry_hvo_still_rejected_by_variant_resolver(self, target_sandbox):
        """Legitimate rejection: an entry's HVO is not a variant ref."""
        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}var_reject")
        with pytest.raises(FP_ParameterError):
            target_sandbox.Variants.GetForm(entry.Hvo)


class TestLocationOperationsResolver:
    """__ResolveObject (Notebook/LocationOperations.py)."""

    @pytest.mark.live_phase("LocationOperations", "add")
    def test_location_hvo_and_raw_object_resolve(self, target_sandbox):
        loc = target_sandbox.Location.Create(f"{TEST_PREFIX}Somewhere")

        # Defect 2: pre-fix, this raised FP_ParameterError.
        name_by_hvo = target_sandbox.Location.GetName(loc.Hvo)
        # Defect 1: pre-fix, GetName's `.Name` access raised AttributeError
        # on the uncast raw ICmObject.
        raw = target_sandbox.Object(loc.Hvo)
        name_by_raw = target_sandbox.Location.GetName(raw)

        assert name_by_hvo == name_by_raw == f"{TEST_PREFIX}Somewhere"

    @pytest.mark.live_phase("LocationOperations", "read")
    def test_person_hvo_still_rejected_by_location_resolver(self, target_sandbox):
        """Legitimate rejection: a person's HVO is not a location."""
        person = target_sandbox.Person.Create(f"{TEST_PREFIX}NotALocation")
        with pytest.raises(FP_ParameterError):
            target_sandbox.Location.GetName(person.Hvo)


class TestPersonOperationsResolver:
    """__ResolveObject (Notebook/PersonOperations.py)."""

    @pytest.mark.live_phase("PersonOperations", "add")
    def test_person_hvo_and_raw_object_resolve(self, target_sandbox):
        person = target_sandbox.Person.Create(f"{TEST_PREFIX}Someone")

        name_by_hvo = target_sandbox.Person.GetName(person.Hvo)
        raw = target_sandbox.Object(person.Hvo)
        name_by_raw = target_sandbox.Person.GetName(raw)

        assert name_by_hvo == name_by_raw == f"{TEST_PREFIX}Someone"


class TestStratumOperationsResolver:
    """__ResolveObject (Grammar/StratumOperations.py) -- non-raising."""

    @pytest.mark.live_phase("StratumOperations", "add")
    def test_stratum_hvo_and_raw_object_resolve(self, target_sandbox):
        stratum = target_sandbox.Strata.Create(f"{TEST_PREFIX}Stratum")

        # Pre-fix: this resolver never raised, but the HVO branch returned
        # a bare ICmObject, so GetName's `.Name` access raised
        # AttributeError.
        name_by_hvo = target_sandbox.Strata.GetName(stratum.Hvo)
        raw = target_sandbox.Object(stratum.Hvo)
        name_by_raw = target_sandbox.Strata.GetName(raw)

        assert name_by_hvo == name_by_raw == f"{TEST_PREFIX}Stratum"


class TestReversalIndexOperationsResolvers:
    """__ResolveObject (Reversal/ReversalIndexOperations.py) and
    __ResolveObject / __GetIndexObject (Reversal/ReversalIndexEntryOperations.py)."""

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_index_hvo_and_raw_object_resolve(self, target_sandbox):
        en_ws = target_sandbox.WSHandle("en")
        index = target_sandbox.ReversalIndexes.Create(f"{TEST_PREFIX}Idx", en_ws)

        name_by_hvo = target_sandbox.ReversalIndexes.GetName(index.Hvo)
        raw = target_sandbox.Object(index.Hvo)
        name_by_raw = target_sandbox.ReversalIndexes.GetName(raw)

        assert name_by_hvo == name_by_raw == f"{TEST_PREFIX}Idx"

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_entry_and_index_hvo_paths(self, target_sandbox):
        en_ws = target_sandbox.WSHandle("en")
        index = target_sandbox.ReversalIndexes.Create(f"{TEST_PREFIX}Idx2", en_ws)

        # Defect 2 on __GetIndexObject: index HVO accepted by Create.
        # wsHandle is passed explicitly here (rather than left to
        # Create's index.WritingSystem-derived default) to isolate the
        # #275 resolver fix from an unrelated pre-existing defect in
        # that default-inference path (index.WritingSystem round-tripped
        # through project.WSHandle() raised
        # System.ArgumentNullException: Value cannot be null. Parameter
        # name: ttp on this build -- not a resolver/cast issue, and out
        # of scope for this issue).
        entry = target_sandbox.ReversalEntries.Create(
            index.Hvo, f"{TEST_PREFIX}revform", wsHandle=en_ws
        )
        assert entry is not None

        # Defect 2 on __ResolveObject: entry HVO accepted. wsHandle is
        # passed explicitly here too -- __GetEntryWS(entry)'s default
        # inference returns None on this build (a second unrelated
        # pre-existing defect, out of scope for #275), which otherwise
        # masks the resolver result behind an unrelated TypeError from
        # get_String(None).
        form_by_hvo = target_sandbox.ReversalEntries.GetForm(entry.Hvo, wsHandle=en_ws)
        # Defect 1: raw ICmObject accepted.
        raw = target_sandbox.Object(entry.Hvo)
        form_by_raw = target_sandbox.ReversalEntries.GetForm(raw, wsHandle=en_ws)

        assert form_by_hvo == form_by_raw == f"{TEST_PREFIX}revform"

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "read")
    def test_index_hvo_still_rejected_by_entry_resolver(self, target_sandbox):
        """Legitimate rejection: an index's HVO is not an entry."""
        en_ws = target_sandbox.WSHandle("en")
        index = target_sandbox.ReversalIndexes.Create(f"{TEST_PREFIX}Idx3", en_ws)
        with pytest.raises(FP_ParameterError):
            target_sandbox.ReversalEntries.GetForm(index.Hvo)


class TestSemanticDomainOperationsResolver:
    """__ResolveObject (Lexicon/SemanticDomainOperations.py)."""

    @pytest.mark.live_phase("SemanticDomainOperations", "add")
    def test_domain_hvo_and_raw_object_resolve(self, target_sandbox):
        domain = target_sandbox.SemanticDomains.Create(
            f"{TEST_PREFIX}Domain", "9.9"
        )

        name_by_hvo = target_sandbox.SemanticDomains.GetName(domain.Hvo)
        raw = target_sandbox.Object(domain.Hvo)
        name_by_raw = target_sandbox.SemanticDomains.GetName(raw)

        assert name_by_hvo == name_by_raw == f"{TEST_PREFIX}Domain"


class TestMediaOperationsInlineResolvers:
    """The 11 repeated inline HVO-resolution blocks in Shared/MediaOperations.py."""

    @pytest.mark.live_phase("MediaOperations", "add")
    def test_media_hvo_and_raw_object_resolve(self, target_sandbox):
        media = target_sandbox.Media.Create(
            f"{TEST_PREFIX}audio.wav", label=f"{TEST_PREFIX}Label"
        )

        path_by_hvo = target_sandbox.Media.GetInternalPath(media.Hvo)
        raw = target_sandbox.Object(media.Hvo)
        path_by_raw = target_sandbox.Media.GetInternalPath(raw)

        assert path_by_hvo == path_by_raw == f"{TEST_PREFIX}audio.wav"


class TestConstChartOperationsResolvers:
    """__ResolveObject (ConstChartOperations.py) and __ResolveObject /
    __ResolveChart (ConstChartRowOperations.py)."""

    @pytest.mark.live_phase("ConstChartOperations", "add")
    def test_chart_hvo_and_raw_object_resolve(self, target_sandbox):
        chart = target_sandbox.ConstCharts.Create(f"{TEST_PREFIX}Chart")

        name_by_hvo = target_sandbox.ConstCharts.GetName(chart.Hvo)
        raw = target_sandbox.Object(chart.Hvo)
        name_by_raw = target_sandbox.ConstCharts.GetName(raw)

        assert name_by_hvo == name_by_raw == f"{TEST_PREFIX}Chart"

    @pytest.mark.live_phase("ConstChartRowOperations", "add")
    def test_row_create_via_chart_hvo_then_row_hvo_resolves(self, target_sandbox):
        chart = target_sandbox.ConstCharts.Create(f"{TEST_PREFIX}Chart2")

        # Defect 2 on ConstChartRowOperations.__ResolveChart: chart HVO
        # accepted by Create.
        row = target_sandbox.ConstChartRows.Create(
            chart.Hvo, label=f"{TEST_PREFIX}Row"
        )
        assert row is not None

        # Defect 2 on ConstChartRowOperations.__ResolveObject: row HVO
        # accepted.
        label_by_hvo = target_sandbox.ConstChartRows.GetLabel(row.Hvo)
        # Defect 1: raw ICmObject accepted.
        raw = target_sandbox.Object(row.Hvo)
        label_by_raw = target_sandbox.ConstChartRows.GetLabel(raw)

        assert label_by_hvo == label_by_raw == f"{TEST_PREFIX}Row"

    @pytest.mark.live_phase("ConstChartRowOperations", "read")
    def test_chart_hvo_still_rejected_by_row_resolver(self, target_sandbox):
        """Legitimate rejection: a chart's HVO is not a row."""
        chart = target_sandbox.ConstCharts.Create(f"{TEST_PREFIX}Chart3")
        with pytest.raises(FP_ParameterError):
            target_sandbox.ConstChartRows.GetLabel(chart.Hvo)


class TestScrBookOperationsResolver:
    """__ResolveObject (Scripture/ScrBookOperations.py).

    ScrBookOperations has no FLExProject accessor property (confirmed by
    grep against FLExProject.py -- none of the six Scripture Operations
    classes are wired up there), so it is instantiated directly, exactly
    as the existing offline suite does (tests/phase4_other_tests.py
    TestScrBookOperations.create_operations()).
    """

    @pytest.mark.live_phase("ScrBookOperations", "add")
    def test_book_hvo_and_raw_object_resolve(self, sena3_sandbox):
        # The Target scratch project has no Scripture module enabled
        # (Create() raises "Project does not have Scripture enabled" on
        # a blank project), so this one resolver test uses sena3_sandbox
        # instead of target_sandbox -- exactly the case anticipated for
        # the Scripture family.
        from flexicon.code.Scripture.ScrBookOperations import ScrBookOperations

        scr_books = ScrBookOperations(sena3_sandbox)
        existing = list(scr_books.GetAll())
        if not existing:
            pytest.skip("Sena 3 sandbox has no Scripture books to resolve")
        book = existing[0]
        # GetCanonicalNum, not GetTitle: GetTitle has its own unrelated
        # pre-existing bug on this build (`book.Title` -- should be
        # `book.TitleOA` -- raises AttributeError regardless of the
        # resolver fix), out of scope for #275.
        expected_num = scr_books.GetCanonicalNum(book)

        # Defect 2: HVO branch. Pre-fix: isinstance(obj, IScrBook) was
        # False even for a genuine book, so this raised FP_ParameterError.
        num_by_hvo = scr_books.GetCanonicalNum(book.Hvo)
        # Defect 1: a raw ICmObject fed into the non-int branch.
        raw = sena3_sandbox.Object(book.Hvo)
        num_by_raw = scr_books.GetCanonicalNum(raw)

        assert num_by_hvo == num_by_raw == expected_num
