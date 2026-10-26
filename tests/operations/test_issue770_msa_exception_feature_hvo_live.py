#
#   test_issue770_msa_exception_feature_hvo_live.py
#
#   Live verification for issue #770 MSA exception-feature RC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_770_"


def _pos(project):
    pos_list = list(project.POS.GetAll())
    assert pos_list, "Target sandbox has no POS entries"
    return pos_list[0]


def _sense(project, label):
    entry = project.LexEntry.Create(
        f"{TEST_PREFIX}{label}", create_blank_sense=False
    )
    return project.Senses.Create(entry, f"{TEST_PREFIX}{label}_gloss")


def test_issue770_remove_exception_feature_after_hvo_refetch(target_sandbox):
    """RemoveExceptionFeature unlinks feature when caller holds Object(hvo) view."""
    project = target_sandbox
    feat = project.InflectionFeatures.ExceptionFeatureCreate(
        f"{TEST_PREFIX}exc", f"{TEST_PREFIX}exc"
    )
    sense = _sense(project, "stem")
    entry = project.Senses.GetOwningEntry(sense)
    try:
        msa = project.MSA.CreateStem(sense, _pos(project))
        project.MSA.AddExceptionFeature(msa, feat)
        assert len(project.MSA.GetExceptionFeatures(msa)) == 1

        bare_feat = project.Object(feat.Hvo)
        project.MSA.RemoveExceptionFeature(msa, bare_feat)
        assert project.MSA.GetExceptionFeatures(msa) == []
    finally:
        project.LexEntry.Delete(entry)


def test_issue770_add_exception_feature_skips_duplicate_hvo_view(target_sandbox):
    """AddExceptionFeature is a no-op when an alternate view shares the same Hvo."""
    project = target_sandbox
    feat = project.InflectionFeatures.ExceptionFeatureCreate(
        f"{TEST_PREFIX}dup", f"{TEST_PREFIX}dup"
    )
    sense = _sense(project, "stem2")
    entry = project.Senses.GetOwningEntry(sense)
    try:
        msa = project.MSA.CreateStem(sense, _pos(project))
        project.MSA.AddExceptionFeature(msa, feat)
        bare_feat = project.Object(feat.Hvo)
        project.MSA.AddExceptionFeature(msa, bare_feat)
        assert len(project.MSA.GetExceptionFeatures(msa)) == 1
    finally:
        project.LexEntry.Delete(entry)
