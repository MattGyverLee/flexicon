#
#   test_issue724_lexsense_anthrocode_hvo_live.py
#
#   Live verification for issue #724 LexSense AnthroCodesRC HVO membership lookup.
#
#   Runs on the Sena 3 sandbox (Target carries no anthropology codes). If the
#   sandbox has none either, a TEST_-prefixed code is created in the sandbox
#   rather than skipping: a skip is "FAIL: unverified".
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_724_"


def _make_entry(project, suffix):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{suffix}")
    return entry


def _anthro_hvos(sense):
    """Re-query the LCM: HVOs currently in sense.AnthroCodesRC."""
    return [item.Hvo for item in sense.AnthroCodesRC]


def test_issue724_remove_anthro_code_after_hvo_refetch(sena3_sandbox):
    """RemoveAnthroCode unlinks code when caller holds Object(hvo) view."""
    project = sena3_sandbox
    ops = project.Senses
    codes = list(project.Anthropology.GetAll())
    if codes:
        code = codes[0]
    else:
        code = project.Anthropology.Create(f"{TEST_PREFIX}code")
    assert code is not None, "no anthropology code available or creatable"

    entry = _make_entry(project, "anthro_hvo")
    try:
        sense = ops.Create(entry, f"{TEST_PREFIX}g")
        pre_hvos = _anthro_hvos(sense)
        assert code.Hvo not in pre_hvos

        ops.AddAnthroCode(sense, code)
        mid_hvos = _anthro_hvos(sense)
        assert code.Hvo in mid_hvos
        assert len(ops.GetAnthroCodes(sense)) == 1

        bare_code = project.Object(code.Hvo)
        ops.RemoveAnthroCode(sense, bare_code)
        post_hvos = _anthro_hvos(sense)
        assert code.Hvo not in post_hvos
        assert len(ops.GetAnthroCodes(sense)) == 0
        print(f"724-EVIDENCE pre={pre_hvos} mid={mid_hvos} post={post_hvos} code={code.Hvo}")
    finally:
        project.LexEntry.Delete(entry)
