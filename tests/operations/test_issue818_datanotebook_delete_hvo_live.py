#
#   test_issue818_datanotebook_delete_hvo_live.py
#
#   Live verification for issue #818 DataNotebookOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue818_delete_top_level_by_hvo(target_project):
    """Delete removes a top-level notebook record after re-fetching by HVO."""
    project = target_project
    title = "TEST_818_delete_hvo"
    record = project.DataNotebook.Create(title)
    try:
        hvo = record.Hvo
        bare_view = project.Object(hvo)
        project.DataNotebook.Delete(bare_view)
        assert project.DataNotebook.Find(title) is None
    finally:
        found = project.DataNotebook.Find(title)
        if found is not None:
            project.DataNotebook.Delete(found)
