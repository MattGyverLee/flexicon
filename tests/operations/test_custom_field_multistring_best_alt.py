#
#   test_custom_field_multistring_best_alt.py
#
#   Regression test for issue #224:
#   FLExProject.GetCustomFieldValue, in the CellarMultiStringTypes branch,
#   used to call `mua.BestAnalysisVernacularAlternative` when
#   `languageTagOrHandle` was None. `mua` (from
#   DomainDataByFlid.get_MultiStringProp) is a bare ITsMultiString
#   (SIL.LCModel.Core.KernelInterfaces), which does NOT implement
#   IMultiAccessorBase -- so it has no BestAnalysisVernacularAlternative
#   accessor, only get_String(wsHandle), StringCount and
#   GetStringFromIndex(i, out ws). Calling the missing accessor raised
#   AttributeError.
#
#   After the fix, the branch calls the new
#   Shared.string_utils.best_multistring_alternative() helper, which
#   reimplements the "best available alternative" priority walk on top of
#   get_String(), and always returns an ITsString (falling back to an
#   empty ITsString if every writing system is unset).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# This test opens a real .fwdata project to locate (or fail to locate) a
# pre-existing MultiString custom field. Custom fields cannot be created
# programmatically from a clean UoW (see issues #20/#21), so this test
# depends on the target project already having one configured via the
# FLEx UI.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")
_CANDIDATE_CLASSES = ("LexEntry", "LexSense", "LexExampleSentence", "MoForm")


def _try_open_project():
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=False)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def readonly_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = _try_open_project()
    if project is None:
        pytest.skip(
            "No FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


def _find_multistring_field(project):
    """
    Search the candidate classes for an existing MultiString/MultiUnicode
    custom field and an object of the matching class to test against.

    Returns:
        (obj, field_id, class_name) tuple, or None if no such field/object
        pair could be found in this project.
    """
    for class_name in _CANDIDATE_CLASSES:
        try:
            fields = project.CustomFields.GetAllFields(class_name)
        except Exception:
            continue

        for field_id, _label in fields:
            if not project.CustomFields.IsMultiString(field_id):
                continue

            obj = None
            if class_name == "LexEntry":
                obj = next(iter(project.LexiconAllEntries()), None)
            elif class_name == "LexSense":
                for entry in project.LexiconAllEntries():
                    senses = list(entry.SensesOS)
                    if senses:
                        obj = senses[0]
                        break
            if obj is None:
                continue

            return obj, field_id, class_name

    return None


class TestCustomFieldMultiStringBestAlternative:
    """
    Regression coverage for issue #224: GetCustomFieldValue must not raise
    AttributeError on a bare ITsMultiString when languageTagOrHandle is None,
    and must always return an ITsString.
    """

    def test_get_custom_field_value_multistring_none_returns_itsstring(
        self, readonly_project
    ):
        """
        GetCustomFieldValue(obj, field_id, None) on a MultiString custom
        field must return an ITsString and must not raise AttributeError.
        """
        found = _find_multistring_field(readonly_project)
        if found is None:
            pytest.skip(
                "No pre-existing MultiString custom field with a populated "
                "object found in the available test project(s). This test "
                "requires a project configured via the FLEx UI with at "
                "least one MultiString custom field (see issues #20/#21 for "
                "why custom fields can't be created programmatically here)."
            )

        obj, field_id, class_name = found

        from SIL.LCModel.Core.KernelInterfaces import ITsString

        try:
            result = readonly_project.GetCustomFieldValue(obj, field_id, None)
        except AttributeError as e:
            raise AssertionError(
                "GetCustomFieldValue must not raise AttributeError when "
                f"languageTagOrHandle is None (class={class_name}, "
                f"field_id={field_id}): {e}"
            )

        assert isinstance(result, ITsString), (
            "GetCustomFieldValue must always return an ITsString for "
            f"MultiString fields, even on a total WS miss; got {type(result)}"
        )
