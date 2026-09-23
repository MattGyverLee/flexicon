#
#   test_issue359_anthropology_gsp_live.py
#
#   Live read-only coverage for issue #359: AnthroCode sync key from Abbreviation.
#
#   Copyright 2026
#

import pytest


@pytest.mark.requires_live_project
def test_get_syncable_properties_anthro_code_from_abbreviation(sena3_sandbox):
    project = sena3_sandbox
    items = project.Anthropology.GetAll()
    if not items:
        pytest.skip("no anthropology items in Sena 3 sandbox")

    for item in items[:20]:
        props = project.Anthropology.GetSyncableProperties(item)
        assert isinstance(props, dict)
        assert "AnthroCode" in props
        assert "Category" in props
        assert props["Category"] is None
        abbr = props.get("Abbreviation") or ""
        anthro_code = props.get("AnthroCode")
        if abbr:
            assert anthro_code == abbr
