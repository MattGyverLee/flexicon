#
#   test_issue342_missing_accessors.py
#
#   Regression coverage for issue #342: sibling accessor gaps in
#   PhonemeOperations and LexSenseOperations.
#
#   These checks are static/AST based plus isolated behavioral checks run
#   against the methods' own AST. They do not import the real operations
#   modules, which keeps the tests runnable without pythonnet / FieldWorks.
#

import ast
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHONEME_SOURCE = ROOT / "flexicon" / "code" / "Grammar" / "PhonemeOperations.py"
LEXSENSE_SOURCE = ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"


def _parse(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _class_node(tree, class_name, path):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    pytest.fail(f"class {class_name} not found in {path}")


def _method_node(class_node, method_name):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    pytest.fail(f"{method_name} not found in class {class_node.name}")


def _build_method(path, class_name, method_name, globals_dict):
    tree = _parse(path)
    cls = _class_node(tree, class_name, path)
    method = _method_node(cls, method_name)
    method = ast.FunctionDef(
        name=method.name,
        args=method.args,
        body=method.body,
        decorator_list=[],
        returns=method.returns,
        type_comment=method.type_comment,
    )
    synthetic = ast.Module(
        body=[
            ast.ClassDef(
                name=class_name,
                bases=[],
                keywords=[],
                body=[method],
                decorator_list=[],
            )
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(synthetic)
    namespace = {}
    exec(compile(synthetic, str(path), "exec"), globals_dict, namespace)
    return getattr(namespace[class_name], method_name)


def test_phoneme_operations_defines_getname():
    """PhonemeOperations must expose the expected GetName accessor."""
    tree = _parse(PHONEME_SOURCE)
    cls = _class_node(tree, "PhonemeOperations", PHONEME_SOURCE)
    _method_node(cls, "GetName")


def test_phoneme_getname_reads_the_name_multistring():
    """GetName must return the text from phoneme.Name.get_String(...)."""
    method = _build_method(
        PHONEME_SOURCE,
        "PhonemeOperations",
        "GetName",
        {
            "normalize_text": lambda text: text,
            "ITsString": lambda value: value,
        },
    )

    phoneme = Mock()
    phoneme.Name.get_String.return_value = Mock(Text="/p/")

    self_obj = Mock()
    self_obj._ValidateParam = Mock()
    self_obj._PhonemeOperations__GetPhonemeObject = Mock(return_value=phoneme)
    self_obj._PhonemeOperations__WSHandle = Mock(return_value=1)

    assert method(self_obj, phoneme) == "/p/"
    self_obj._ValidateParam.assert_called_once_with(phoneme, "phoneme_or_hvo")
    phoneme.Name.get_String.assert_called_once_with(1)


def test_lexsense_operations_defines_getmsa():
    """LexSenseOperations must expose the expected GetMSA accessor."""
    tree = _parse(LEXSENSE_SOURCE)
    cls = _class_node(tree, "LexSenseOperations", LEXSENSE_SOURCE)
    _method_node(cls, "GetMSA")


def test_lexsense_getmsa_returns_morphosyntaxanalysisra():
    """GetMSA must return the sense's MorphoSyntaxAnalysisRA object."""
    method = _build_method(
        LEXSENSE_SOURCE,
        "LexSenseOperations",
        "GetMSA",
        {},
    )

    msa = Mock()
    sense = Mock(MorphoSyntaxAnalysisRA=msa)

    self_obj = Mock()
    self_obj._ValidateParam = Mock()
    self_obj._LexSenseOperations__GetSenseObject = Mock(return_value=sense)

    assert method(self_obj, sense) is msa
    self_obj._ValidateParam.assert_called_once_with(sense, "sense_or_hvo")


def test_lexsense_getmsa_returns_none_when_missing():
    """GetMSA must return None when a sense has no attached MSA."""
    method = _build_method(
        LEXSENSE_SOURCE,
        "LexSenseOperations",
        "GetMSA",
        {},
    )

    sense = Mock(MorphoSyntaxAnalysisRA=None)

    self_obj = Mock()
    self_obj._ValidateParam = Mock()
    self_obj._LexSenseOperations__GetSenseObject = Mock(return_value=sense)

    assert method(self_obj, sense) is None
