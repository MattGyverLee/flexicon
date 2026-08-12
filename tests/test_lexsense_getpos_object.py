#
#   test_lexsense_getpos_object.py
#
#   Regression coverage for LexSenseOperations.GetPartOfSpeechObject
#   (issue #232).
#
#   sense.MorphoSyntaxAnalysisRA is the BASE interface
#   IMoMorphSynAnalysis, which does NOT declare PartOfSpeechRA -- that
#   property only exists on the four concrete MSA subtypes
#   (MoStemMsa, MoInflAffMsa, MoDerivAffMsa, MoUnclassifiedAffixMsa).
#   The previous implementation did
#       return getattr(msa, "PartOfSpeechRA", None)
#   directly on the base interface, which silently returned None for
#   EVERY sense. The fix delegates to lcm_casting.get_pos_from_msa(),
#   which casts to the correct concrete subtype first.
#
#   These checks are static (AST based) plus mock-based behavioral
#   checks run against an isolated copy of the method's own AST (not
#   the real module). This is NOT the same technique as
#   test_agent_version_unicode.py (that file is pure static AST with
#   no exec step). The reason for the exec-based harness here: three
#   sibling test files (test_affix_template_wrappers.py,
#   test_annotation_wrappers.py, test_prohibition_wrappers.py) stub
#   sys.modules["SIL"] = MagicMock() at module scope; conftest.py:41-52
#   documents that this stub poisons the real CLR SIL namespace for any
#   later real import of flexlibs2/flexicon modules in the same
#   process (that's why those three files are in collect_ignore there).
#   To stay import-safe regardless of test run order/composition, and
#   without requiring a real FieldWorks install, this file never
#   imports LexSenseOperations directly -- it extracts
#   GetPartOfSpeechObject's own AST and execs it into an isolated
#   synthetic module instead.
#

import ast
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
)
LCM_CASTING_SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "flexicon" / "code" / "lcm_casting.py"
)

CLASS_NAME = "LexSenseOperations"
METHOD_NAME = "GetPartOfSpeechObject"
# Historical local name that used to hold the (now-removed) duplicated
# literal in LexSenseOperations.py -- kept only so the "must not come back"
# test below can name what it is checking for the absence of.
POS_CLASSES_CONST_NAME = "_POS_BEARING_MSA_CLASSES"
# Canonical name, now defined once in lcm_casting.py and imported by
# LexSenseOperations.py (issue #232 P1 followup).
POS_BEARING_CONST_NAME = "POS_BEARING_MSA_CLASSES"
# lcm_casting.py's dispatch table that get_pos_from_msa() reads and that
# POS_BEARING_MSA_CLASSES is derived from (frozenset(_MSA_POS_PROPERTY)).
MSA_POS_PROPERTY_CONST_NAME = "_MSA_POS_PROPERTY"


def _source_tree():
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


def _lcm_casting_tree():
    return ast.parse(LCM_CASTING_SOURCE_PATH.read_text(encoding="utf-8"))


def _class_node(tree, name=CLASS_NAME):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    pytest.fail("class %s not found in %s" % (name, SOURCE_PATH))


def _method_node(class_node, name=METHOD_NAME):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    pytest.fail("%s not found in class %s" % (name, class_node.name))


def _module_level_assign(tree, target_name):
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == target_name:
                return node
    pytest.fail("module-level assignment %s not found" % target_name)


def _get_pos_from_msa_calls(func_node):
    return [
        node
        for node in ast.walk(func_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "get_pos_from_msa"
    ]


def _getattr_calls_reading_pos_ra(func_node):
    """
    Return getattr(...) calls whose second argument is the literal
    string "PartOfSpeechRA" -- the buggy base-interface read this fix
    removes. getattr(msa, "ClassName", None) is deliberately NOT
    matched (that's the legitimate subtype dispatch check added by
    this fix).
    """
    offenders = []
    for node in ast.walk(func_node):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr"):
            continue
        if len(node.args) < 2:
            continue
        second_arg = node.args[1]
        if isinstance(second_arg, ast.Constant) and second_arg.value == "PartOfSpeechRA":
            offenders.append(node)
    return offenders


# ---------------------------------------------------------------------------
# Static (AST) assertions against the real source file
# ---------------------------------------------------------------------------


def test_no_longer_reads_pos_ra_directly_off_the_base_msa_interface():
    """The base-interface getattr(msa, "PartOfSpeechRA", ...) read must be gone."""
    tree = _source_tree()
    func = _method_node(_class_node(tree))

    offenders = _getattr_calls_reading_pos_ra(func)

    assert not offenders, (
        "%s still reads PartOfSpeechRA via getattr() directly off the base "
        "IMoMorphSynAnalysis interface; delegate to get_pos_from_msa() "
        "instead (issue #232)" % METHOD_NAME
    )


def test_delegates_to_get_pos_from_msa():
    """The fixed method must delegate POS extraction to get_pos_from_msa()."""
    tree = _source_tree()
    func = _method_node(_class_node(tree))

    calls = _get_pos_from_msa_calls(func)

    assert calls, "%s must call get_pos_from_msa() (issue #232, ruling R1)" % METHOD_NAME


def test_get_pos_from_msa_is_imported():
    """get_pos_from_msa must be imported at module scope for the delegation to work."""
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "get_pos_from_msa" in source.split("class %s" % CLASS_NAME, 1)[0], (
        "get_pos_from_msa does not appear to be imported before the class body"
    )


def test_lexsense_no_longer_defines_its_own_msa_class_list():
    """
    LexSenseOperations.py must NOT re-literalize the POS-bearing MSA
    class-name list as its own module-level assignment. That duplication
    (removed by the issue #232 P1 followup) is exactly what let this file's
    allowlist silently diverge from lcm_casting.get_pos_from_msa()'s
    dispatch table.
    """
    tree = _source_tree()

    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == POS_CLASSES_CONST_NAME:
                pytest.fail(
                    "%s still defines its own module-level %s assignment; "
                    "the allowlist must be imported from lcm_casting instead "
                    "(issue #232 P1 followup)" % (SOURCE_PATH.name, POS_CLASSES_CONST_NAME)
                )


def test_lexsense_imports_pos_bearing_classes_from_lcm_casting():
    """The recognized-subtype allowlist must be imported from lcm_casting, not redefined."""
    tree = _source_tree()

    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "lcm_casting" in node.module:
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)

    assert POS_BEARING_CONST_NAME in imported_names, (
        "%s must import %s from lcm_casting (issue #232 P1 followup)"
        % (SOURCE_PATH.name, POS_BEARING_CONST_NAME)
    )


def test_get_part_of_speech_object_gates_on_the_imported_canonical_name():
    """GetPartOfSpeechObject's dispatch gate must reference the imported canonical name."""
    tree = _source_tree()
    func = _method_node(_class_node(tree))

    names_used = {node.id for node in ast.walk(func) if isinstance(node, ast.Name)}

    assert POS_BEARING_CONST_NAME in names_used, (
        "%s must gate on the imported %s, not a local re-definition "
        "(issue #232 P1 followup)" % (METHOD_NAME, POS_BEARING_CONST_NAME)
    )


def test_lcm_casting_dispatch_table_has_exactly_the_four_known_subtypes():
    """
    Coupling test: get_pos_from_msa()'s dispatch table in lcm_casting.py
    (_MSA_POS_PROPERTY, whose keys back the public POS_BEARING_MSA_CLASSES)
    must be exactly the four known POS-bearing MSA subtypes. Combined with
    the two tests above (LexSenseOperations imports POS_BEARING_MSA_CLASSES
    rather than defining its own copy), this fails if the two files ever
    diverge again.
    """
    tree = _lcm_casting_tree()
    assign = _module_level_assign(tree, MSA_POS_PROPERTY_CONST_NAME)

    value = assign.value
    assert isinstance(value, ast.Dict), "%s should be defined as a dict literal" % MSA_POS_PROPERTY_CONST_NAME

    keys = {key.value for key in value.keys if isinstance(key, ast.Constant)}
    assert keys == {"MoStemMsa", "MoInflAffMsa", "MoDerivAffMsa", "MoUnclassifiedAffixMsa"}


def test_stale_derivational_affix_caveat_removed_from_docstring():
    """The stale 'issue #87' None-for-MoDerivAffMsa docstring language must be gone."""
    tree = _source_tree()
    func = _method_node(_class_node(tree))
    docstring = ast.get_docstring(func) or ""

    assert "FromPartOfSpeechRA" not in docstring
    assert "issue #87" not in docstring


# ---------------------------------------------------------------------------
# Mock-based behavioral assertions
#
# The real LexSenseOperations module transitively imports SIL.LCModel via
# pythonnet, which requires a FieldWorks installation. To test behavior
# without one, we extract GetPartOfSpeechObject's own (unmodified) AST
# subtree and exec it into an isolated module namespace. This runs the real
# method body -- just without pulling in the real module's LCM imports --
# and lets us patch get_pos_from_msa() the same way we would on the real
# module. POS_BEARING_MSA_CLASSES is now imported from lcm_casting.py
# rather than assigned locally, so instead of lifting a module-level
# assignment out of LexSenseOperations.py's own AST (as before), we inject
# the same four known values directly into the synthetic module's
# namespace so the extracted method body's reference to the name resolves.
# ---------------------------------------------------------------------------


def _build_harness():
    tree = _source_tree()
    class_node = _class_node(tree)
    method_node = _method_node(class_node)

    # Strip decorators (@OperationsMethod is BaseOperations' dual class/
    # instance-level calling descriptor; irrelevant here since we call the
    # plain function directly against a mock `self`).
    method_copy = ast.FunctionDef(
        name=method_node.name,
        args=method_node.args,
        body=method_node.body,
        decorator_list=[],
        returns=None,
    )
    synthetic_class = ast.ClassDef(
        name=CLASS_NAME,
        bases=[],
        keywords=[],
        body=[method_copy],
        decorator_list=[],
    )
    synthetic_module = ast.Module(body=[synthetic_class], type_ignores=[])
    ast.fix_missing_locations(synthetic_module)

    code = compile(synthetic_module, filename=str(SOURCE_PATH), mode="exec")

    module = types.ModuleType("_lexsense_getpos_harness")
    exec(code, module.__dict__)

    # get_pos_from_msa / logger / POS_BEARING_MSA_CLASSES are referenced by
    # the method body but are not part of the extracted AST (they come from
    # the real module's imports); provide default mocks/values so the
    # harness is self-contained.
    module.get_pos_from_msa = Mock(name="get_pos_from_msa")
    module.logger = Mock(name="logger")
    module.POS_BEARING_MSA_CLASSES = frozenset(
        {"MoStemMsa", "MoInflAffMsa", "MoDerivAffMsa", "MoUnclassifiedAffixMsa"}
    )
    return module


@pytest.fixture
def harness():
    return _build_harness()


def _make_sense(msa, hvo=4242):
    sense = Mock(name="sense")
    sense.Hvo = hvo
    sense.MorphoSyntaxAnalysisRA = msa
    return sense


def _make_self(harness_module, sense):
    self_obj = Mock(name="self")
    self_obj._ValidateParam = Mock()
    # Mirrors Python's compile-time name mangling of self.__GetSenseObject
    # inside a class literally named "LexSenseOperations".
    self_obj._LexSenseOperations__GetSenseObject = Mock(return_value=sense)
    return self_obj


def _invoke(harness_module, self_obj, sense_or_hvo):
    method = getattr(harness_module, CLASS_NAME).__dict__[METHOD_NAME]
    return method(self_obj, sense_or_hvo)


def test_no_msa_returns_none_and_does_not_warn(harness):
    """(a) msa is None -> None, no log (R4a)."""
    sense = _make_sense(msa=None)
    self_obj = _make_self(harness, sense)

    with patch.object(harness, "get_pos_from_msa") as mock_get_pos:
        result = _invoke(harness, self_obj, sense)

    assert result is None
    mock_get_pos.assert_not_called()
    harness.logger.warning.assert_not_called()


def test_unrecognized_msa_class_returns_none_and_warns(harness):
    """(b) MSA exists but ClassName is not one of the four known types -> None + warning (R4b)."""
    msa = Mock(name="msa")
    msa.ClassName = "MoSomeUnknownMsa"
    sense = _make_sense(msa)
    self_obj = _make_self(harness, sense)

    with patch.object(harness, "get_pos_from_msa") as mock_get_pos:
        result = _invoke(harness, self_obj, sense)

    assert result is None
    mock_get_pos.assert_not_called()
    harness.logger.warning.assert_called_once()
    # The unrecognized ClassName should be identifiable in the warning call.
    warn_args = harness.logger.warning.call_args
    assert "MoSomeUnknownMsa" in warn_args.args or "MoSomeUnknownMsa" in str(warn_args)


@pytest.mark.parametrize(
    "class_name", ["MoStemMsa", "MoInflAffMsa", "MoDerivAffMsa", "MoUnclassifiedAffixMsa"]
)
def test_recognized_msa_class_delegates_to_get_pos_from_msa(harness, class_name):
    """A recognized MSA subtype delegates to get_pos_from_msa() and returns its result (R1/R2)."""
    msa = Mock(name="msa")
    msa.ClassName = class_name
    sense = _make_sense(msa)
    self_obj = _make_self(harness, sense)
    sentinel_pos = Mock(name="pos_object")

    with patch.object(harness, "get_pos_from_msa", return_value=sentinel_pos) as mock_get_pos:
        result = _invoke(harness, self_obj, sense)

    assert result is sentinel_pos
    mock_get_pos.assert_called_once_with(msa)
    harness.logger.warning.assert_not_called()
