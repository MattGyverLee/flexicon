#
#   test_issue334_guid_parse_formatexception_live.py
#
#   Live-LCM verification for issue #334: four unguarded System.Guid(...)
#   parses leaked a bare CLR System.FormatException / ArgumentNullException
#   instead of an FP_ParameterError. This file exercises the two framings
#   named in the ruling against a real (sandboxed) FLEx project:
#
#     1. Shared/catalog_backed.py::_create_from_entry -- catalog-sourced
#        Guid (malformed shipped data), raise BEFORE the transaction opens.
#     2. Grammar/PhonFeatureOperations.py::__CreateValueWithGuid, reached
#        via the public ApplySyncableProperties -- caller-supplied Guid in
#        a hand-built props dict.
#
#   Per CLAUDE.md's live-verification protocol, this file uses the
#   `target_sandbox` fixture (a tempdir copy of the Target .fwbackup) so
#   nothing can leak into a real project, and is gated by
#   `@pytest.mark.requires_live_project`. Run with:
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest tests/operations/test_issue334_guid_parse_formatexception_live.py \
#           -m requires_live_project -q
#
#   Follows the tests/operations/test_target_live_smoke.py template.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_334_"


class TestCatalogSourcedGuidRaisesFpParameterError:
    """
    Ruling item 1: a CatalogEntry with a malformed/empty guid reaching
    CatalogBackedMixin._create_from_entry must raise FP_ParameterError,
    not a raw CLR System.FormatException / System.ArgumentNullException.

    PhonFeatureOperations uses the mixin's _create_from_entry unmodified
    for feature-level (top-level) creation -- only the value-child
    creation (_CreateValueFromEntry) is overridden locally -- so this is
    a direct, non-mocked exercise of the exact production code path at
    Shared/catalog_backed.py:479.
    """

    @pytest.mark.live_phase("PhonFeatureOperations", "add")
    def test_empty_catalog_guid_raises_fp_parameter_error(self, target_sandbox):
        from flexicon.code.FLExProject import FP_ParameterError
        from flexicon.code.Shared.catalog import CatalogEntry

        ops = target_sandbox.PhonFeatures
        parent_obj = ops._get_root_list()

        entry = CatalogEntry(
            id=f"{TEST_PREFIX}malformed_feature",
            guid="",  # malformed: System.Guid("") raises FormatException
            abbrev={},
            term={},
            def_={},
        )

        with pytest.raises(FP_ParameterError) as excinfo:
            ops._create_from_entry(entry, parent_obj, set(), [])

        # The raw CLR type must not have escaped -- it is wrapped, and
        # preserved as __cause__ for debuggability (same contract as #262).
        import System

        assert excinfo.value.__cause__ is not None
        assert isinstance(
            excinfo.value.__cause__,
            (System.FormatException, System.ArgumentNullException),
        )
        # Message names the offending entry and frames it as catalog data,
        # not caller error.
        assert entry.id in str(excinfo.value)

    @pytest.mark.live_phase("PhonFeatureOperations", "add")
    def test_malformed_catalog_guid_does_not_mark_undo_stack(self, target_sandbox):
        """
        Ruling item 4: the raise must happen BEFORE
        `with self._TransactionCM(...)` opens, so a malformed catalog
        entry never marks the undo stack.

        Observed via LCM's own IActionHandler (project.project
        .ActionHandlerAccessor), the same accessor _TransactionCM itself
        reads (flexicon/code/transaction.py:121, :186). CurrentDepth must
        return to its pre-call value (no leaked open transaction) and
        UndoableSequenceCount (the count of completed undo tasks) must be
        unchanged (no undo task was ever pushed).

        NOTE: this assertion has not been run against a live project as
        part of this change -- see the task's live-verification report.
        If UndoableSequenceCount is not the correct/available member on
        this LCM build's IActionHandler, this test will fail with an
        AttributeError at the accessor read, not a false pass; do not
        weaken the assertion to make that failure disappear.
        """
        from flexicon.code.FLExProject import FP_ParameterError
        from flexicon.code.Shared.catalog import CatalogEntry

        ops = target_sandbox.PhonFeatures
        parent_obj = ops._get_root_list()
        action_handler = target_sandbox.project.ActionHandlerAccessor

        depth_before = action_handler.CurrentDepth
        undo_count_before = action_handler.UndoableSequenceCount

        entry = CatalogEntry(
            id=f"{TEST_PREFIX}malformed_feature_undo_check",
            guid="not-a-guid",
            abbrev={},
            term={},
            def_={},
        )

        with pytest.raises(FP_ParameterError):
            ops._create_from_entry(entry, parent_obj, set(), [])

        assert action_handler.CurrentDepth == depth_before, (
            "CurrentDepth changed -- a transaction was left open by the "
            "malformed-Guid raise."
        )
        assert action_handler.UndoableSequenceCount == undo_count_before, (
            "UndoableSequenceCount changed -- an undo task was pushed for "
            "a malformed catalog Guid that should have raised before the "
            "transaction ever opened."
        )


class TestApplySyncablePropertiesMalformedGuid:
    """
    Ruling item 2: ApplySyncableProperties, given a hand-built props dict
    carrying a malformed "Guid" for a co-created value, must raise
    FP_ParameterError -- exercising
    PhonFeatureOperations.__CreateValueWithGuid via its only public
    entry point.
    """

    @pytest.mark.live_phase("PhonFeatureOperations", "add")
    def test_malformed_value_guid_in_props_raises_fp_parameter_error(
        self, target_sandbox
    ):
        from flexicon.code.FLExProject import FP_ParameterError

        ops = target_sandbox.PhonFeatures
        anal_ws = next(
            iter(ws.Id for ws in target_sandbox.WritingSystems.GetAll())
        )

        feat = ops.Create(
            name=f"{TEST_PREFIX}shell_feature", abbreviation="t334"
        )
        try:
            props = {
                "Name": {anal_ws: f"{TEST_PREFIX}shell_feature"},
                "Values": [
                    {
                        "Guid": "not-a-guid",
                        "Name": {anal_ws: "bogus"},
                        "Abbreviation": {anal_ws: "x"},
                    }
                ],
            }

            with pytest.raises(FP_ParameterError) as excinfo:
                ops.ApplySyncableProperties(feat, props)

            import System

            assert excinfo.value.__cause__ is not None
            assert isinstance(
                excinfo.value.__cause__,
                (System.FormatException, System.ArgumentNullException),
            )
        finally:
            ops.Delete(feat)


class TestValidCatalogGuidStillImports:
    """
    Ruling item 3: the non-error path must be unaffected -- a
    well-formed catalog GUID still imports correctly. Reads the result
    back from the LCM rather than trusting the value just passed in.
    """

    @pytest.mark.live_phase("PhonFeatureOperations", "add")
    def test_valid_catalog_guid_still_creates_feature(self, target_sandbox):
        ops = target_sandbox.PhonFeatures

        feat = ops.CreateFromCatalog("PHON:fPAConsonantal")
        try:
            assert feat is not None

            # Read back from the LCM: re-fetch by GUID rather than
            # asserting on the object still held in `feat`.
            reread = target_sandbox.Object(feat.Guid)
            assert reread is not None
            assert str(reread.Guid).lower() == str(feat.Guid).lower()

            # A second CreateFromCatalog call for the same source_id must
            # be idempotent (pre-existing contract, unaffected by this fix).
            second = ops.CreateFromCatalog("PHON:fPAConsonantal")
            assert str(second.Guid).lower() == str(feat.Guid).lower()
        finally:
            # CreateFromCatalog features are owned by PhFeatureSystemOA;
            # delete via the feature system's collection directly since
            # this feature was not created through ops.Create().
            feature_system = ops._get_root_list()
            feature_system.FeaturesOC.Remove(feat)
