#
#   test_issue778_msa_changeaffix_hvo_live.py
#
#   Live verification for issue #778 ChangeAffixVariant exception-feature copy.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_778_"


def _first_pos(project):
    for pos in project.POS.GetAll():
        return pos
    return None


class TestIssue778MsaChangeAffixVariantHvoLive:
    """ChangeAffixVariant must copy FromProdRestrictRC by HVO, not proxy identity."""

    @pytest.mark.live_phase("MSAOperations", "modify")
    def test_infl_to_deriv_copies_exception_features_for_raw_msa(self, target_sandbox):
        project = target_sandbox
        pos = _first_pos(project)
        if pos is None:
            pytest.skip("no POS in sandbox")

        lexeme = f"{TEST_PREFIX}prefix"
        existing = project.LexEntry.Find(lexeme)
        if existing is not None:
            project.LexEntry.Delete(existing)
        entry = project.LexEntry.Create(lexeme, morph_type_name="prefix")
        sense = list(entry.SensesOS)[0]
        project.Senses.SetPartOfSpeech(sense, pos, msa_kind="infl")
        infl_msa = sense.MorphoSyntaxAnalysisRA

        feat = project.InflectionFeatures.ExceptionFeatureCreate(
            f"{TEST_PREFIX}exc", f"{TEST_PREFIX}exc"
        )
        project.MSA.AddExceptionFeature(infl_msa, feat)
        assert len(project.MSA.GetExceptionFeatures(infl_msa)) == 1

        try:
            infl_raw = project.Object(infl_msa.Hvo)
            new_msa = project.MSA.ChangeAffixVariant(infl_raw, "deriv")
            copied = project.MSA.GetExceptionFeatures(new_msa)
            assert len(copied) == 1, (
                "exception feature not copied after infl->deriv with Object(hvo) MSA"
            )
        finally:
            project.LexEntry.Delete(entry)
