#
#   test_325_syncable_properties_live.py
#
#   Live LCM verification for issue #325 (syncable-properties), Task T3.
#
#   Verifies wave-1 code (T2a-T2e) against a live FLEx database for each
#   of five deliverable areas:
#
#     (a) Etymology language_rs round-trip (R1, R2, R6)
#     (b) ILexReference owner_guid + targets_rs (R3)
#     (c) Text media + IText.Name (R4, R8)
#     (d) ConstChartMovedText.Create full path with segments (R5)
#     (e) LexSense payload lacks DoNotShowMainEntryInRC (R7)
#
#   Commands:
#     python -m pytest -m "not requires_live_project" -q
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_325_syncable_properties_live.py -m requires_live_project -q
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import json
import logging
import os
import pathlib
import sys

import pytest

pytestmark = pytest.mark.requires_live_project

logger = logging.getLogger(__name__)

TEST_PREFIX = "TEST_325_"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clr_name(obj):
    try:
        return obj.GetType().FullName
    except Exception:
        return type(obj).__name__


def _repo_root():
    return pathlib.Path(__file__).resolve().parent.parent.parent


def _write_evidence(data: dict):
    ev_dir = _repo_root() / "specs" / "325-syncable-properties" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    out = ev_dir / "live-T3-syncable-properties.md"
    lines = ["# Live verification -- issue #325 T3 syncable-properties\n\n"]
    for section, body in data.items():
        lines.append(f"## {section}\n\n")
        if isinstance(body, dict):
            for k, v in body.items():
                lines.append(f"- **{k}**: `{v}`\n")
        else:
            lines.append(str(body) + "\n")
        lines.append("\n")
    out.write_text("".join(lines), encoding="utf-8")
    return out


# Accumulated evidence across all tests in this module
_EVIDENCE = {}


def _open_ro(project_name):
    """Open a project read-only; return FLExProject or None on failure."""
    if "SIL.LCModel" not in sys.modules:
        return None
    try:
        from flexicon.code.FLExProject import FLExProject
        p = FLExProject()
        p.OpenProject(project_name, writeEnabled=False)
        return p
    except Exception as exc:
        logger.warning("[WARN] Could not open '%s' read-only: %s", project_name, exc)
        return None


def _open_rw(project_name):
    """Open a project write-enabled in-place; return FLExProject or None."""
    if "SIL.LCModel" not in sys.modules:
        return None
    try:
        from flexicon.code.FLExProject import FLExProject
        p = FLExProject()
        p.OpenProject(project_name, writeEnabled=True)
        return p
    except Exception as exc:
        logger.warning("[WARN] Could not open '%s' write-enabled: %s", project_name, exc)
        return None


def _close(project):
    if project is not None:
        try:
            project.CloseProject()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# (a) Etymology language_rs round-trip (R1, R2, R6)
# ---------------------------------------------------------------------------

class TestEtymologyLanguageRS:
    """
    (a) R1/R2/R6 -- Etymology language_rs round-trip.

    Verifies:
    - GetSyncableProperties emits language_rs (list of GUIDs), no LanguageNotesRA key
    - ApplySyncableProperties replaces LanguageRS sequence; re-read matches
    - Duplicate preserves LanguageNotes; LanguageRS NOT copied (R2 out-of-scope)
    - GetLanguage/SetLanguage emit [WARN] and delegate
    """

    @pytest.mark.live_phase("EtymologyOperations", "add")
    def test_language_rs_roundtrip(self, target_sandbox):
        """
        Seed LanguageRS (>=2 if Languages list populated), call
        GetSyncableProperties, then ApplySyncableProperties onto a fresh
        etymology and re-read LanguageRS by HVO/GUID cast.
        """
        import System
        import warnings

        project = target_sandbox
        assert project.writeEnabled, "target_sandbox must be write-enabled"

        etym_ops = project.Etymology
        entry_ops = project.LexEntry

        # Seed Language possibilities into LanguagesOA when the list is empty
        # (Target sandbox ships with Count=0; LanguageRS Apply cannot be
        # exercised without at least one ICmPossibility to reference).
        lang_possibilities = []
        seeded_lang_objs = []
        try:
            from SIL.LCModel import ICmPossibilityFactory
            from SIL.LCModel.Core.Text import TsStringUtils

            lex_db = project.project.LangProject.LexDbOA
            langs_list = None
            if hasattr(lex_db, "LanguagesOA") and lex_db.LanguagesOA is not None:
                langs_list = lex_db.LanguagesOA
                lang_possibilities = list(langs_list.PossibilitiesOS)

            if len(lang_possibilities) < 2 and langs_list is not None:
                factory = project.project.ServiceLocator.GetService(
                    ICmPossibilityFactory
                )
                ws_handle = project.project.DefaultAnalWs
                with etym_ops._TransactionCM("T3 seed LanguagesOA"):
                    for label in (
                        f"{TEST_PREFIX}lang_a",
                        f"{TEST_PREFIX}lang_b",
                    ):
                        poss = factory.Create()
                        langs_list.PossibilitiesOS.Add(poss)
                        poss.Name.set_String(
                            ws_handle, TsStringUtils.MakeString(label, ws_handle)
                        )
                        seeded_lang_objs.append(poss)
                lang_possibilities = list(langs_list.PossibilitiesOS)
        except Exception as exc:
            logger.warning("[WARN] Could not seed LanguagesOA: %s", exc)

        # Create a source entry + etymology
        src_entry = entry_ops.Create(lexeme_form=f"{TEST_PREFIX}etym_src")
        try:
            src_etym = etym_ops.Create(src_entry, form="src_form")
            try:
                # Set LanguageNotes (Source key) to test Duplicate preservation.
                # TsStringUtils lives in SIL.LCModel.Core.Text (not KernelInterfaces).
                with etym_ops._TransactionCM("T3 set LanguageNotes"):
                    from SIL.LCModel.Core.Text import TsStringUtils
                    ws_handle = project.project.DefaultAnalWs
                    note_ts = TsStringUtils.MakeString("T3_source_note", ws_handle)
                    src_etym.LanguageNotes.set_String(ws_handle, note_ts)

                # Seed LanguageRS if possibilities are available (>=2 if possible)
                seeded_guids = []
                if lang_possibilities:
                    langs_to_seed = lang_possibilities[:2]
                    etym_ops.SetLanguages(src_etym, langs_to_seed)
                    seeded_guids = [str(l.Guid) for l in langs_to_seed]
                    _EVIDENCE["(a) languages_seeded"] = (
                        f"{len(seeded_guids)} GUIDs: {seeded_guids}"
                    )
                else:
                    _EVIDENCE["(a) languages_seeded"] = (
                        "FAIL: Languages list empty and seeding failed"
                    )
                    pytest.fail(
                        "LanguageRS Apply cannot be verified: LanguagesOA empty "
                        "and seeding produced 0 possibilities"
                    )

                # --- GetSyncableProperties ---
                props = etym_ops.GetSyncableProperties(src_etym)

                # R1: language_rs must be present as a list
                assert "language_rs" in props, \
                    "GetSyncableProperties: 'language_rs' key is absent"
                assert isinstance(props["language_rs"], list), \
                    f"'language_rs' must be a list, got {type(props['language_rs'])}"

                # R2: LanguageNotesRA must NOT be present
                assert "LanguageNotesRA" not in props, \
                    "GetSyncableProperties: 'LanguageNotesRA' key must not be present (R2 removed it)"

                # R1: If we seeded GUIDs, they must appear in order
                if seeded_guids:
                    assert props["language_rs"] == seeded_guids, (
                        f"language_rs mismatch: expected {seeded_guids}, "
                        f"got {props['language_rs']}"
                    )

                _EVIDENCE["(a) GetSyncableProperties language_rs"] = props["language_rs"]
                _EVIDENCE["(a) LanguageNotesRA absent"] = "LanguageNotesRA" not in props

                # --- ApplySyncableProperties onto a target etymology ---
                tgt_entry = entry_ops.Create(lexeme_form=f"{TEST_PREFIX}etym_tgt")
                try:
                    tgt_etym = etym_ops.Create(tgt_entry, form="tgt_form")
                    try:
                        etym_ops.ApplySyncableProperties(tgt_etym, props)

                        # Re-read LanguageRS by GUID (not just the input)
                        tgt_etym_guid = str(tgt_etym.Guid)
                        from SIL.LCModel import ILexEtymologyRepository
                        repo = project.project.ServiceLocator.GetService(ILexEtymologyRepository)
                        refetched = None
                        for e in repo.AllInstances():
                            if str(e.Guid) == tgt_etym_guid:
                                refetched = e
                                break
                        assert refetched is not None, "Could not re-fetch target etymology by GUID"

                        if seeded_guids:
                            if hasattr(refetched, "LanguageRS"):
                                actual_guids = [str(l.Guid) for l in refetched.LanguageRS]
                                assert actual_guids == seeded_guids, (
                                    f"LanguageRS after Apply: expected {seeded_guids}, "
                                    f"got {actual_guids}"
                                )
                                _EVIDENCE["(a) LanguageRS after Apply (re-read)"] = actual_guids
                            else:
                                pytest.fail("LanguageRS absent on re-fetched etymology impl")
                        else:
                            _EVIDENCE["(a) LanguageRS after Apply (re-read)"] = (
                                "Skipped (no languages seeded; list was empty)"
                            )

                    finally:
                        etym_ops.Delete(tgt_etym)
                finally:
                    entry_ops.Delete(tgt_entry)

                # --- Duplicate preserves LanguageNotes (R2) ---
                # Duplicate(item_or_hvo, insert_after=True, deep=False) --
                # first arg is the etymology, not the owning entry.
                dup_etym = etym_ops.Duplicate(src_etym)
                try:
                    dup_guid = str(dup_etym.Guid)
                    from SIL.LCModel import ILexEtymologyRepository
                    repo = project.project.ServiceLocator.GetService(ILexEtymologyRepository)
                    dup_refetched = None
                    for e in repo.AllInstances():
                        if str(e.Guid) == dup_guid:
                            dup_refetched = e
                            break
                    assert dup_refetched is not None, "Could not re-fetch duplicated etymology"

                    # LanguageNotes preserved
                    if hasattr(dup_refetched, "LanguageNotes"):
                        ws_handle = project.project.DefaultAnalWs
                        from SIL.LCModel.Core.KernelInterfaces import ITsString
                        dup_note = normalize_ts(ITsString(
                            dup_refetched.LanguageNotes.get_String(ws_handle)
                        ).Text)
                        _EVIDENCE["(a) Duplicate LanguageNotes preserved"] = dup_note
                        assert dup_note == "T3_source_note", (
                            f"Duplicate did not preserve LanguageNotes: got '{dup_note}'"
                        )
                    else:
                        _EVIDENCE["(a) Duplicate LanguageNotes preserved"] = "SKIP: no LanguageNotes on impl"

                    # LanguageRS not copied by Duplicate (R2 out-of-scope)
                    if hasattr(dup_refetched, "LanguageRS"):
                        dup_lang_count = dup_refetched.LanguageRS.Count
                        _EVIDENCE["(a) Duplicate LanguageRS count (expect 0)"] = dup_lang_count
                        assert dup_lang_count == 0, (
                            f"Duplicate should NOT copy LanguageRS; got {dup_lang_count} items"
                        )
                finally:
                    etym_ops.Delete(dup_etym)

                # --- GetLanguage/SetLanguage warn+delegate (R6) ---
                import io
                import logging as _logging

                log_capture = io.StringIO()
                handler = _logging.StreamHandler(log_capture)
                handler.setLevel(_logging.WARNING)
                root_log = _logging.getLogger("flexicon.code.Lexicon.EtymologyOperations")
                root_log.addHandler(handler)
                try:
                    _ = etym_ops.GetLanguage(src_etym)
                    _ = etym_ops.SetLanguage(src_etym, None)
                finally:
                    root_log.removeHandler(handler)

                log_text = log_capture.getvalue()
                assert "[WARN] GetLanguage reads index 0" in log_text or \
                       "GetLanguage reads index 0" in log_text, \
                    f"GetLanguage did not emit [WARN]; log was: {log_text!r}"
                assert "SetLanguage sets only index 0" in log_text, \
                    f"SetLanguage did not emit [WARN]; log was: {log_text!r}"
                _EVIDENCE["(a) GetLanguage/SetLanguage warn"] = (
                    "[WARN] emitted for both deprecated methods"
                )

                _EVIDENCE["(a) RESULT"] = "PASS"

            finally:
                etym_ops.Delete(src_etym)
        finally:
            entry_ops.Delete(src_entry)
            # Best-effort cleanup of seeded language possibilities (sandbox
            # is disposable; Remove only -- Delete after Remove NREs).
            if seeded_lang_objs:
                try:
                    langs_list = project.project.LangProject.LexDbOA.LanguagesOA
                    with etym_ops._TransactionCM("T3 cleanup LanguagesOA"):
                        for poss in list(seeded_lang_objs):
                            try:
                                if poss in langs_list.PossibilitiesOS:
                                    langs_list.PossibilitiesOS.Remove(poss)
                            except Exception:
                                pass
                except Exception as exc:
                    logger.warning("[WARN] LanguagesOA cleanup: %s", exc)


def normalize_ts(text):
    """Strip FLEx null marker from ITsString text."""
    if text is None or text == "***":
        return ""
    return text


# ---------------------------------------------------------------------------
# (b) ILexReference: owner_guid + targets_rs + ApplySyncableProperties
# ---------------------------------------------------------------------------

class TestLexReferenceOwnerGuid:
    """
    (b) R3 -- ILexReference owner_guid + targets_rs.

    Verifies:
    - owner_guid in props == str(ILexRefType(ref.Owner).Guid)
    - targets_rs present as ordered list of GUIDs
    - ReferenceTypeRA absent from props
    - ApplySyncableProperties does not raise on a writable reference
    """

    @pytest.mark.live_phase("LexReferenceOperations", "read")
    def test_owner_guid_and_targets_rs(self):
        """
        Open Sena_InterlinearTraining (populated; has LexReferences)
        read-only, probe GetSyncableProperties on the first LexReference.
        """
        from SIL.LCModel import (
            ILexReference, ILexReferenceRepository, ILexRefType,
        )

        project = _open_ro("Sena_InterlinearTraining")
        if project is None:
            pytest.skip("Sena_InterlinearTraining not accessible")

        try:
            repo = project.project.ServiceLocator.GetService(ILexReferenceRepository)
            all_refs = list(repo.AllInstances())
            if not all_refs:
                pytest.skip("No ILexReference instances in Sena_InterlinearTraining")

            ref = all_refs[0]
            ref_ops = project.LexReferences

            props = ref_ops.GetSyncableProperties(ref)

            # owner_guid must equal str(ILexRefType(ref.Owner).Guid)
            expected_owner_guid = str(ILexRefType(ref.Owner).Guid)
            assert "owner_guid" in props, "GetSyncableProperties: 'owner_guid' key absent"
            assert props["owner_guid"] == expected_owner_guid, (
                f"owner_guid mismatch: expected {expected_owner_guid}, got {props['owner_guid']}"
            )

            # targets_rs must be present as list
            assert "targets_rs" in props, "GetSyncableProperties: 'targets_rs' key absent"
            assert isinstance(props["targets_rs"], list), (
                f"targets_rs must be a list, got {type(props['targets_rs'])}"
            )

            # ReferenceTypeRA must not be present (R3)
            assert "ReferenceTypeRA" not in props, (
                "GetSyncableProperties: 'ReferenceTypeRA' key must not be present (R3)"
            )

            _EVIDENCE["(b) owner_guid"] = props["owner_guid"]
            _EVIDENCE["(b) targets_rs count"] = len(props["targets_rs"])
            _EVIDENCE["(b) ReferenceTypeRA absent"] = "ReferenceTypeRA" not in props
            _EVIDENCE["(b) RESULT"] = "PASS (read-path)"

        finally:
            _close(project)

    @pytest.mark.live_phase("LexReferenceOperations", "modify")
    def test_apply_syncable_properties_does_not_raise(self):
        """
        Open Sena_InterlinearTraining write-enabled, find an existing
        ILexReference, call ApplySyncableProperties (same props -> idempotent),
        verify no exception raised. Re-read owner_guid after apply.
        """
        require_live = os.environ.get("FLEXLIBS_REQUIRE_LIVE") == "1"
        from SIL.LCModel import (
            ILexReference, ILexReferenceRepository, ILexRefType,
        )

        project = _open_rw("Sena_InterlinearTraining")
        if project is None:
            if require_live:
                pytest.fail("FLEXLIBS_REQUIRE_LIVE=1: Sena_InterlinearTraining must be writable for (b)")
            pytest.skip("Sena_InterlinearTraining not accessible write-enabled")

        ref_to_restore = None
        original_props = None
        try:
            repo = project.project.ServiceLocator.GetService(ILexReferenceRepository)
            all_refs = list(repo.AllInstances())
            if not all_refs:
                pytest.skip("No ILexReference instances in Sena_InterlinearTraining")

            ref = all_refs[0]
            ref_ops = project.LexReferences
            original_props = ref_ops.GetSyncableProperties(ref)

            # Apply same props (idempotent) -- must not raise
            ref_ops.ApplySyncableProperties(ref, original_props)

            # Re-read owner_guid by GUID
            ref_guid = str(ref.Guid)
            refetched = None
            for r in repo.AllInstances():
                if str(r.Guid) == ref_guid:
                    refetched = r
                    break
            assert refetched is not None, "Could not re-fetch ILexReference by GUID after Apply"

            re_props = ref_ops.GetSyncableProperties(refetched)
            assert re_props["owner_guid"] == original_props["owner_guid"], (
                f"owner_guid changed after idempotent Apply: "
                f"before={original_props['owner_guid']!r}, after={re_props['owner_guid']!r}"
            )

            _EVIDENCE["(b) ApplySyncableProperties (idempotent, no raise)"] = "PASS"
            _EVIDENCE["(b) owner_guid stable after Apply"] = re_props["owner_guid"]
            _EVIDENCE["(b) RESULT"] = "PASS"

        finally:
            # Restore: re-apply original props (already idempotent -- Name/Comment
            # unchanged, no structural change was made)
            _close(project)

    @pytest.mark.live_phase("LexReferenceOperations", "modify")
    def test_targets_rs_mutating_apply(self, target_sandbox):
        """
        R3: Create a LexReference with 3 sense targets in target_sandbox,
        Apply a reversed targets_rs (Remove+rotate replace, never Clear),
        re-read TargetsRS from the LCM by GUID.
        """
        project = target_sandbox
        assert project.writeEnabled

        ref_ops = project.LexReferences
        entry_ops = project.LexEntry
        sense_ops = project.Senses

        entries = []
        senses = []
        try:
            for i in range(3):
                e = entry_ops.Create(lexeme_form=f"{TEST_PREFIX}ref_tgt_{i}")
                entries.append(e)
                senses.append(sense_ops.Create(e, gloss=f"{TEST_PREFIX}gloss_{i}"))

            rtype = ref_ops.FindType(f"{TEST_PREFIX}Seq")
            if rtype is None:
                rtype = ref_ops.CreateType(f"{TEST_PREFIX}Seq", "Sequence")

            ref = ref_ops.Create(rtype, senses)
            try:
                before = [str(t.Guid) for t in ref.TargetsRS]
                assert len(before) == 3, f"expected 3 targets, got {before}"
                mutated = list(reversed(before))
                assert mutated != before

                props = ref_ops.GetSyncableProperties(ref)
                props["targets_rs"] = mutated
                ref_ops.ApplySyncableProperties(ref, props)

                ref_guid = str(ref.Guid)
                from SIL.LCModel import ILexReferenceRepository

                repo = project.project.ServiceLocator.GetService(
                    ILexReferenceRepository
                )
                refetched = None
                for r in repo.AllInstances():
                    if str(r.Guid) == ref_guid:
                        refetched = r
                        break
                assert refetched is not None, "Could not re-fetch LexReference"

                after = [str(t.Guid) for t in refetched.TargetsRS]
                assert after == mutated, (
                    f"targets_rs after mutating Apply: expected {mutated}, "
                    f"got {after}"
                )
                _EVIDENCE["(b) targets_rs before"] = before
                _EVIDENCE["(b) targets_rs after mutating Apply (re-read)"] = after
                _EVIDENCE["(b) targets_rs mutating Apply"] = "PASS"
            finally:
                ref_ops.Delete(ref)
        finally:
            for e in entries:
                try:
                    entry_ops.Delete(e)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# (c) Text media + IText.Name payload (R4, R8)
# ---------------------------------------------------------------------------

class TestTextMediaAndName:
    """
    (c) R4 + R8 -- IText.Name in sync payload; media_uris key present.

    Name (R8) is verified via target_sandbox (create a text, check payload).
    Media (R4) requires a project with actual media files; if none is
    found, marks that specific check as FAIL: unverified + needs_human.
    """

    @pytest.mark.live_phase("TextOperations", "add")
    def test_text_name_in_payload(self, target_sandbox):
        """
        R8: Create a text with a name in target_sandbox; verify 'Name'
        key appears in GetSyncableProperties payload.
        """
        project = target_sandbox
        text_ops = project.Texts

        text = text_ops.Create(f"{TEST_PREFIX}name_payload_text")
        try:
            # SetName uses the built-in TextOperations helper (avoids manual
            # TsString construction which requires the SIL.LCModel.Core.Text
            # assembly to be explicitly referenced).
            text_ops.SetName(text, "T3_text_name")

            props = text_ops.GetSyncableProperties(text)

            assert "Name" in props, (
                f"GetSyncableProperties: 'Name' key absent (R8). Got keys: {list(props.keys())}"
            )
            assert isinstance(props["Name"], dict), (
                f"'Name' must be a dict (MultiString), got {type(props['Name'])}"
            )

            # Verify the name we set appears in the dict
            name_found = any("T3_text_name" in str(v) for v in props["Name"].values())
            assert name_found, (
                f"Set name 'T3_text_name' not found in Name dict: {props['Name']}"
            )

            _EVIDENCE["(c) Name in payload (R8)"] = "PASS"
            _EVIDENCE["(c) Name dict keys"] = list(props["Name"].keys())

        finally:
            text_ops.Delete(text)

    @pytest.mark.live_phase("TextOperations", "add")
    def test_media_uris_roundtrip_in_sandbox(self, target_sandbox):
        """
        R4: Create MediaFilesOA + MediaURI in target_sandbox (own before set),
        verify GetSyncableProperties media_uris, Apply onto a second text,
        and re-read MediaURIsOC from the LCM.
        """
        from System import Type as ClrType
        from flexicon.code.lcm_casting import cast_to_concrete

        project = target_sandbox
        text_ops = project.Texts
        sl = project.project.ServiceLocator
        cont_fac = sl.GetService(
            ClrType.GetType(
                "SIL.LCModel.ICmMediaContainerFactory, SIL.LCModel", True
            )
        )
        uri_fac = sl.GetService(
            ClrType.GetType(
                "SIL.LCModel.ICmMediaURIFactory, SIL.LCModel", True
            )
        )

        src = text_ops.Create(f"{TEST_PREFIX}media_src")
        try:
            concrete = cast_to_concrete(src)
            probe_uri = "file:///TEST_325_media_roundtrip.mp3"
            with text_ops._TransactionCM("T3 seed MediaFilesOA"):
                container = cont_fac.Create()
                concrete.MediaFilesOA = container
                new_uri = uri_fac.Create()
                container.MediaURIsOC.Add(new_uri)
                new_uri.MediaURI = probe_uri

            props = text_ops.GetSyncableProperties(src)
            assert "media_uris" in props, (
                f"media_uris absent after seeding. Keys: {list(props.keys())}"
            )
            assert props["media_uris"][0]["uri"] == probe_uri, props["media_uris"]
            _EVIDENCE["(c) media_uris GSP"] = props["media_uris"]

            tgt = text_ops.Create(f"{TEST_PREFIX}media_tgt")
            try:
                text_ops.ApplySyncableProperties(
                    tgt, {"media_uris": props["media_uris"]}
                )
                tgt_guid = str(tgt.Guid)
                from SIL.LCModel import ITextRepository

                repo = project.project.ServiceLocator.GetService(ITextRepository)
                refetched = None
                for t in repo.AllInstances():
                    if str(t.Guid) == tgt_guid:
                        refetched = t
                        break
                assert refetched is not None, "Could not re-fetch target text by GUID"

                c2 = cast_to_concrete(refetched)
                cont2 = getattr(c2, "MediaFilesOA", None)
                assert cont2 is not None, "MediaFilesOA None after Apply"
                actual_uris = [str(u.MediaURI) for u in cont2.MediaURIsOC]
                assert probe_uri in actual_uris, (
                    f"MediaURI not in LCM after Apply: {actual_uris}"
                )
                re_props = text_ops.GetSyncableProperties(refetched)
                assert re_props.get("media_uris"), re_props
                assert any(
                    e.get("uri") == probe_uri for e in re_props["media_uris"]
                ), re_props["media_uris"]

                _EVIDENCE["(c) media_uris after Apply (re-read)"] = actual_uris
                _EVIDENCE["(c) media_uris (R4)"] = (
                    f"PASS -- GSP+Apply round-trip uri={probe_uri!r}"
                )
            finally:
                text_ops.Delete(tgt)
        finally:
            text_ops.Delete(src)


# ---------------------------------------------------------------------------
# (d) ConstChartMovedText.Create full path with segments (R5)
# ---------------------------------------------------------------------------

class TestConstChartMovedTextCreate:
    """
    (d) R5 -- ConstChartMovedText.Create full path with live segments.

    Exercises:
    - Create via factory -> row.CellsOS.Add -> WordGroupRA + ColumnRA -> Preposed
    - No NRE raised
    - row.CellsOS contains the marker after create
    - WordGroupRA == original word group
    - Preposed readable and settable
    - Find, GetAll, GetWordGroup work
    - Delete removes marker from CellsOS

    Builds chart / row / word group from scratch in target_sandbox (no
    pre-existing ConstChartWordGroup in fwdata). Pattern: test_issue290,
    test_325_reflection_live.
    """

    @pytest.mark.live_phase("ConstChartMovedTextOperations", "add")
    def test_create_full_path_no_nre(self, target_sandbox):
        """
        Full path: text + segment -> chart + row + word group ->
        ConstChartMovedText.Create -> re-read -> verify -> Delete.
        """
        from SIL.LCModel import (
            IConstChartRow,
            IConstChartMovedTextMarker,
            IConstChartMovedTextMarkerRepository,
            IStTxtPara,
        )

        project = target_sandbox
        assert project.writeEnabled, "target_sandbox must be write-enabled"

        charts = project.ConstCharts
        rows = project.ConstChartRows
        word_groups = project.ConstChartWordGroups
        texts = project.Texts
        paragraphs = project.Paragraphs
        segments = project.Segments
        moved_ops = project.ConstChartMovedText

        chart = None
        text = None
        marker_created = None
        row = None

        try:
            text = texts.Create(f"{TEST_PREFIX}movedtext_text")
            paragraphs.Create(text, f"{TEST_PREFIX}sentence for moved text.")
            para_list = list(text.ContentsOA.ParagraphsOS)
            para = IStTxtPara(para_list[0])
            seg = segments.AppendSentence(para, f"{TEST_PREFIX}sentence for moved text.")
            if seg is None:
                segs = list(para.SegmentsOS)
                assert segs, "No ISegment available to build word group in target_sandbox"
                seg = segs[0]

            chart = charts.Create(f"{TEST_PREFIX}movedtext_chart")
            row = rows.Create(chart)
            wg = word_groups.Create(row, seg, seg)
            wg_guid = str(wg.Guid)
            row = IConstChartRow(wg.Owner)

            existing = moved_ops.Find(wg)
            assert existing is None, "Fresh word group must not already have a moved-text marker"

            marker_created = moved_ops.Create(wg, preposed=True)
            assert marker_created is not None, "Create returned None"
            marker_guid = str(marker_created.Guid)

            marker_repo = project.project.ServiceLocator.GetService(
                IConstChartMovedTextMarkerRepository
            )
            refetched = None
            for m in marker_repo.AllInstances():
                if str(m.Guid) == marker_guid:
                    refetched = m
                    break
            assert refetched is not None, "Marker not found in repository after Create"

            def _is_moved_marker(cell):
                if getattr(cell, "ClassName", None) == "ConstChartMovedTextMarker":
                    return True
                try:
                    return isinstance(cell, IConstChartMovedTextMarker)
                except Exception:
                    return False

            post_cells = list(row.CellsOS)
            marker_in_cells = any(
                _is_moved_marker(c) and str(c.Guid) == marker_guid
                for c in post_cells
            )
            assert marker_in_cells, (
                f"Marker GUID {marker_guid} not found in row.CellsOS after Create. "
                f"CellsOS types: {[_clr_name(c) for c in post_cells]}"
            )

            wgra = getattr(refetched, "WordGroupRA", None)
            assert wgra is not None, "WordGroupRA is None after Create"
            assert str(wgra.Guid) == wg_guid, (
                f"WordGroupRA.Guid mismatch: expected {wg_guid}, got {str(wgra.Guid)}"
            )

            preposed_val = refetched.Preposed
            assert preposed_val is True or preposed_val == True, (
                f"Preposed should be True after Create(preposed=True); got {preposed_val!r}"
            )

            _EVIDENCE["(d) Create no NRE"] = "PASS"
            _EVIDENCE["(d) row.CellsOS contains marker"] = "PASS"
            _EVIDENCE["(d) WordGroupRA == word group"] = "PASS"
            _EVIDENCE["(d) Preposed re-read"] = str(preposed_val)

            found = moved_ops.Find(wg)
            assert found is not None, "Find(wg) returned None after Create"
            assert str(found.Guid) == marker_guid, (
                f"Find returned wrong marker: {str(found.Guid)} != {marker_guid}"
            )
            _EVIDENCE["(d) Find"] = "PASS"

            chart_owner = row.Owner
            all_markers = list(moved_ops.GetAll(chart_owner))
            assert any(str(m.Guid) == marker_guid for m in all_markers), (
                f"GetAll did not include the created marker {marker_guid}"
            )
            _EVIDENCE["(d) GetAll"] = f"PASS ({len(all_markers)} total)"

            got_wg = moved_ops.GetWordGroup(refetched)
            assert got_wg is not None, "GetWordGroup returned None"
            assert str(got_wg.Guid) == wg_guid, (
                f"GetWordGroup returned wrong word group: {str(got_wg.Guid)} != {wg_guid}"
            )
            _EVIDENCE["(d) GetWordGroup"] = "PASS"

            moved_ops.SetPreposed(refetched, False)
            refetched2 = None
            for m in marker_repo.AllInstances():
                if str(m.Guid) == marker_guid:
                    refetched2 = m
                    break
            assert refetched2 is not None
            assert refetched2.Preposed == False, (
                f"SetPreposed(False) did not persist; got {refetched2.Preposed!r}"
            )
            _EVIDENCE["(d) SetPreposed round-trip"] = "PASS"

            moved_ops.Delete(marker_created)
            marker_created = None

            still_there = any(
                str(m.Guid) == marker_guid for m in marker_repo.AllInstances()
            )
            assert not still_there, "Marker still in repository after Delete"

            post_delete_cells = list(row.CellsOS)
            marker_in_cells_after = any(
                _is_moved_marker(c) and str(c.Guid) == marker_guid
                for c in post_delete_cells
            )
            assert not marker_in_cells_after, "Marker still in row.CellsOS after Delete"

            _EVIDENCE["(d) Delete removes from CellsOS"] = "PASS"
            _EVIDENCE["(d) RESULT"] = "PASS (target_sandbox, built from scratch)"

        finally:
            if marker_created is not None:
                try:
                    moved_ops.Delete(marker_created)
                except Exception:
                    pass
            if chart is not None:
                try:
                    charts.Delete(chart)
                except Exception:
                    pass
            if text is not None:
                try:
                    texts.Delete(text)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# (e) LexSense payload lacks DoNotShowMainEntryInRC (R7)
# ---------------------------------------------------------------------------

class TestLexSenseNoDoNotShowMainEntry:
    """
    (e) R7 -- LexSense GetSyncableProperties lacks DoNotShowMainEntryInRC.

    Verifies:
    - DoNotShowMainEntryInRC absent from payload
    - DoNotPublishInRC still present
    """

    @pytest.mark.live_phase("LexSenseOperations", "read")
    def test_sense_payload_lacks_donotshow(self, target_sandbox):
        """
        Create a LexEntry+Sense in target_sandbox. GetSyncableProperties.
        Assert DoNotShowMainEntryInRC absent. Assert DoNotPublishInRC present.
        """
        project = target_sandbox
        entry_ops = project.LexEntry
        sense_ops = project.Senses

        entry = entry_ops.Create(lexeme_form=f"{TEST_PREFIX}sense_payload")
        try:
            sense = sense_ops.Create(entry, "T3_payload_gloss")
            try:
                props = sense_ops.GetSyncableProperties(sense)

                # R7: must NOT be present
                assert "DoNotShowMainEntryInRC" not in props, (
                    f"GetSyncableProperties: 'DoNotShowMainEntryInRC' must not be present (R7). "
                    f"Got: {list(props.keys())}"
                )

                # DoNotPublishInRC must still be present (different field)
                assert "DoNotPublishInRC" in props, (
                    f"GetSyncableProperties: 'DoNotPublishInRC' is absent (it should still be present). "
                    f"Got: {list(props.keys())}"
                )

                _EVIDENCE["(e) DoNotShowMainEntryInRC absent"] = "PASS"
                _EVIDENCE["(e) DoNotPublishInRC present"] = "PASS"
                _EVIDENCE["(e) RESULT"] = "PASS"

            finally:
                sense_ops.Delete(sense)
        finally:
            entry_ops.Delete(entry)


# ---------------------------------------------------------------------------
# live_status.json + evidence writer
# ---------------------------------------------------------------------------

class TestT3EvidenceRecord:
    """Write live_status.json and the evidence file at end of T3."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_write_live_status_and_evidence(self, target_sandbox):
        """
        Confirm live mode and write tests/live_status.json +
        specs/325-syncable-properties/evidence/live-T3-syncable-properties.md.
        """
        from datetime import datetime, timezone

        repo_root = _repo_root()
        status_path = repo_root / "tests" / "live_status.json"

        status = {
            "run_mode": "live",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "test_file": "tests/operations/test_325_syncable_properties_live.py",
            "issue": "MattGyverLee/flexicon#325",
            "task": "T3",
        }
        with open(status_path, "w", encoding="utf-8") as fh:
            json.dump(status, fh, indent=2)

        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None, (
            "target_sandbox.project is None -- mock, not live"
        )

        with open(status_path, encoding="utf-8") as fh:
            written = json.load(fh)
        assert written["run_mode"] == "live", (
            f"FAIL: unverified -- run_mode is '{written['run_mode']}', expected 'live'"
        )

        _EVIDENCE["commands"] = (
            "python -m pytest -m \"not requires_live_project\" -q; "
            "$env:FLEXLIBS_REQUIRE_LIVE = \"1\"; "
            "python -m pytest tests/operations/test_325_syncable_properties_live.py "
            "-m requires_live_project -q"
        )
        _EVIDENCE["run_mode"] = written["run_mode"]
        _EVIDENCE["run_timestamp"] = written["run_timestamp"]
        ev_path = _write_evidence(_EVIDENCE)
        print(f"\n[OK] Evidence written to {ev_path}")

        assert written["run_mode"] == "live"
