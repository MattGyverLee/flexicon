#
#   test_issue329_datanotebook_ra.py
#
#   Class: TestIssue329DataNotebookRaStaticLock
#          TestIssue329DataNotebookStatusRoundTripLive
#
#   Issue #329: DataNotebookOperations used bare Status/Type/Confidence on
#   IRnGenericRec; LCM members are StatusRA/TypeRA/ConfidenceRA.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
from pathlib import Path

import pytest

TEST_PREFIX = "TEST_329_"

_RECORD_LOCALS = frozenset(
    {"record", "source", "duplicate", "source_rec", "dup_rec"}
)
_FORBIDDEN_ATTRS = frozenset({"Type", "Status", "Confidence"})


def _make_toplevel_record(project, title):
    from SIL.LCModel import IRnGenericRecFactory
    from SIL.LCModel.Core.Text import TsStringUtils

    factory = project.project.ServiceLocator.GetService(IRnGenericRecFactory)
    ws = project.project.DefaultAnalWs

    record = factory.Create()
    project.lp.ResearchNotebookOA.RecordsOC.Add(record)
    record.Title = TsStringUtils.MakeString(title, ws)
    return record


class TestIssue329DataNotebookRaStaticLock:
    """Offline ratchet: no phantom bare Type/Status/Confidence on records."""

    def test_record_attrs_use_ra_suffix_in_module(self):
        module_path = (
            Path(__file__).resolve().parents[2]
            / "flexicon/code/Notebook/DataNotebookOperations.py"
        )
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr not in _FORBIDDEN_ATTRS:
                    continue
                if isinstance(node.value, ast.Name) and node.value.id in _RECORD_LOCALS:
                    violations.append((node.lineno, node.attr, node.value.id))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id != "hasattr" or len(node.args) < 2:
                    continue
                obj, name = node.args[0], node.args[1]
                if (
                    isinstance(obj, ast.Name)
                    and obj.id in _RECORD_LOCALS
                    and isinstance(name, ast.Constant)
                    and name.value in _FORBIDDEN_ATTRS
                ):
                    violations.append((node.lineno, name.value, obj.id))

        assert not violations, (
            "Bare Type/Status/Confidence on record locals (use *RA): "
            + ", ".join(f"L{ln} {attr} on {var}" for ln, attr, var in violations)
        )


@pytest.mark.requires_live_project
class TestIssue329DataNotebookStatusRoundTripLive:
    @pytest.mark.live_phase("DataNotebookOperations", "set_status")
    def test_set_status_reread_by_hvo_and_sync_props(self, target_sandbox):
        notebook = target_sandbox.DataNotebook
        statuses = notebook.GetAllStatuses()
        if not statuses:
            pytest.skip("Target has no notebook status possibilities")

        record = _make_toplevel_record(
            target_sandbox, f"{TEST_PREFIX}status_roundtrip"
        )
        hvo = int(record.Hvo)
        chosen = statuses[0]

        try:
            notebook.SetStatus(hvo, chosen)
            reread = notebook.GetStatus(hvo)
            assert reread is not None
            assert reread.Hvo == chosen.Hvo

            props = notebook.GetSyncableProperties(hvo)
            assert props["Status"] == str(chosen.Guid)
        finally:
            target_sandbox.lp.ResearchNotebookOA.RecordsOC.Remove(record)
