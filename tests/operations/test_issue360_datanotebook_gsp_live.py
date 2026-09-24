#
#   test_issue360_datanotebook_gsp_live.py
#
#   Live read-only coverage for issue #360: GetSyncableProperties on notebook records.
#
#   Copyright 2026
#

import pytest


@pytest.mark.requires_live_project
def test_get_syncable_properties_on_all_data_notebook_records(sena3_sandbox):
    project = sena3_sandbox
    records = project.DataNotebook.GetAll()
    if not records:
        pytest.skip("Sena 3 sandbox has no data notebook records")

    expected_keys = {
        "Title",
        "Text",
        "Type",
        "Status",
        "Confidence",
        "DateOfEvent",
    }
    for record in records:
        props = project.DataNotebook.GetSyncableProperties(record)
        assert isinstance(props, dict)
        assert expected_keys <= set(props.keys())
