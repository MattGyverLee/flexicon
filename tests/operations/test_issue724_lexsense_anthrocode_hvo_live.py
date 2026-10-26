#
#   test_issue724_lexsense_anthrocode_hvo_live.py
#
#   Live verification for issue #724 LexSense AnthroCodesRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_724_"


def _make_entry(project, suffix):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{suffix}")
    return entry


def test_issue724_remove_anthro_code_after_hvo_refetch(target_sandbox):
    """RemoveAnthroCode unlinks code when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Senses
    anthro_list = project.Anthropology.GetList()
    if anthro_list is None:
        pytest.skip("Target has no anthropology list")
    codes = list(anthro_list.PossibilitiesOS)
    if not codes:
        pytest.skip("Target has no anthropology codes to reference")

    code = codes[0]
    entry = _make_entry(project, "anthro_hvo")
    try:
        sense = ops.Create(entry, f"{TEST_PREFIX}g")
        ops.AddAnthroCode(sense, code)
        assert len(ops.GetAnthroCodes(sense)) == 1

        bare_code = project.Object(code.Hvo)
        ops.RemoveAnthroCode(sense, bare_code)
        assert len(ops.GetAnthroCodes(sense)) == 0
    finally:
        project.LexEntry.Delete(entry)
