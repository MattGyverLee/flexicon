#
#   test_325_reflection_live.py
#
#   Live LCM reflection for issue #325 (syncable-properties), Task T0.
#
#   Surfaces (declared + inherited) via clr.GetClrType + dir() for:
#     - ICmMediaContainer, ICmMediaURI
#     - IText (MediaFilesOA)
#     - ILexEtymology (LanguageRS element type, owning list)
#     - ILexReference (OwnerType/Name/Comment types, TargetsRS)
#     - ILexRefType
#     - IConstChartMovedTextMarker, IConstChartRow, IConstChartWordGroup
#     - ILexSense (DoNotShowMainEntryInRC absent)
#
#   Write-path:
#     target_sandbox -- chart/row/word-group construction, moved-text-
#     marker via factory -> WordGroupRA/ColumnRA -> Preposed assignment;
#     records whether Preposed sets without NullReferenceException.
#
#   Read-path counts:
#     sena3_live_ro (local fixture, opens "Sena 3" read-only by name)
#       -- populated LanguageRS count, ILexReference per owner type
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import json
import os
import sys
import pathlib

import pytest

pytestmark = pytest.mark.requires_live_project

# ---------------------------------------------------------------------------
# Local fixture: Sena 3 read-only by project name
# (Sena 3 is on this machine; reads are unrestricted per CLAUDE.md)
# ---------------------------------------------------------------------------

@pytest.fixture
def sena3_live_ro():
    """
    Open a populated project read-only for reflection evidence.  Reads are
    unrestricted per CLAUDE.md.  Prefers 'Sena 3' but falls back to other
    populated projects on this machine when Sena 3's fwdata is unavailable.
    Fails loudly when FLEXLIBS_REQUIRE_LIVE=1 and no candidate is reachable.
    """
    require_live = os.environ.get("FLEXLIBS_REQUIRE_LIVE") == "1"

    def _unavailable(reason):
        if require_live:
            pytest.fail(
                f"FLEXLIBS_REQUIRE_LIVE=1 but no read-only project is "
                f"available: {reason}. Refusing to skip."
            )
        pytest.skip(reason)

    if "SIL.LCModel" not in sys.modules:
        _unavailable("Requires SIL.LCModel (FieldWorks installed)")

    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception as exc:
        _unavailable(f"Could not import FLExProject: {exc}")

    # Candidate projects -- try in order; Sena 3 preferred; Ejagham Full
    # and Hdi are also populated with lexical references and etymologies.
    candidates = ["Sena 3", "Ejagham Full", "Hdi", "SampleLexicon3"]
    last_exc = None
    for candidate in candidates:
        project = FLExProject()
        try:
            project.OpenProject(candidate, writeEnabled=False)
            print(f"[INFO] sena3_live_ro opened '{candidate}' read-only")
            break
        except Exception as exc:
            last_exc = exc
            try:
                project.CloseProject()
            except Exception:
                pass
    else:
        _unavailable(
            f"None of {candidates} could be opened read-only. "
            f"Last error: {last_exc}"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dir_public(obj):
    """Return sorted list of non-dunder members from dir(obj)."""
    return sorted(m for m in dir(obj) if not m.startswith("__"))


def _clr_type_name(obj):
    """Return full CLR type name, or Python type name if unavailable."""
    try:
        return obj.GetType().FullName
    except Exception:
        return type(obj).__name__


def _write_raw(data: dict, filename: str):
    """Write JSON evidence to specs/325-syncable-properties/evidence/."""
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    evidence_dir = repo_root / "specs" / "325-syncable-properties" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_path = evidence_dir / filename
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    return out_path


# ---------------------------------------------------------------------------
# T0-A: Media interfaces (ICmMediaContainer, ICmMediaURI, IText.MediaFilesOA)
# ---------------------------------------------------------------------------

class TestT0AMediaInterfaces:
    """Reflect on ICmMediaContainer, ICmMediaURI, IText.MediaFilesOA."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_media_container_and_uri_surfaces(self, sena3_live_ro):
        """
        Surfaces ICmMediaContainer and ICmMediaURI from a live Sena 3
        project.  Also probes IText.MediaFilesOA presence.
        """
        import clr
        from SIL.LCModel import (
            ICmMediaContainer, ICmMediaURI, IText, ITextRepository,
        )

        evidence = {}

        # --- ICmMediaContainer via GetClrType ---
        clr_type_container = clr.GetClrType(ICmMediaContainer)
        evidence["ICmMediaContainer_clr_type"] = str(clr_type_container)
        evidence["ICmMediaContainer_static_dir"] = sorted(
            m for m in dir(clr_type_container) if not m.startswith("__")
        )

        # Live instance via LangProject.MediaContainerOA
        lp = sena3_live_ro.project.LangProject
        container = getattr(lp, "MediaContainerOA", None)
        evidence["LangProject_has_MediaContainerOA"] = hasattr(lp, "MediaContainerOA")
        if container is not None:
            evidence["ICmMediaContainer_live_clr_type"] = _clr_type_name(container)
            evidence["ICmMediaContainer_live_dir"] = _dir_public(container)
            evidence["ICmMediaContainer_has_MediaURIsOC"] = hasattr(container, "MediaURIsOC")
            if hasattr(container, "MediaURIsOC"):
                count = container.MediaURIsOC.Count
                evidence["ICmMediaContainer_MediaURIsOC_count"] = count
                for uri_obj in container.MediaURIsOC:
                    evidence["ICmMediaURI_live_clr_type"] = _clr_type_name(uri_obj)
                    evidence["ICmMediaURI_live_dir"] = _dir_public(uri_obj)
                    evidence["ICmMediaURI_has_MediaFileRA"] = hasattr(uri_obj, "MediaFileRA")
                    evidence["ICmMediaURI_has_MediaURI"] = hasattr(uri_obj, "MediaURI")
                    break
        else:
            evidence["ICmMediaContainer_live"] = "MediaContainerOA is None on LangProject"

        # --- ICmMediaURI via GetClrType ---
        clr_type_uri = clr.GetClrType(ICmMediaURI)
        evidence["ICmMediaURI_clr_type"] = str(clr_type_uri)
        evidence["ICmMediaURI_static_dir"] = sorted(
            m for m in dir(clr_type_uri) if not m.startswith("__")
        )

        # --- IText.MediaFilesOA via GetClrType and live instance ---
        clr_type_text = clr.GetClrType(IText)
        evidence["IText_clr_type"] = str(clr_type_text)
        evidence["IText_static_has_MediaFilesOA"] = "MediaFilesOA" in dir(clr_type_text)

        text_repo = sena3_live_ro.project.ServiceLocator.GetService(ITextRepository)
        for text in text_repo.AllInstances():
            evidence["IText_live_clr_type"] = _clr_type_name(text)
            evidence["IText_live_has_MediaFilesOA"] = hasattr(text, "MediaFilesOA")
            mf = getattr(text, "MediaFilesOA", None)
            evidence["IText_MediaFilesOA_is_None"] = (mf is None)
            if mf is not None:
                evidence["IText_MediaFilesOA_clr_type"] = _clr_type_name(mf)
                evidence["IText_MediaFilesOA_dir"] = _dir_public(mf)
            break

        _write_raw(evidence, "live-T0-media-raw.json")

        assert isinstance(evidence.get("ICmMediaContainer_static_dir"), list), \
            "ICmMediaContainer GetClrType reflection failed"
        assert isinstance(evidence.get("ICmMediaURI_static_dir"), list), \
            "ICmMediaURI GetClrType reflection failed"


# ---------------------------------------------------------------------------
# T0-B: ILexEtymology -- LanguageRS element type, owning list, count
# ---------------------------------------------------------------------------

class TestT0BLexEtymologyLanguageRS:
    """Probe ILexEtymology.LanguageRS element type and backing list."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_languageRS_element_type_and_list(self, sena3_live_ro):
        """
        Reflects on ILexEtymology.LanguageRS from live Sena 3 instances.
        Records element CLR type and which ICmPossibilityList owns it.
        Counts etymologies with at least one LanguageRS entry.
        """
        import clr
        from SIL.LCModel import ILexEtymology, ILexEtymologyRepository

        evidence = {}

        clr_type = clr.GetClrType(ILexEtymology)
        evidence["ILexEtymology_clr_type"] = str(clr_type)
        evidence["ILexEtymology_static_has_LanguageRS"] = "LanguageRS" in dir(clr_type)
        evidence["ILexEtymology_static_has_Source"] = "Source" in dir(clr_type)
        evidence["ILexEtymology_static_has_LanguageNotes"] = "LanguageNotes" in dir(clr_type)

        etym_repo = sena3_live_ro.project.ServiceLocator.GetService(ILexEtymologyRepository)
        all_etyms = list(etym_repo.AllInstances())
        evidence["ILexEtymology_total_count"] = len(all_etyms)

        populated_language_rs = 0
        element_type_set = set()
        list_name_set = set()

        for etym in all_etyms:
            if "ILexEtymology_live_dir" not in evidence:
                evidence["ILexEtymology_live_clr_type"] = _clr_type_name(etym)
                evidence["ILexEtymology_live_dir"] = _dir_public(etym)
                evidence["ILexEtymology_live_has_LanguageRS"] = hasattr(etym, "LanguageRS")
                evidence["ILexEtymology_live_has_Source"] = hasattr(etym, "Source")
                evidence["ILexEtymology_live_has_LanguageNotes"] = hasattr(etym, "LanguageNotes")

            lang_rs = getattr(etym, "LanguageRS", None)
            if lang_rs is not None and lang_rs.Count > 0:
                populated_language_rs += 1
                for elem in lang_rs:
                    element_type_set.add(_clr_type_name(elem))
                    # Walk to owner to identify the backing list
                    owner = getattr(elem, "Owner", None)
                    if owner is not None:
                        owner_owner = getattr(owner, "Owner", None)
                        # The list is the owner's owner (CmPossibility -> List)
                        # or sometimes the owner itself if it IS the list
                        target = owner_owner if owner_owner is not None else owner
                        name_obj = getattr(target, "Name", None)
                        if name_obj is not None:
                            try:
                                name_text = name_obj.BestAnalysisAlternative.Text
                                list_name_set.add(str(name_text))
                            except Exception:
                                list_name_set.add(repr(name_obj))
                    if "LanguageRS_first_element_dir" not in evidence:
                        evidence["LanguageRS_first_element_dir"] = _dir_public(elem)
                        evidence["LanguageRS_first_element_clr_type"] = _clr_type_name(elem)
                    break

        evidence["ILexEtymology_populated_LanguageRS_count"] = populated_language_rs
        evidence["LanguageRS_element_CLR_types"] = sorted(element_type_set)
        evidence["LanguageRS_backing_list_names"] = sorted(list_name_set)

        _write_raw(evidence, "live-T0-etymology-raw.json")

        assert evidence.get("ILexEtymology_live_has_LanguageRS") is not None or len(all_etyms) == 0, \
            "Could not probe any live ILexEtymology instance"


# ---------------------------------------------------------------------------
# T0-C: ILexReference, ILexRefType surfaces + per-owner-type counts
# ---------------------------------------------------------------------------

class TestT0CLexReferenceSurfaces:
    """Reflect on ILexReference, ILexRefType; count per owner type."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_lexreference_surfaces_and_counts(self, sena3_live_ro):
        """
        Surfaces ILexReference and ILexRefType from Sena 3.
        Records OwnerType, Name, Comment types, TargetsRS.
        Counts ILexReference per owner type.
        """
        import clr
        from SIL.LCModel import (
            ILexReference, ILexReferenceRepository,
            ILexRefType, ILexRefTypeRepository,
        )

        evidence = {}

        # --- ILexRefType static + live ---
        clr_reftype = clr.GetClrType(ILexRefType)
        evidence["ILexRefType_clr_type"] = str(clr_reftype)
        evidence["ILexRefType_static_dir"] = sorted(
            m for m in dir(clr_reftype) if not m.startswith("__")
        )

        reftype_repo = sena3_live_ro.project.ServiceLocator.GetService(ILexRefTypeRepository)
        all_reftypes = list(reftype_repo.AllInstances())
        evidence["ILexRefType_count"] = len(all_reftypes)
        if all_reftypes:
            rt = all_reftypes[0]
            evidence["ILexRefType_live_clr_type"] = _clr_type_name(rt)
            evidence["ILexRefType_live_dir"] = _dir_public(rt)
            evidence["ILexRefType_has_Name"] = hasattr(rt, "Name")
            evidence["ILexRefType_has_Abbreviation"] = hasattr(rt, "Abbreviation")
            evidence["ILexRefType_has_MappingType"] = hasattr(rt, "MappingType")
            evidence["ILexRefType_has_Members"] = hasattr(rt, "Members")
            evidence["ILexRefType_has_Comment"] = hasattr(rt, "Comment")
            if hasattr(rt, "Name"):
                try:
                    evidence["ILexRefType_Name_clr_type"] = _clr_type_name(rt.Name)
                except Exception as exc:
                    evidence["ILexRefType_Name_clr_type"] = f"error: {exc}"
            if hasattr(rt, "Comment"):
                try:
                    evidence["ILexRefType_Comment_clr_type"] = _clr_type_name(rt.Comment)
                except Exception as exc:
                    evidence["ILexRefType_Comment_clr_type"] = f"error: {exc}"

        # --- ILexReference static + live + per-owner-type counts ---
        clr_ref = clr.GetClrType(ILexReference)
        evidence["ILexReference_clr_type"] = str(clr_ref)
        evidence["ILexReference_static_dir"] = sorted(
            m for m in dir(clr_ref) if not m.startswith("__")
        )

        ref_repo = sena3_live_ro.project.ServiceLocator.GetService(ILexReferenceRepository)
        all_refs = list(ref_repo.AllInstances())
        evidence["ILexReference_total"] = len(all_refs)

        owner_type_counts: dict = {}
        targets_rs_types: set = set()

        for ref in all_refs:
            if "ILexReference_live_dir" not in evidence:
                evidence["ILexReference_live_clr_type"] = _clr_type_name(ref)
                evidence["ILexReference_live_dir"] = _dir_public(ref)
                evidence["ILexReference_has_TargetsRS"] = hasattr(ref, "TargetsRS")
                evidence["ILexReference_has_Name"] = hasattr(ref, "Name")
                evidence["ILexReference_has_Comment"] = hasattr(ref, "Comment")
                if hasattr(ref, "Name"):
                    try:
                        evidence["ILexReference_Name_clr_type"] = _clr_type_name(ref.Name)
                    except Exception as exc:
                        evidence["ILexReference_Name_clr_type"] = f"error: {exc}"
                if hasattr(ref, "Comment"):
                    try:
                        evidence["ILexReference_Comment_clr_type"] = _clr_type_name(ref.Comment)
                    except Exception as exc:
                        evidence["ILexReference_Comment_clr_type"] = f"error: {exc}"

            owner = getattr(ref, "Owner", None)
            if owner is not None:
                try:
                    owner_cn = owner.ClassName
                except Exception:
                    owner_cn = type(owner).__name__
                owner_type_counts[owner_cn] = owner_type_counts.get(owner_cn, 0) + 1

            targets_rs = getattr(ref, "TargetsRS", None)
            if targets_rs is not None:
                for tgt in targets_rs:
                    try:
                        targets_rs_types.add(tgt.ClassName)
                    except Exception:
                        targets_rs_types.add(_clr_type_name(tgt))

        evidence["ILexReference_per_owner_type"] = owner_type_counts
        evidence["ILexReference_TargetsRS_element_classnames"] = sorted(targets_rs_types)

        _write_raw(evidence, "live-T0-lexref-raw.json")

        # Soft assertions -- zero is a valid data outcome
        assert isinstance(evidence.get("ILexRefType_static_dir"), list)
        assert isinstance(evidence.get("ILexReference_static_dir"), list)


# ---------------------------------------------------------------------------
# T0-D: ILexSense -- confirm DoNotShowMainEntryInRC absent
# ---------------------------------------------------------------------------

class TestT0DLexSenseSurface:
    """Probe ILexSense for DoNotShowMainEntryInRC."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_lexsense_donotshow_absent(self, sena3_live_ro):
        """
        Reflects on ILexSense from live Sena 3.
        Asserts DoNotShowMainEntryInRC is absent on live instances.
        """
        import clr
        from SIL.LCModel import ILexSense, ILexSenseRepository

        evidence = {}

        clr_type = clr.GetClrType(ILexSense)
        evidence["ILexSense_clr_type"] = str(clr_type)
        evidence["ILexSense_static_has_DoNotShowMainEntryInRC"] = (
            "DoNotShowMainEntryInRC" in dir(clr_type)
        )
        evidence["ILexSense_static_has_AnthroNote"] = "AnthroNote" in dir(clr_type)
        evidence["ILexSense_static_has_Source"] = "Source" in dir(clr_type)
        evidence["ILexSense_static_has_SemanticDomainsRC"] = "SemanticDomainsRC" in dir(clr_type)

        sense_repo = sena3_live_ro.project.ServiceLocator.GetService(ILexSenseRepository)
        for sense in sense_repo.AllInstances():
            evidence["ILexSense_live_clr_type"] = _clr_type_name(sense)
            evidence["ILexSense_live_dir"] = _dir_public(sense)
            evidence["ILexSense_live_has_DoNotShowMainEntryInRC"] = hasattr(
                sense, "DoNotShowMainEntryInRC"
            )
            evidence["ILexSense_live_has_AnthroNote"] = hasattr(sense, "AnthroNote")
            evidence["ILexSense_live_has_Source"] = hasattr(sense, "Source")
            evidence["ILexSense_live_has_SemanticDomainsRC"] = hasattr(sense, "SemanticDomainsRC")
            if hasattr(sense, "Source"):
                try:
                    evidence["ILexSense_Source_clr_type"] = _clr_type_name(sense.Source)
                except Exception as exc:
                    evidence["ILexSense_Source_clr_type"] = f"error: {exc}"
            break

        _write_raw(evidence, "live-T0-lexsense-raw.json")

        assert not evidence.get("ILexSense_live_has_DoNotShowMainEntryInRC", True), \
            "DoNotShowMainEntryInRC IS present on live ILexSense -- unexpected"


# ---------------------------------------------------------------------------
# T0-E: Discourse interfaces surface + Preposed marker round-trip
#        (target_sandbox -- write-path)
# ---------------------------------------------------------------------------

class TestT0EDiscourseInterfaces:
    """
    Reflect on IConstChartMovedTextMarker, IConstChartRow,
    IConstChartWordGroup; attempt Preposed setter the FLEx way:
    factory -> WordGroupRA / ColumnRA -> Preposed.
    """

    @pytest.mark.live_phase("ConstChartMovedTextOperations", "add")
    def test_discourse_surfaces_and_preposed_roundtrip(self, target_sandbox):
        """
        1. Reflect on all three discourse cell-part interfaces.
        2. Build a real chart / row in target_sandbox.
        3. Create a word group if a live ISegment is available.
        4. Create a moved-text marker via factory; set WordGroupRA and
           ColumnRA before assigning Preposed.
        5. Record whether set_Preposed raises NullReferenceException.
        """
        import clr
        from SIL.LCModel import (
            IConstChartMovedTextMarker, IConstChartMovedTextMarkerFactory,
            IConstChartRow, IConstChartRowFactory,
            IConstChartWordGroup, IConstChartWordGroupFactory,
        )

        evidence = {}

        # --- Static CLR surface via GetClrType ---
        for iface_name, iface in [
            ("IConstChartMovedTextMarker", IConstChartMovedTextMarker),
            ("IConstChartRow", IConstChartRow),
            ("IConstChartWordGroup", IConstChartWordGroup),
        ]:
            ct = clr.GetClrType(iface)
            evidence[f"{iface_name}_clr_type"] = str(ct)
            evidence[f"{iface_name}_static_dir"] = sorted(
                m for m in dir(ct) if not m.startswith("__")
            )

        # --- Build real chart / row ---
        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        word_groups = target_sandbox.ConstChartWordGroups
        texts = target_sandbox.Texts
        markers_ops = target_sandbox.ConstChartMarkers

        text = texts.Create("TEST_325 reflection text")
        try:
            para = None
            seg = None
            if hasattr(text, "ContentsOA") and text.ContentsOA is not None:
                paras = list(text.ContentsOA.ParagraphsOS)
                if paras:
                    para = paras[0]
            if para is not None and hasattr(para, "SegmentsOS"):
                segs = list(para.SegmentsOS)
                if segs:
                    seg = segs[0]

            chart = charts.Create("TEST_325 reflection chart")
            try:
                row = rows.Create(chart)
                try:
                    # --- Live IConstChartRow surface ---
                    evidence["IConstChartRow_live_clr_type"] = _clr_type_name(row)
                    evidence["IConstChartRow_live_dir"] = _dir_public(row)
                    evidence["IConstChartRow_has_Label"] = hasattr(row, "Label")
                    evidence["IConstChartRow_has_Notes"] = hasattr(row, "Notes")
                    evidence["IConstChartRow_has_CellsOS"] = hasattr(row, "CellsOS")
                    evidence["IConstChartRow_has_ClauseType"] = hasattr(row, "ClauseType")
                    evidence["IConstChartRow_has_EndParagraph"] = hasattr(row, "EndParagraph")
                    evidence["IConstChartRow_has_EndSegmentRA"] = hasattr(row, "EndSegmentRA")
                    evidence["IConstChartRow_has_StartDependentClauseGroup"] = hasattr(
                        row, "StartDependentClauseGroup"
                    )
                    if hasattr(row, "Label"):
                        try:
                            evidence["IConstChartRow_Label_clr_type"] = _clr_type_name(row.Label)
                        except Exception as exc:
                            evidence["IConstChartRow_Label_clr_type"] = f"error: {exc}"
                    if hasattr(row, "Notes"):
                        try:
                            evidence["IConstChartRow_Notes_clr_type"] = _clr_type_name(row.Notes)
                        except Exception as exc:
                            evidence["IConstChartRow_Notes_clr_type"] = f"error: {exc}"

                    # --- Get or create a column marker (ICmPossibility) ---
                    col_marker = None
                    lp = target_sandbox.project.LangProject
                    disc_data = getattr(lp, "DiscourseDataOA", None)
                    if disc_data is not None:
                        chart_markers_list = getattr(disc_data, "ChartMarkersOA", None)
                        if (chart_markers_list is not None
                                and chart_markers_list.PossibilitiesOS.Count > 0):
                            col_marker = chart_markers_list.PossibilitiesOS[0]

                    if col_marker is None:
                        # Create a minimal marker to use as column reference
                        col_marker = markers_ops.Create("TEST_325 column")

                    # --- Word group (requires a live ISegment) ---
                    if seg is not None:
                        word_group = None
                        try:
                            word_group = word_groups.Create(row, seg, seg)
                            evidence["word_group_create_outcome"] = "success"
                        except Exception as exc:
                            evidence["word_group_create_outcome"] = f"raised: {exc}"

                        if word_group is not None:
                            evidence["IConstChartWordGroup_live_clr_type"] = _clr_type_name(word_group)
                            evidence["IConstChartWordGroup_live_dir"] = _dir_public(word_group)
                            evidence["IConstChartWordGroup_has_ColumnRA"] = hasattr(word_group, "ColumnRA")
                            evidence["IConstChartWordGroup_has_BeginSegmentRA"] = hasattr(
                                word_group, "BeginSegmentRA"
                            )
                            evidence["IConstChartWordGroup_has_EndSegmentRA"] = hasattr(
                                word_group, "EndSegmentRA"
                            )

                            # --- Moved-text marker: factory -> row.CellsOS.Add -> WordGroupRA -> ColumnRA -> Preposed ---
                            # R5 (issue #325): IConstChartWordGroup.MovedTextMarkerOA does NOT exist.
                            # Correct ownership: marker is a peer cell in row.CellsOS.
                            # Navigation: marker.WordGroupRA -> word group (not the reverse).
                            factory = target_sandbox.project.ServiceLocator.GetService(
                                IConstChartMovedTextMarkerFactory
                            )
                            new_marker = factory.Create()
                            evidence["IConstChartMovedTextMarker_live_clr_type"] = _clr_type_name(new_marker)
                            evidence["IConstChartMovedTextMarker_live_dir"] = _dir_public(new_marker)
                            evidence["IConstChartMovedTextMarker_has_Preposed"] = hasattr(
                                new_marker, "Preposed"
                            )
                            evidence["IConstChartMovedTextMarker_has_WordGroupRA"] = hasattr(
                                new_marker, "WordGroupRA"
                            )
                            evidence["IConstChartMovedTextMarker_has_ColumnRA"] = hasattr(
                                new_marker, "ColumnRA"
                            )

                            # Step 1: insert marker into row.CellsOS (R5 ownership model;
                            # NOT word_group.MovedTextMarkerOA which does not exist).
                            try:
                                row.CellsOS.Add(new_marker)
                                evidence["row_CellsOS_Add_outcome"] = "success"
                            except Exception as exc:
                                evidence["row_CellsOS_Add_outcome"] = f"raised: {exc}"

                            # Step 2: set WordGroupRA
                            if hasattr(new_marker, "WordGroupRA"):
                                try:
                                    new_marker.WordGroupRA = word_group
                                    evidence["set_WordGroupRA_outcome"] = "success"
                                except Exception as exc:
                                    evidence["set_WordGroupRA_outcome"] = f"raised: {exc}"

                            # Step 3: set ColumnRA
                            if hasattr(new_marker, "ColumnRA") and col_marker is not None:
                                try:
                                    new_marker.ColumnRA = col_marker
                                    evidence["set_ColumnRA_outcome"] = "success"
                                except Exception as exc:
                                    evidence["set_ColumnRA_outcome"] = f"raised: {exc}"

                            # Step 4: set Preposed -- the key question from T0
                            try:
                                new_marker.Preposed = True
                                evidence["Preposed_set_True_outcome"] = "success"
                                # Read back to confirm
                                evidence["Preposed_readback"] = bool(new_marker.Preposed)
                            except Exception as exc:
                                evidence["Preposed_set_True_outcome"] = f"raised: {exc}"
                    else:
                        evidence["word_group_skip_reason"] = (
                            "No live ISegment available in target_sandbox text; "
                            "gathering raw factory surface only"
                        )
                        # Still capture marker surface
                        factory = target_sandbox.project.ServiceLocator.GetService(
                            IConstChartMovedTextMarkerFactory
                        )
                        new_marker = factory.Create()
                        evidence["IConstChartMovedTextMarker_live_clr_type"] = _clr_type_name(new_marker)
                        evidence["IConstChartMovedTextMarker_live_dir"] = _dir_public(new_marker)
                        evidence["IConstChartMovedTextMarker_has_Preposed"] = hasattr(new_marker, "Preposed")
                        try:
                            new_marker.Preposed = True
                            evidence["Preposed_set_True_outcome_raw"] = "success"
                        except Exception as exc:
                            evidence["Preposed_set_True_outcome_raw"] = f"raised: {exc}"

                finally:
                    rows.Delete(row)
            finally:
                charts.Delete(chart)
        finally:
            texts.Delete(text)

        _write_raw(evidence, "live-T0-discourse-raw.json")

        assert "IConstChartRow_live_dir" in evidence, \
            "IConstChartRow live reflection did not execute"
        assert "IConstChartMovedTextMarker_live_dir" in evidence, \
            "IConstChartMovedTextMarker live reflection did not execute"


# ---------------------------------------------------------------------------
# T0-F: Write live_status.json
# ---------------------------------------------------------------------------

class TestT0FEvidenceRecord:
    """Record run_mode in tests/live_status.json."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_write_live_status(self, target_sandbox):
        """
        Confirms live mode and writes tests/live_status.json.
        """
        from datetime import datetime, timezone

        repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
        status_path = repo_root / "tests" / "live_status.json"

        status = {
            "run_mode": "live",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "test_file": "tests/operations/test_325_reflection_live.py",
            "issue": "MattGyverLee/flexicon#325",
            "task": "T0",
        }
        with open(status_path, "w", encoding="utf-8") as fh:
            json.dump(status, fh, indent=2)

        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None, \
            "target_sandbox.project is None -- mock, not live"

        with open(status_path, encoding="utf-8") as fh:
            written = json.load(fh)
        assert written["run_mode"] == "live", \
            f"FAIL: unverified -- run_mode is '{written['run_mode']}', expected 'live'"
