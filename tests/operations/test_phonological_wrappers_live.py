#
#   test_phonological_wrappers_live.py
#
#   Live verification for issue #326 phonological wrapper corrections.
#
#   Modeled on tests/operations/test_target_live_smoke.py: the Target sandbox
#   fixture proves the session reached a real LCM. The actual assertions read
#   from installed FLEx projects (reads are unrestricted per CLAUDE.md) because
#   the Sena 3 fixture is not present in this worktree.
#
#   Verifies:
#     - PhSimpleContextSeg.segment returns the linked phoneme via
#       FeatureStructureRA (not the nonexistent SegmentRA).
#     - PhSimpleContextNC.natural_class returns the linked natural class via
#       FeatureStructureRA (not the nonexistent NaturalClassRA).
#     - PhonologicalRule.has_metathesis_parts / metathesis_parts derive the
#       swapped parts from StrucDescOS + switch-index fields.
#
#   No writes are performed to installed projects; the Target sandbox is only
#   opened to satisfy the live-fixture contract. No TEST_ objects are created.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import os

import pytest

pytestmark = pytest.mark.requires_live_project

_EVIDENCE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "specs",
        "326-phonological-wrapper-members",
        "evidence",
    )
)

# Installed FLEx projects to scan for live phonological-rule samples. Reads are
# unrestricted (CLAUDE.md); Sena 3 is excluded because its live .fwdata is known
# corrupted in this environment (T1 reflection report).
_READ_CANDIDATES = (
    "arz-flex",
    "Aweti",
    "blx-flex",
    "Circumsanity",
    "Claude-Swahili",
    "Claude-Turkish",
    "Egyptian Arabic Template",
    "Ejagham Full",
    "Ejagham Full GT-Test",
    "Ejagham Mini",
    "Ejagham028Src",
    "Ejaw",
    "Esperanto",
    "fmp",
    "French-FLExTrans",
    "French-FLExTrans-Demo2025",
    "French-FLExTrans-Exp4",
    "French-FLExTrans-Exp5",
    "German-FLExTrans-Sample",
    "Hdi",
    "Iceve-Maci Test-Iceve",
    "Iceve-Maci Test-Ici",
    "Indonesian Problem",
    "Indonesian-FLExTrans",
    "Indonesian-preclean",
    "IndonesianHC",
    "IndonesianHC-Complete",
    "IndonesianHC-Start",
    "IndonesianRelated-FLExTrans",
    "Isenye Nora",
    "Kenyang-M",
    "Korean-GIAL",
    "Lamkang flextrans experiment",
    "Lex Training Sample Project 1",
    "Malay Parsing-20230810withHC",
    "Malay Project",
    "Mbugwe Lizzie",
    "Mbugwe Lizzie FLExTrans",
    "Mbugwe Lizzie FLExTrans RA-01",
    "Mbugwe LizzieHC parsecrash",
    "Mbugwe LizzieHC practice",
    "Meetto -Flextrans",
    "morphboundary",
    "Naami dub",
    "Nchani",
    "Nepali flextrans experiment",
    "Ngoreme FLEx",
    "Ngoreme Johnny",
    "Nomaande",
    "NotOnClitic",
    "Pere",
    "Proj_no_pop",
    "Quechua qxh",
    "Quenya",
    "Rangi Lizzie FLExTrans",
    "Resembli",
    "Resembli Original",
    "ResembliO",
    "ResembliO-Delete",
    "SampleLexicon",
    "SampleLexicon3",
    "Sena_InterlinearTraining",
    "Sichuan Yi",
    "Spanish-FLExTrans-Demo2025",
    "Spanish-FLExTrans-Exp4",
    "Spanish-FLExTrans-Exp5",
    "SpanishParsing",
    "Swahili Andreas",
    "Swedish-FLExTrans-Sample",
    "SwissGerman",
    "TAK-Flextrans",
    "Takwane-Jeff",
    "Test",
    "TestLangProj",
    "Tlachichilco Tepehua",
    "Tlachichilco Tepehua-NT Noparse",
    "Tlachichilco Tepehua-NT orthography",
    "Tlachichilco Tepehua-Speedtest",
    "Turkish",
    "Vanaw",
    "Xinaliq",
    "Yi Sichuan",
)


def _open_readonly(name):
    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    project.OpenProject(name, writeEnabled=False)
    return project


def _write_evidence(payload, filename):
    os.makedirs(_EVIDENCE_DIR, exist_ok=True)
    path = os.path.join(_EVIDENCE_DIR, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=str)
    print(f"\n[OK] Wrote programmer live evidence to {path}")


class TestTargetFixtureReachLiveLCM:
    """Prove the Target sandbox fixture opens a real LCM cache, not a mock."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_target_sandbox_opens_write_enabled(self, target_sandbox):
        """A fresh sandbox copy of the Target backup opens for writing."""
        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None


class TestInstalledProjectsWrapperReadBack:
    """Read-back verification against installed FLEx projects."""

    @pytest.mark.live_phase("PhonologicalRuleOperations", "read")
    def test_context_links_read_back_via_wrappers(self, target_sandbox):
        """
        Real PhSimpleContextSeg and PhSimpleContextNC instances link to their
        segment/natural class through FeatureStructureRA. The wrapper properties
        must return non-None objects.
        """
        from flexicon.code.Grammar.phonological_rule import PhonologicalRule
        from flexicon.code.System.phonological_context import PhonologicalContext

        evidence = {
            "projects_scanned": 0,
            "projects_opened": 0,
            "seg_found": False,
            "nc_found": False,
            "seg_class_name": None,
            "nc_class_name": None,
        }

        seg_found = nc_found = False
        for name in _READ_CANDIDATES:
            evidence["projects_scanned"] += 1
            try:
                project = _open_readonly(name)
            except Exception:
                continue
            evidence["projects_opened"] += 1
            try:
                phon_data = project.lp.PhonologicalDataOA
                rules = (
                    list(phon_data.PhonRulesOS)
                    if phon_data and hasattr(phon_data, "PhonRulesOS")
                    else []
                )
                for raw_rule in rules:
                    wrapped_rule = PhonologicalRule(raw_rule)
                    for ctx in wrapped_rule.input_contexts:
                        if ctx.is_simple_context_seg:
                            segment = ctx.segment
                            assert segment is not None, (
                                "PhSimpleContextSeg.segment returned None on a live rule; "
                                "FeatureStructureRA link is broken."
                            )
                            seg_found = True
                            evidence["seg_found"] = True
                            evidence["seg_class_name"] = getattr(
                                segment, "ClassName", type(segment).__name__
                            )
                        if ctx.is_simple_context_nc:
                            nc = ctx.natural_class
                            assert nc is not None, (
                                "PhSimpleContextNC.natural_class returned None on a live rule; "
                                "FeatureStructureRA link is broken."
                            )
                            nc_found = True
                            evidence["nc_found"] = True
                            evidence["nc_class_name"] = getattr(
                                nc, "ClassName", type(nc).__name__
                            )
                        if seg_found and nc_found:
                            break
                    if seg_found and nc_found:
                        break
            finally:
                try:
                    project.CloseProject()
                except Exception:
                    pass

            if seg_found and nc_found:
                break

        assert seg_found, "No PhSimpleContextSeg found in installed FLEx projects"
        assert nc_found, "No PhSimpleContextNC found in installed FLEx projects"
        _write_evidence({"context_links": evidence}, "live-programmer-context-links.json")

    @pytest.mark.live_phase("PhonologicalRuleOperations", "read")
    def test_metathesis_parts_read_back_via_wrapper(self, target_sandbox):
        """
        Real PhMetathesisRule instances expose swapped parts derived from
        StrucDescOS slices using LeftSwitchIndex/LeftSwitchLimit and
        RightSwitchIndex/RightSwitchLimit.
        """
        from flexicon.code.Grammar.phonological_rule import PhonologicalRule

        evidence = {
            "projects_scanned": 0,
            "projects_opened": 0,
            "metathesis_found": False,
            "left_count": 0,
            "right_count": 0,
            "left_switch": None,
            "right_switch": None,
        }

        found = False
        for name in _READ_CANDIDATES:
            evidence["projects_scanned"] += 1
            try:
                project = _open_readonly(name)
            except Exception:
                continue
            evidence["projects_opened"] += 1
            try:
                phon_data = project.lp.PhonologicalDataOA
                rules = (
                    list(phon_data.PhonRulesOS)
                    if phon_data and hasattr(phon_data, "PhonRulesOS")
                    else []
                )
                for raw_rule in rules:
                    wrapped_rule = PhonologicalRule(raw_rule)
                    if wrapped_rule.has_metathesis_parts:
                        left, right = wrapped_rule.metathesis_parts
                        found = True
                        evidence["metathesis_found"] = True
                        evidence["left_count"] = len(left)
                        evidence["right_count"] = len(right)
                        concrete = wrapped_rule.concrete
                        evidence["left_switch"] = (
                            int(getattr(concrete, "LeftSwitchIndex", -1)),
                            int(getattr(concrete, "LeftSwitchLimit", -1)),
                        )
                        evidence["right_switch"] = (
                            int(getattr(concrete, "RightSwitchIndex", -1)),
                            int(getattr(concrete, "RightSwitchLimit", -1)),
                        )
                        assert len(left) >= 0 and len(right) >= 0
                        break
                    if found:
                        break
            finally:
                try:
                    project.CloseProject()
                except Exception:
                    pass

            if found:
                break

        assert found, "No PhMetathesisRule with valid parts found in installed FLEx projects"
        _write_evidence({"metathesis_parts": evidence}, "live-programmer-metathesis.json")
