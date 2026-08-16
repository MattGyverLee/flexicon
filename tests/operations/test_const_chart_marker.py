#
#   test_const_chart_marker.py
#
#   Class: TestConstChartMarkerCRUD / TestConstChartMarkerHierarchy /
#          TestConstChartMarkerReorderGuard / TestMigrationFromTag
#          Behavioural coverage for ConstChartMarkerOperations after
#          the ChartTag -> ChartMarker rename and scope cleanup.
#          Replaces the prior static-grep test file.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


def _delete_marker_by_name(project, name):
    """Best-effort cleanup of a test marker by name (any depth)."""
    found = project.ConstChartMarkers.Find(name)
    if found is not None:
        try:
            project.ConstChartMarkers.Delete(found)
        except Exception:
            pass


class TestConstChartMarkerCRUD:
    """
    Round-trip Create -> Find -> Delete against the project-wide
    DiscourseDataOA.ChartMarkersOA list. Pins the post-refactor API
    shape (no chart_or_hvo, project-wide scope) and the auto-init
    behaviour for fresh projects.
    """

    def test_create_then_find_round_trips(self, writable_project):
        name = "qZ_marker_roundtrip"
        _delete_marker_by_name(writable_project, name)

        created = writable_project.ConstChartMarkers.Create(name)
        try:
            assert created is not None, "Create returned None"

            found = writable_project.ConstChartMarkers.Find(name)
            assert found is not None, "Find returned None for created marker"
            assert found.Hvo == created.Hvo, (
                f"Find returned wrong marker: "
                f"created Hvo={created.Hvo}, found Hvo={found.Hvo}"
            )

            name_back = writable_project.ConstChartMarkers.GetName(created)
            assert name_back == name, (
                f"GetName returned {name_back!r}, expected {name!r}"
            )
        finally:
            writable_project.ConstChartMarkers.Delete(created)

    def test_find_returns_none_for_missing(self, writable_project):
        result = writable_project.ConstChartMarkers.Find(
            "qZ_definitely_does_not_exist_marker"
        )
        assert result is None

    def test_create_no_chart_arg(self, writable_project):
        """
        Issue #47: Create takes only the name. The pre-refactor API
        accepted a chart_or_hvo arg that was silently discarded after
        the issue #26 fix. Pin the new signature.
        """
        import inspect

        from flexlibs2.code.Discourse.ConstChartMarkerOperations import (
            ConstChartMarkerOperations,
        )

        sig = inspect.signature(ConstChartMarkerOperations.Create)
        params = [
            p.name for p in sig.parameters.values()
            if p.name not in ("self", "args", "kwargs")
        ]
        assert "name" in params or len(params) == 1, (
            f"Create signature should be Create(self, name); got params {params}"
        )
        # And no parameter looks like a chart reference.
        for name in ("chart", "chart_or_hvo", "chart_hvo"):
            assert name not in params, (
                f"Create still accepts a chart-reference param "
                f"({name!r}); the issue #47 cleanup did not land"
            )

    def test_set_and_get_description(self, writable_project):
        name = "qZ_marker_desc"
        _delete_marker_by_name(writable_project, name)

        marker = writable_project.ConstChartMarkers.Create(name)
        try:
            assert (
                writable_project.ConstChartMarkers.GetDescription(marker)
                == ""
            )
            writable_project.ConstChartMarkers.SetDescription(
                marker, "Used by qZ tests"
            )
            assert (
                writable_project.ConstChartMarkers.GetDescription(marker)
                == "Used by qZ tests"
            )
        finally:
            writable_project.ConstChartMarkers.Delete(marker)


class TestConstChartMarkerHierarchy:
    """
    Issue #48: Find and GetAll must walk SubPossibilitiesOS so
    hierarchical markers ("Topic > Contrastive Topic") are reachable.
    The pre-refactor code iterated only the top-level PossibilitiesOS.
    """

    def test_find_locates_sub_marker(self, writable_project):
        from SIL.LCModel import ICmPossibilityFactory
        from SIL.LCModel.Core.Text import TsStringUtils

        parent_name = "qZ_topic_parent"
        child_name = "qZ_topic_contrastive"
        _delete_marker_by_name(writable_project, parent_name)
        _delete_marker_by_name(writable_project, child_name)

        parent = writable_project.ConstChartMarkers.Create(parent_name)
        try:
            # Add a sub-marker via raw LCM (the wrapper's Create is
            # top-level only; sub-marker creation is a separate API
            # surface we don't wrap yet).
            sl = writable_project.project.ServiceLocator
            sub_factory = sl.GetService(ICmPossibilityFactory)
            # Raw LCM writes -> own unit of work (tasks.md D14). Create,
            # attach and name are one unit: a half-built child marker would
            # be found by the very GetAll/Find this test then asserts on.
            with writable_project.UndoableOperation("test: build sub-marker"):
                child = sub_factory.Create()
                parent.SubPossibilitiesOS.Add(child)
                ws = writable_project.project.DefaultAnalWs
                child.Name.set_String(
                    ws, TsStringUtils.MakeString(child_name, ws)
                )

            found = writable_project.ConstChartMarkers.Find(child_name)
            assert found is not None, (
                "Find should walk into SubPossibilitiesOS (issue #48); "
                f"could not locate child marker {child_name!r}"
            )
            assert found.Hvo == child.Hvo
        finally:
            writable_project.ConstChartMarkers.Delete(parent)

    def test_get_all_includes_sub_markers(self, writable_project):
        from SIL.LCModel import ICmPossibilityFactory
        from SIL.LCModel.Core.Text import TsStringUtils

        parent_name = "qZ_topic_parent_getall"
        child_name = "qZ_topic_child_getall"
        _delete_marker_by_name(writable_project, parent_name)
        _delete_marker_by_name(writable_project, child_name)

        parent = writable_project.ConstChartMarkers.Create(parent_name)
        try:
            sl = writable_project.project.ServiceLocator
            sub_factory = sl.GetService(ICmPossibilityFactory)
            # Raw LCM writes -> own unit of work (tasks.md D14). Create,
            # attach and name are one unit: a half-built child marker would
            # be found by the very GetAll/Find this test then asserts on.
            with writable_project.UndoableOperation("test: build sub-marker"):
                child = sub_factory.Create()
                parent.SubPossibilitiesOS.Add(child)
                ws = writable_project.project.DefaultAnalWs
                child.Name.set_String(
                    ws, TsStringUtils.MakeString(child_name, ws)
                )

            all_markers = list(writable_project.ConstChartMarkers.GetAll())
            hvos = [m.Hvo for m in all_markers]
            assert parent.Hvo in hvos, "Parent marker missing from GetAll"
            assert child.Hvo in hvos, (
                "Sub-marker missing from GetAll -- the hierarchy walk "
                "didn't include nested SubPossibilitiesOS (issue #48)"
            )
        finally:
            writable_project.ConstChartMarkers.Delete(parent)


class TestConstChartMarkerReorderGuard:
    """
    Issue #52: inherited MoveUp / MoveDown / Reorder would silently
    reorder the project-wide marker list. _GetSequence now raises
    NotImplementedError; the inherited methods inherit the raise.
    """

    def test_get_sequence_raises_not_implemented(self, writable_project):
        with pytest.raises(NotImplementedError) as exc_info:
            writable_project.ConstChartMarkers._GetSequence(None)
        msg = str(exc_info.value).lower()
        assert "project-wide" in msg or "shared" in msg, (
            "NotImplementedError message should explain the project-wide "
            f"concern; got: {exc_info.value!r}"
        )


class TestConstChartMarkerMigrationFromTag:
    """
    Issue #46: ConstChartTags accessor and ConstChartTagOperations
    class were removed in favour of ConstChartMarkers. Pin that the
    old surface is gone so a regression that re-introduces an alias
    fails loudly.
    """

    def test_old_attribute_is_gone(self, writable_project):
        assert not hasattr(writable_project, "ConstChartTags"), (
            "FLExProject.ConstChartTags should be removed; an alias "
            "would reintroduce the ChartMarker/ChartTag conflation."
        )

    def test_old_module_is_gone(self):
        with pytest.raises(ImportError):
            from flexlibs2.code.Discourse.ConstChartTagOperations import (  # noqa: F401
                ConstChartTagOperations,
            )

    def test_new_accessor_present(self, writable_project):
        assert hasattr(writable_project, "ConstChartMarkers")
        assert hasattr(writable_project, "ConstChartCellTags"), (
            "ConstChartCellTags accessor (issue #49) should be wired up"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
