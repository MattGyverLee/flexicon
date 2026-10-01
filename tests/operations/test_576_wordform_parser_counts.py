#
#   test_576_wordform_parser_counts.py
#
#   Mock-based tests for issue #576: WordformOperations parser-coverage
#   convenience wrappers GetParserCount / GetUserCount / IsParsed.
#
#   The FieldWorks runtime (clr / SIL.LCModel) is unavailable in this
#   environment, so this module stubs those imports in sys.modules before
#   importing WordformOperations, and exercises the new methods against
#   unittest mocks.
#
#   Copyright 2026
#

import sys
import types
import pathlib
from unittest.mock import MagicMock

import pytest


def _install_offline_stubs():
    """Stub clr/SIL imports and the top-level flexicon package so
    WordformOperations can be imported without the FieldWorks runtime."""
    sys.modules.setdefault("clr", MagicMock())
    for name in (
        "SIL",
        "SIL.LCModel",
        "SIL.LCModel.Core",
        "SIL.LCModel.Core.KernelInterfaces",
        "SIL.LCModel.Core.Text",
    ):
        sys.modules.setdefault(name, MagicMock())

    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    if "flexicon" not in sys.modules:
        # The real flexicon/__init__.py imports FLExInit, which needs the
        # FieldWorks runtime (System). Stub the package with a real __path__
        # so submodule imports still resolve to the repository files.
        flexicon_pkg = types.ModuleType("flexicon")
        flexicon_pkg.__path__ = [str(repo_root / "flexicon")]
        sys.modules["flexicon"] = flexicon_pkg

    if "flexicon.code.FLExProject" not in sys.modules:
        # The real FLExProject imports Windows-only subprocess names.
        # The operations module only needs the exception types from it.
        from flexicon.code.exceptions import FP_ParameterError, FP_NullParameterError

        fake = types.ModuleType("flexicon.code.FLExProject")
        fake.FP_ParameterError = FP_ParameterError
        fake.FP_NullParameterError = FP_NullParameterError
        sys.modules["flexicon.code.FLExProject"] = fake


_install_offline_stubs()

import flexicon.code.TextsWords.WordformOperations as wf_ops_module  # noqa: E402
from flexicon.code.TextsWords.WordformOperations import WordformOperations  # noqa: E402
from flexicon.code.exceptions import FP_NullParameterError  # noqa: E402


def _make_wordform(parser_count=0, user_count=0):
    wf = MagicMock()
    wf.ClassName = "WfiWordform"
    wf.ParserCount = parser_count
    wf.UserCount = user_count
    return wf


@pytest.fixture
def offline_ops(monkeypatch):
    """WordformOperations with the HVO-cast helper pinned to identity.

    Offline, SIL.LCModel is a MagicMock, so the real cast_to_concrete would
    return a mock-of-a-mock instead of the wordform under test. Pinning it
    to identity keeps the resolver behavior (ClassName gate, HVO lookup)
    while making property values deterministic.
    """
    monkeypatch.setattr(wf_ops_module, "cast_to_concrete", lambda obj: obj)
    wf = _make_wordform(parser_count=7, user_count=3)
    project = MagicMock()
    project.Object = MagicMock(return_value=wf)
    ops = WordformOperations(project)
    return ops, project, wf


class TestGetParserCount:
    def test_returns_parser_count_as_int(self, offline_ops):
        ops, _, wf = offline_ops
        assert ops.GetParserCount(wf) == 7

    def test_zero_when_unparsed(self, offline_ops, monkeypatch):
        ops, _, wf = offline_ops
        wf.ParserCount = 0
        assert ops.GetParserCount(wf) == 0

    def test_resolves_hvo_through_project_object(self, offline_ops):
        ops, project, _ = offline_ops
        assert ops.GetParserCount(1234) == 7
        project.Object.assert_called_with(1234)


class TestGetUserCount:
    def test_returns_user_count_as_int(self, offline_ops):
        ops, _, wf = offline_ops
        assert ops.GetUserCount(wf) == 3

    def test_resolves_hvo_through_project_object(self, offline_ops):
        ops, project, _ = offline_ops
        assert ops.GetUserCount(1234) == 3
        project.Object.assert_called_with(1234)


class TestIsParsed:
    def test_true_when_parser_count_positive(self, offline_ops):
        ops, _, wf = offline_ops
        assert ops.IsParsed(wf) is True

    def test_false_when_parser_count_zero(self, offline_ops):
        ops, _, wf = offline_ops
        wf.ParserCount = 0
        assert ops.IsParsed(wf) is False

    def test_matches_get_parser_count_comparison(self, offline_ops):
        ops, _, wf = offline_ops
        for count in (0, 1, 2, 42):
            wf.ParserCount = count
            assert ops.IsParsed(wf) == (ops.GetParserCount(wf) > 0)

    def test_resolves_hvo_through_project_object(self, offline_ops):
        ops, project, _ = offline_ops
        assert ops.IsParsed(1234) is True
        project.Object.assert_called_with(1234)


class TestNullParameter:
    @pytest.mark.parametrize("method_name", ["GetParserCount", "GetUserCount", "IsParsed"])
    def test_none_raises_fp_null_parameter_error(self, offline_ops, method_name):
        ops, _, _ = offline_ops
        with pytest.raises(FP_NullParameterError):
            getattr(ops, method_name)(None)


class TestConventions:
    """Offline ratchets for issue #576 conventions."""

    @pytest.fixture
    def source(self):
        repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
        return (repo_root / "flexicon" / "code" / "TextsWords" / "WordformOperations.py").read_text(
            encoding="utf-8"
        )

    def test_methods_use_operations_method_decorator(self, source):
        for name in ("GetParserCount", "GetUserCount", "IsParsed"):
            idx = source.index(f"def {name}(self, wordform_or_hvo)")
            assert "@OperationsMethod" in source[max(0, idx - 200) : idx]

    def test_methods_validate_null_parameter(self, source):
        for name in ("GetParserCount", "GetUserCount", "IsParsed"):
            idx = source.index(f"def {name}(self, wordform_or_hvo)")
            body = source[idx : idx + 2500]
            assert 'self._ValidateParam(wordform_or_hvo, "wordform_or_hvo")' in body

    def test_docstrings_have_example_and_see_also(self, source):
        for name in ("GetParserCount", "GetUserCount", "IsParsed"):
            idx = source.index(f"def {name}(self, wordform_or_hvo)")
            doc = source[idx : idx + 3500]
            assert "Example:" in doc, name
            assert "See Also:" in doc, name

    def test_is_parsed_docstring_states_exact_parsed_semantics(self, source):
        idx = source.index("def IsParsed(self, wordform_or_hvo)")
        doc = source[idx : idx + 3500]
        # Must state EXACTLY what counts as "parsed": parser evaluations,
        # not approved analyses -- and name the composite it differs from.
        assert "evaluated" in doc
        assert "computer-approved" in doc
        assert "IsComputerApproved" in doc
        assert "GetParserCount(wordform_or_hvo) > 0" in doc

    def test_pyi_stubs_present(self):
        repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
        stub = (
            repo_root / "flexicon" / "code" / "TextsWords" / "WordformOperations.pyi"
        ).read_text(encoding="utf-8")
        assert "def GetParserCount(self, wordform_or_hvo: Any) -> int: ..." in stub
        assert "def GetUserCount(self, wordform_or_hvo: Any) -> int: ..." in stub
        assert "def IsParsed(self, wordform_or_hvo: Any) -> bool: ..." in stub
