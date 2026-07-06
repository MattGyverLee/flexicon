#
#   test_phonemes.py
#
#   Class: TestPhonemeOperationsCreateRegression
#          Phase 2 regression tests for PhonemeOperations.Create — guards
#          against the orphan-NPE bug closed by issue #6 where a freshly
#          created IPhPhoneme had `.Name.set_String(...)` called on it
#          before the phoneme was attached to its owning collection. LCM
#          forbids setting properties on an orphan object; the fix in
#          PhonemeOperations.py moves `phoneme_set.PhonemesOC.Add(...)`
#          ahead of the Name assignment.
#
#          Reproducer:
#              phoneme = project.Phonemes.Create("o")    # ASCII; NFD
#                                                        # normalization is
#                                                        # a separate Phase
#                                                        # 3 concern.
#              assert project.Phonemes.GetRepresentation(phoneme) == "o"
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-LCM project fixture (matches the Phase 1 pattern from
# tests/test_flexproject_discoverability.py)
# ---------------------------------------------------------------------------

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_project(write_enabled):
    """
    Attempt to open one of the standard test projects.

    Returns the open FLExProject on success, or None if no FieldWorks
    project is reachable. Caller is responsible for CloseProject().
    """
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=write_enabled)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    """
    Module-scoped fixture providing an open, write-enabled FLExProject.

    Skips dependent tests if SIL.LCModel isn't loaded or no candidate
    FieldWorks project can be opened in write mode.
    """
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_project(write_enabled=True)
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------


class TestPhonemeOperationsCreateRegression:
    """
    Regression coverage for issue #6: PhonemeOperations.Create() must attach
    the new phoneme to phoneme_set.PhonemesOC before setting Name, otherwise
    LCM raises a NullReferenceException ("orphan NPE") because property
    writes on unowned objects are not permitted.
    """

    def test_create_does_not_npe(self, writable_project):
        """
        Issue #6 reproducer: creating a phoneme with ASCII representation
        must succeed (no NPE) and round-trip its representation.

        Uses an ASCII character so this test is decoupled from NFD/Unicode
        normalization concerns, which belong to Phase 3.
        """
        # Use a representation that's extremely unlikely to clash with
        # existing phoneme inventory. If it does, the Create() call will
        # raise FP_ParameterError("Phoneme '...' already exists") and we
        # adapt by deleting first.
        representation = "qZ_phase2_regression"

        # Pre-clean: if a previous run left this phoneme behind, remove it
        # so the regression test starts from a clean slate.
        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        # Act: this is the call that previously NPE'd before the Phase 2
        # fix (set_String on an orphan phoneme).
        phoneme = writable_project.Phonemes.Create(representation)

        try:
            # Assert: returned object is non-None and its representation
            # round-trips through GetRepresentation.
            assert phoneme is not None, (
                "Create() returned None instead of an IPhPhoneme"
            )
            assert writable_project.Phonemes.GetRepresentation(phoneme) == (
                representation
            ), (
                "Phoneme representation did not round-trip after Create() — "
                "fix did not preserve Name assignment after owner Add"
            )
        finally:
            # Clean up: delete the phoneme so re-running the suite is
            # idempotent.
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass


class TestPhonemeFindNFDRegression:
    """
    Regression coverage for issue #9/#10: Find()/Exists() must succeed
    when the user supplies an NFC-encoded query against a phoneme whose
    Representation FLEx stored in NFD. Without the Phase 3
    `normalize_match_key()` helper, Find('ö') silently returned None
    even though Create('ö') had just produced the phoneme.

    Uses the writable_project fixture above (module-scoped). The
    fixture does NOT roll back changes — the test creates a phoneme
    with a unique representation, runs Find against it, then deletes
    it in a finally block so re-runs are idempotent.
    """

    def test_find_finds_nfc_input_for_nfd_stored_diacritic(
        self, writable_project
    ):
        """
        Reproducer from MattGyverLee/flexlibs#10:
            phoneme = project.Phonemes.Create('ö')   # NFC input
            found   = project.Phonemes.Find('ö')     # NFC query
        Before Phase 3 the Find() call returned None because FLEx
        stores the Representation in NFD and the lookup compared raw
        bytes.

        We use 'ö' (NFC, single codepoint U+00F6) as the round-trip
        sentinel — the canonical case from the issue report.
        """
        representation = "ö"  # NFC: precomposed o-with-diaeresis

        # Pre-clean: if a previous run left this phoneme behind, remove
        # it so the regression test starts from a known state. Use the
        # post-fix Find so cleanup itself doesn't depend on the bug.
        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        # Act
        phoneme = writable_project.Phonemes.Create(representation)

        try:
            assert phoneme is not None, (
                "Create('ö') returned None — Phase 2 fix regression?"
            )

            # Issue #10 core assertion: Find must locate the just-created
            # phoneme even though Python's 'ö' is NFC and FLEx storage
            # is NFD.
            found = writable_project.Phonemes.Find(representation)

            assert found is not None, (
                "Find('ö') returned None — NFD normalization helper is "
                "not being applied to Phonemes.Find (issue #10)"
            )
            assert found.Hvo == phoneme.Hvo, (
                "Find('ö') returned the wrong phoneme — "
                f"got Hvo={found.Hvo}, expected Hvo={phoneme.Hvo}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass


class TestPhonemeIPAOperations:
    """
    Phase 5c coverage for the additive IPA-related setters/finders on
    PhonemeOperations: SetBasicIPASymbol, FindCode, ReplaceCode.

    These tests use the module-scoped writable_project fixture (shared
    above). Each test creates its own throw-away phoneme with a unique
    representation and cleans up in a `finally` block so re-running the
    suite is idempotent against a live FieldWorks project.
    """

    # ---------------------------------------------------------------
    # SetBasicIPASymbol
    # ---------------------------------------------------------------

    def test_set_basic_ipa_symbol_writes_round_trip(self, writable_project):
        """SetBasicIPASymbol -> GetBasicIPASymbol round-trips."""
        representation = "qZ_ipa_set_roundtrip"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            writable_project.Phonemes.SetBasicIPASymbol(phoneme, "ɯ")

            ws = writable_project.project.DefaultVernWs
            got = writable_project.Phonemes.GetBasicIPASymbol(phoneme, ws)
            assert got == "ɯ", (
                f"SetBasicIPASymbol round-trip failed: expected 'ɯ', "
                f"got {got!r}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    def test_set_basic_ipa_symbol_handles_combined_diacritic(
        self, writable_project
    ):
        """
        Defensive: set a precomposed-diacritic NFC string ("ö") via
        SetBasicIPASymbol and verify GetBasicIPASymbol returns the
        same Python string. FW may store as NFD internally; the
        getter/setter pair must round-trip the user's view.
        """
        representation = "qZ_ipa_set_diacritic"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            writable_project.Phonemes.SetBasicIPASymbol(phoneme, "ö")

            ws = writable_project.project.DefaultVernWs
            got = writable_project.Phonemes.GetBasicIPASymbol(phoneme, ws)
            # Storage may normalise NFD; both NFC and NFD should be
            # acceptable round-trips. We assert *content equivalence*
            # after Unicode normalisation rather than byte equality.
            import unicodedata
            assert unicodedata.normalize("NFC", got) == "ö", (
                f"SetBasicIPASymbol('ö') round-trip failed: got {got!r}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    def test_set_basic_ipa_symbol_explicit_ws(self, writable_project):
        """
        Passing wsHandle=<vern handle> explicitly must write to that
        WS — read back with the same handle and the value must match.
        """
        representation = "qZ_ipa_set_explicit_ws"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            ws = writable_project.project.DefaultVernWs

            writable_project.Phonemes.SetBasicIPASymbol(
                phoneme, "ʃ", wsHandle=ws
            )

            got = writable_project.Phonemes.GetBasicIPASymbol(phoneme, ws)
            assert got == "ʃ", (
                f"SetBasicIPASymbol(wsHandle={ws}) round-trip failed: "
                f"got {got!r}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    # ---------------------------------------------------------------
    # FindCode
    # ---------------------------------------------------------------

    def test_find_code_returns_existing(self, writable_project):
        """
        After AddCode("[tʰ]"), FindCode(phoneme, "[tʰ]") must return
        an IPhCode whose Hvo matches the code we just added.
        """
        representation = "qZ_findcode_existing"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            added = writable_project.Phonemes.AddCode(phoneme, "[tʰ]")

            found = writable_project.Phonemes.FindCode(phoneme, "[tʰ]")
            assert found is not None, (
                "FindCode returned None for code that was just added"
            )
            assert found.Hvo == added.Hvo, (
                f"FindCode returned wrong code: got Hvo={found.Hvo}, "
                f"expected Hvo={added.Hvo}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    def test_find_code_returns_none_for_missing(self, writable_project):
        """
        FindCode for a representation that doesn't exist on the
        phoneme must return None (not raise).
        """
        representation = "qZ_findcode_missing"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            result = writable_project.Phonemes.FindCode(
                phoneme, "nonexistent_code_repr"
            )
            assert result is None, (
                f"FindCode for missing repr should return None, got "
                f"{result!r}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    def test_find_code_nfd_safe(self, writable_project):
        """
        Phase 3 regression for codes: AddCode with NFC input (single
        codepoint "ö" U+00F6) must still be findable via FindCode with
        the same NFC input even though FLEx storage may be NFD.
        Mirrors the Phonemes.Find NFD-safety guarantee from issue #10.
        """
        representation = "qZ_findcode_nfd_safe"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            # NFC input. "ö" is a single-codepoint precomposed form;
            # FLEx may store it decomposed as "o" + U+0308.
            added = writable_project.Phonemes.AddCode(phoneme, "ö")

            found = writable_project.Phonemes.FindCode(phoneme, "ö")
            assert found is not None, (
                "FindCode('ö' NFC) returned None — NFD normalisation "
                "is not applied to code lookup"
            )
            assert found.Hvo == added.Hvo, (
                f"FindCode returned wrong code: got Hvo={found.Hvo}, "
                f"expected Hvo={added.Hvo}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    # ---------------------------------------------------------------
    # ReplaceCode
    # ---------------------------------------------------------------

    def test_replace_code_swaps_representation(self, writable_project):
        """
        AddCode("[a]"), then ReplaceCode("[a]", "[b]"). After the swap
        FindCode("[b]") must return the new code, and FindCode("[a]")
        must return None.
        """
        representation = "qZ_replacecode_swap"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            writable_project.Phonemes.AddCode(phoneme, "[a]")

            new_code = writable_project.Phonemes.ReplaceCode(
                phoneme, "[a]", "[b]"
            )

            assert new_code is not None, (
                "ReplaceCode returned None instead of the new IPhCode"
            )

            found_new = writable_project.Phonemes.FindCode(phoneme, "[b]")
            assert found_new is not None, (
                "FindCode('[b]') returned None after ReplaceCode"
            )
            assert found_new.Hvo == new_code.Hvo, (
                f"FindCode found wrong code: got Hvo={found_new.Hvo}, "
                f"expected new Hvo={new_code.Hvo}"
            )

            found_old = writable_project.Phonemes.FindCode(phoneme, "[a]")
            assert found_old is None, (
                f"Old code '[a]' was not removed by ReplaceCode: "
                f"found Hvo={found_old.Hvo if found_old else None}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    def test_replace_code_raises_when_old_not_found(self, writable_project):
        """
        ReplaceCode for a string old_code_or_repr that isn't present
        on the phoneme must raise FP_ParameterError (not silently
        AddCode the new value).
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        representation = "qZ_replacecode_missing"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)
        try:
            with pytest.raises(FP_ParameterError):
                writable_project.Phonemes.ReplaceCode(
                    phoneme, "nonexistent_code_repr", "[x]"
                )

            # And the phoneme must not have grown a "[x]" code as a
            # side effect of the failed replace.
            assert (
                writable_project.Phonemes.FindCode(phoneme, "[x]") is None
            ), (
                "ReplaceCode unexpectedly added the new code even though "
                "the old code was missing"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass


class TestPhonemeAddCodePlaceholderRegression:
    """
    Regression coverage for issue #17: PhonemeOperations.Create leaves a
    stray '***' IPhCode (FLEX null marker) on the phoneme. AddCode used
    to always append a new IPhCode, so every wrapper-created phoneme
    ended up carrying a junk placeholder code that broke HermitCrab
    parser loading.

    The Option B fix in AddCode reuses the autocreated placeholder code
    when the phoneme has exactly one code and its representation in the
    target WS is empty or '***'. Subsequent AddCode calls append
    normally, so multi-code workflows still behave.
    """

    def test_add_code_reuses_placeholder_on_first_call(self, writable_project):
        """
        Direct reproducer from the issue:
            ch = project.Phonemes.Create("ch")
            project.Phonemes.AddCode(ch, "ch")
            project.Phonemes.AddCode(ch, "Ch")
            project.Phonemes.AddCode(ch, "CH")
            # codes must be exactly 3 ("ch", "Ch", "CH"), not 4
            # (no '***' placeholder code leaking through).
        """
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        representation = "qZ_add_code_placeholder"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)

        try:
            # Apply the issue's repro pattern.
            writable_project.Phonemes.AddCode(phoneme, "ch")
            writable_project.Phonemes.AddCode(phoneme, "Ch")
            writable_project.Phonemes.AddCode(phoneme, "CH")

            ws = writable_project.project.DefaultVernWs
            codes = writable_project.Phonemes.GetCodes(phoneme)
            reprs = [
                ITsString(c.Representation.get_String(ws)).Text or ""
                for c in codes
            ]

            # Core assertion: exactly 3 codes, all user-provided.
            assert len(codes) == 3, (
                f"Expected 3 codes after 3 AddCode calls, got {len(codes)}: "
                f"{reprs!r}. The placeholder code wasn't reused (issue #17)."
            )

            # No placeholder leaked through.
            assert "***" not in reprs, (
                f"Stray '***' placeholder code found: {reprs!r}"
            )
            assert "" not in reprs, (
                f"Stray empty-representation code found: {reprs!r}"
            )

            # All three user-provided reprs are present.
            assert set(reprs) == {"ch", "Ch", "CH"}, (
                f"Code representations don't match input: {reprs!r}"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass

    def test_add_code_appends_when_phoneme_already_has_real_codes(
        self, writable_project
    ):
        """
        When the phoneme already has at least one real code, subsequent
        AddCode calls must append rather than overwrite — even when the
        single existing code happens to look empty. The reuse heuristic
        only fires for the LCM-autogenerated placeholder pattern.
        """
        representation = "qZ_add_code_append"

        existing = writable_project.Phonemes.Find(representation)
        if existing is not None:
            writable_project.Phonemes.Delete(existing)

        phoneme = writable_project.Phonemes.Create(representation)

        try:
            # First AddCode reuses placeholder => 1 code with 'first'.
            first = writable_project.Phonemes.AddCode(phoneme, "first")
            codes_after_first = writable_project.Phonemes.GetCodes(phoneme)
            assert len(codes_after_first) == 1, (
                f"After first AddCode: expected 1 code, "
                f"got {len(codes_after_first)} - placeholder reuse failed"
            )

            # Second AddCode must append => 2 codes total.
            second = writable_project.Phonemes.AddCode(phoneme, "second")
            codes_after_second = writable_project.Phonemes.GetCodes(phoneme)
            assert len(codes_after_second) == 2, (
                f"After second AddCode: expected 2 codes, "
                f"got {len(codes_after_second)} - append path broken"
            )
            assert first.Hvo != second.Hvo, (
                "AddCode returned same code object twice; second call "
                "should have created a distinct IPhCode"
            )
        finally:
            try:
                writable_project.Phonemes.Delete(phoneme)
            except Exception:
                pass


class TestPhonemeSync:
    """
    Live-LCM coverage for PhonemeOperations.GetSyncableProperties /
    ApplySyncableProperties (issue #222).

    Covers the ITsString.get_String crash fix (guarded multistring read,
    including BasicIPASymbol's variant shape) and the FeaturesOA
    feature-value specs that let a synced phoneme carry its phonological
    features.
    """

    def test_getsyncable_does_not_crash(self, writable_project):
        """
        GetSyncableProperties must return a dict without raising, even when
        BasicIPASymbol is present (the scalar-shape read previously crashed
        inside ITsString.get_String).
        """
        ops = writable_project.Phonemes
        phoneme = ops.Create("/zzsync/")
        try:
            ops.SetBasicIPASymbol(phoneme, "z")
            props = ops.GetSyncableProperties(phoneme)
            assert isinstance(props, dict)
            assert "Name" in props
            # BasicIPASymbol round-trips into the props as a ws->text dict.
            assert props.get("BasicIPASymbol")
        finally:
            try:
                ops.Delete(phoneme)
            except Exception:
                pass

    def test_getsyncable_surfaces_feature_specs(self, writable_project):
        """
        A phoneme with a FeaturesOA feature structure must surface its
        (feature, value) specs as GUID pairs under 'Features'.
        """
        feat_ops = writable_project.PhonFeatures
        ph_ops = writable_project.Phonemes

        feat = feat_ops.CreateFromCatalog("PHON:fPAConsonantal")
        feat_guid = str(feat.Guid)
        plus = next(
            v for v in feat_ops.GetValues(feat)
            if feat_ops.GetAbbreviation(v) == "+"
        )
        value_guid = str(plus.Guid)

        phoneme = ph_ops.Create("/zzfeat/")
        try:
            feat_ops.MakeFeatStruc([(feat, plus)], owner=phoneme)

            props = ph_ops.GetSyncableProperties(phoneme)
            assert "FeaturesGuid" in props
            assert "Features" in props, "Feature specs missing"
            pairs = {
                (s["FeatureGuid"].lower(), s["ValueGuid"].lower())
                for s in props["Features"]
            }
            assert (feat_guid.lower(), value_guid.lower()) in pairs
        finally:
            try:
                ph_ops.Delete(phoneme)
            except Exception:
                pass
            try:
                writable_project.PhonFeatures.Delete(feat)
            except Exception:
                pass

    def test_apply_rewires_feature_specs(self, writable_project):
        """
        ApplySyncableProperties must rewire Features specs against the
        target project's feature system by GUID, so the applied phoneme
        carries the feature value.
        """
        feat_ops = writable_project.PhonFeatures
        ph_ops = writable_project.Phonemes

        feat = feat_ops.CreateFromCatalog("PHON:fPAConsonantal")
        feat_guid = str(feat.Guid)
        plus = next(
            v for v in feat_ops.GetValues(feat)
            if feat_ops.GetAbbreviation(v) == "+"
        )
        value_guid = str(plus.Guid)

        anal_ws = next(iter(
            ws.Id for ws in writable_project.WritingSystems.GetAll()
        ))
        src_props = {
            "Name": {anal_ws: "/zzapply/"},
            "Features": [
                {"FeatureGuid": feat_guid, "ValueGuid": value_guid},
            ],
        }

        phoneme = ph_ops.Create("/zzapply-shell/")
        try:
            ph_ops.ApplySyncableProperties(phoneme, src_props)

            props_back = ph_ops.GetSyncableProperties(phoneme)
            pairs = {
                (s["FeatureGuid"].lower(), s["ValueGuid"].lower())
                for s in props_back.get("Features", [])
            }
            assert (feat_guid.lower(), value_guid.lower()) in pairs, (
                "Feature spec was not rewired onto the target phoneme"
            )
        finally:
            try:
                ph_ops.Delete(phoneme)
            except Exception:
                pass
            try:
                writable_project.PhonFeatures.Delete(feat)
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
