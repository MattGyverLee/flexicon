#
#   test_issue816_phonfeature_delete_hvo_live.py
#
#   Live verification for issue #816 PhonFeatureOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_816_"


def _feature_hvos(phon_ops):
    return {int(f.Hvo) for f in phon_ops.GetAll()}


def test_issue816_delete_removes_from_featuresoc_by_hvo(target_sandbox):
    """Delete removes a feature when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    phon_ops = project.PhonFeatures
    keep = phon_ops.Create(f"{TEST_PREFIX}keep", "K")
    victim = phon_ops.Create(f"{TEST_PREFIX}victim", "V")
    try:
        hvo = victim.Hvo
        bare_view = project.Object(hvo)
        before = _feature_hvos(phon_ops)

        phon_ops.Delete(bare_view)

        after = _feature_hvos(phon_ops)
        assert hvo not in after
        assert keep.Hvo in after
        assert before - after == {int(hvo)}
    finally:
        for feat in list(phon_ops.GetAll()):
            name = phon_ops.GetName(feat)
            if name and name.startswith(TEST_PREFIX):
                phon_ops.Delete(feat)


def test_issue816_delete_value_removes_from_valuesoc_by_hvo(target_sandbox):
    """DeleteValue removes a value when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    phon_ops = project.PhonFeatures
    feat = phon_ops.Create(f"{TEST_PREFIX}feat", "F")
    try:
        plus = phon_ops.CreateValue(feat, f"{TEST_PREFIX}plus", "+")
        minus = phon_ops.CreateValue(feat, f"{TEST_PREFIX}minus", "-")
        hvo = minus.Hvo
        bare_view = project.Object(hvo)

        phon_ops.DeleteValue(bare_view)

        remaining = {int(v.Hvo) for v in phon_ops.GetValues(feat)}
        assert int(plus.Hvo) in remaining
        assert int(hvo) not in remaining
    finally:
        phon_ops.Delete(feat)
