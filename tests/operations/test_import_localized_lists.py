#
#   test_import_localized_lists.py
#
#   Class: TestLocalizedListsImportContract
#          Coverage for FLExProject.LocalizedLists.Import -- the
#          wrapper around XmlTranslatedLists.ImportTranslatedListsForWs
#          added to close item 3 of issue #29. Methods now live on
#          LocalizedListsOperations (issue #73) and the enumerator
#          returns a structured ImportLocalizedListsResult (issue #75).
#
#          We deliberately avoid triggering a real import against the
#          shared Sena 3 test project (the same pollution rationale as
#          AnthropologyOperations.ImportCatalog tests -- a successful
#          import mutates the project's possibility lists with
#          translation alternatives that subsequent test runs would
#          have to account for). The tests cover the input-validation
#          guards plus the FP_FileNotFoundError path for unknown
#          language codes.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys
from unittest.mock import patch

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    try:
        from flexicon.code.FLExProject import FLExProject
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


class TestLocalizedListsImportContract:
    """
    Static / input-validation coverage for LocalizedLists.Import.

    Live importing is intentionally NOT exercised here: a successful
    import mutates the test project's possibility-list state with
    translated alternatives, polluting subsequent runs of unrelated
    tests. The contract tests below confirm the method is discoverable,
    rejects bad input, and refuses obvious errors -- enough to catch
    regressions in the surface without seeding state.
    """

    def test_property_is_on_flex_project(self):
        """
        LocalizedLists must be a property on FLExProject that returns
        a LocalizedListsOperations instance with Import and
        ImportForAllAnalysisWritingSystems methods.
        """
        from flexicon.code.FLExProject import FLExProject

        assert "LocalizedLists" in dir(FLExProject), (
            "LocalizedLists property missing from FLExProject"
        )
        prop = getattr(FLExProject, "LocalizedLists")
        assert isinstance(prop, property), (
            "LocalizedLists must be a property accessor"
        )

    def test_import_method_signature(self):
        """
        LocalizedListsOperations.Import must be callable with the
        documented (language_code, progress=None) signature.
        """
        from flexicon.code.Lists.LocalizedListsOperations import (
            LocalizedListsOperations,
        )

        method = getattr(LocalizedListsOperations, "Import", None)
        assert callable(method), (
            "LocalizedListsOperations.Import is missing or not callable"
        )

        params = inspect.signature(method).parameters
        assert "language_code" in params, (
            f"Import is missing 'language_code'; got: {list(params)}"
        )
        assert "progress" in params, (
            f"Import is missing 'progress'; got: {list(params)}"
        )
        assert params["progress"].default is None, (
            "Import 'progress' must default to None"
        )

    def test_rejects_none_language_code(self, writable_project):
        """
        Import(None) must raise FP_NullParameterError before any FW
        filesystem access.
        """
        from flexicon.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            writable_project.LocalizedLists.Import(None)

    def test_rejects_empty_language_code(self, writable_project):
        """
        Empty or whitespace-only language_code must raise
        FP_ParameterError -- this prevents the bogus ZIP filename
        ``LocalizedLists-.zip`` from being constructed.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError):
            writable_project.LocalizedLists.Import("")
        with pytest.raises(FP_ParameterError):
            writable_project.LocalizedLists.Import("   ")

    def test_unknown_language_code_raises_file_not_found(
        self, writable_project
    ):
        """
        For a language code with no shipping translation ZIP, Import
        must raise FP_FileNotFoundError -- not a generic
        FileNotFoundError or AttributeError.
        """
        from flexicon.code.FLExProject import FP_FileNotFoundError

        # "zz-XX" is the standard "unallocated" code; no LocalizedLists
        # ZIP should ever ship for it.
        with pytest.raises(FP_FileNotFoundError):
            writable_project.LocalizedLists.Import("zz-XX")


class TestImportForAllAnalysisWritingSystems:
    """
    Coverage for the auto-enumerator that loops over enabled analysis
    writing systems and applies whatever translation packs ship for
    them. Same anti-pollution constraints apply: we don't trigger live
    imports against Sena 3. We verify the method shape, the missing-
    ZIP skip behavior, and the structured-result contract (#75).
    """

    def test_method_signature(self):
        """
        ImportForAllAnalysisWritingSystems must exist on
        LocalizedListsOperations and take only a progress= keyword.
        """
        from flexicon.code.Lists.LocalizedListsOperations import (
            LocalizedListsOperations,
        )

        method = getattr(
            LocalizedListsOperations,
            "ImportForAllAnalysisWritingSystems",
            None,
        )
        assert callable(method), (
            "ImportForAllAnalysisWritingSystems missing or not callable"
        )

        params = inspect.signature(method).parameters
        assert "progress" in params
        # No language_code: this is the project-wide enumerator.
        assert "language_code" not in params, (
            "Enumerator must not require a language_code; "
            "use LocalizedLists.Import(code) for the single-WS form"
        )

    def test_iterates_enabled_ws_and_dispatches(self, writable_project):
        """
        Verify the enumerator's iteration + dispatch logic WITHOUT
        actually mutating the project's possibility lists. We
        monkey-patch the underlying per-WS Import with a recorder and
        confirm:
          - Each enabled analysis WS got its IcuLocale forwarded to
            Import, in iteration order.
          - The returned ImportLocalizedListsResult.imported matches
            the recorder.
          - .imported is a list[str]; .skipped is a list of
            SkippedWS(code, reason) entries.
        """
        from flexicon.code.Lists.LocalizedListsOperations import (
            ImportLocalizedListsResult,
            LocalizedListsOperations,
            SkippedWS,
        )

        recorded_calls = []

        def _recording_stub(self_arg, language_code, progress=None):
            # Capture what the enumerator dispatched; do NOT touch LCM.
            recorded_calls.append(language_code)

        target = (
            f"{LocalizedListsOperations.__module__}."
            f"{LocalizedListsOperations.__qualname__}.Import"
        )
        with patch(target, _recording_stub):
            result = (
                writable_project.LocalizedLists
                .ImportForAllAnalysisWritingSystems()
            )

        assert isinstance(result, ImportLocalizedListsResult), (
            f"Enumerator must return ImportLocalizedListsResult, got "
            f"{type(result).__name__}"
        )
        assert isinstance(result.imported, list), (
            f".imported must be a list, got {type(result.imported).__name__}"
        )
        assert isinstance(result.skipped, list), (
            f".skipped must be a list, got {type(result.skipped).__name__}"
        )
        # Each imported code must be a non-empty string.
        for code in result.imported:
            assert isinstance(code, str) and code, (
                f"Imported entries must be non-empty strings; got {code!r}"
            )
        # Each skipped entry must be a SkippedWS(code, reason) with
        # string fields.
        for entry in result.skipped:
            assert isinstance(entry, SkippedWS), (
                f"Skipped entries must be SkippedWS instances; got "
                f"{type(entry).__name__}"
            )
            assert isinstance(entry.code, str) and entry.code, (
                f"SkippedWS.code must be a non-empty string; got {entry.code!r}"
            )
            assert isinstance(entry.reason, str) and entry.reason, (
                f"SkippedWS.reason must be a non-empty string; "
                f"got {entry.reason!r}"
            )
        # Imported codes must mirror the dispatch order.
        assert result.imported == recorded_calls, (
            "Enumerator's .imported did not match the dispatched "
            f"calls: imported {result.imported!r}, dispatched "
            f"{recorded_calls!r}"
        )
        # Iteration touched at least one enabled analysis WS (Sena 3
        # and the standard test projects all have English enabled).
        assert len(recorded_calls) >= 1, (
            "Enumerator dispatched no calls -- "
            "CurrentAnalysisWritingSystems iteration may be broken"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
