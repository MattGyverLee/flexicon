#
#   test_issue678_annotationdef_delete_hvo_live.py
#
#   Live verification for issue #678 AnnotationDef Delete HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue678_delete_removes_from_list_by_hvo(target_project):
    """Delete removes a custom annotation def after re-fetching by HVO."""
    project = target_project
    ops = project.AnnotationDef
    name = "TEST_678_delete_hvo"
    created = ops.Create(name, 0)
    try:
        hvo = created.Hvo
        bare_view = project.Object(hvo)
        ops.Delete(bare_view)
        remaining = [d for d in ops.GetAll() if d.Hvo == hvo]
        assert remaining == []
    finally:
        for d in ops.GetAll():
            if ops.GetName(d) == name:
                ops.Delete(d)
