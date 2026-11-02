#
#   test_issue846_featurestructure_delete_hvo_live.py
#
#   Live verification for issue #846 FeatureStructureDelete HVO slot match.
#
#   Copyright 2026
#

import pytest

from flexicon import cast_to_concrete

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_846_"


def _phoneme_without_features(phon_ops):
    for phoneme in phon_ops.GetAll():
        concrete = cast_to_concrete(phoneme)
        if hasattr(concrete, "FeaturesOA") and concrete.FeaturesOA is None:
            return concrete
    return None


def test_issue846_feature_structure_delete_by_hvo(target_project):
    """FeatureStructureDelete clears FeaturesOA after re-fetching fs by HVO."""
    project = target_project
    infl_ops = project.InflectionFeatures
    phon_ops = project.Phoneme

    phoneme = _phoneme_without_features(phon_ops)
    if phoneme is None:
        pytest.skip("No phoneme with empty FeaturesOA in Target project")

    fs = infl_ops.FeatureStructureCreate()
    fs_hvo = fs.Hvo
    phoneme_hvo = phoneme.Hvo

    try:
        with infl_ops._TransactionCM(f"{TEST_PREFIX}attach feature structure"):
            phoneme.FeaturesOA = fs

        bare_fs = project.Object(fs_hvo)
        infl_ops.FeatureStructureDelete(bare_fs)

        reread = cast_to_concrete(project.Object(phoneme_hvo))
        assert reread.FeaturesOA is None, (
            "FeaturesOA should be cleared when Delete matches slot by HVO"
        )
    finally:
        reread = cast_to_concrete(project.Object(phoneme_hvo))
        if reread.FeaturesOA is not None:
            with infl_ops._TransactionCM(f"{TEST_PREFIX}cleanup feature structure"):
                reread.FeaturesOA = None
