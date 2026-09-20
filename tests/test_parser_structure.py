#
#   test_parser_structure.py
#
#   Tier A1, structural half -- CP2a T006. The two STANDING ratchets over
#   the shipped parser surface:
#
#     A1.2 (FR-006, SC-002)  No code path compares a detected parser version
#                            against a minimum. Zero occurrences.
#     A1.3 (FR-003)          No module-scope parser import exists anywhere.
#                            Loading is triggered by USE only.
#
#   These are controls, not conventions an implementer has to remember
#   (Constitution Principle III). Both failure modes are silent: a version
#   floor looks reasonable in review and only bites on the machine with the
#   "wrong" FieldWorks; a module-scope parser import makes `import flexicon`
#   require a parser component that FR-003 promises it does not.
#
#   Template: tests/test_public_casting_export.py:127-153 (ast.parse over
#   inspect.getsource, module-scope Import/ImportFrom scan).
#
#   WHY EACH DETECTOR HAS A SELF-TEST. A structural ratchet that scans for
#   something absent passes trivially when it scans nothing -- and CP2a
#   writes these BEFORE the code they police exists. The self-tests plant a
#   known violation in a synthetic module and assert the detector catches
#   it, so "green" means "the detector works and found nothing", never
#   "the detector found nothing to look at".
#
#   Platform: Python (standard library only -- no FieldWorks needed; these
#             scan source text, they do not import the parser).
#
#   Copyright 2026
#

import ast
import os

import pytest


PARSER_CLR_NAMESPACE = "SIL.FieldWorks.WordWorks.Parser"
PARSER_ASSEMBLY = "ParserCore"

# The facade CP2a builds. Absent until T010/T011 land; the tests that police
# it specifically say so rather than passing silently.
FACADE_RELPATH = os.path.join("flexicon", "code", "Parser", "ParserOperations.py")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _package_sources():
    """Every .py file shipped under flexicon/ -- the scan surface."""
    root = os.path.join(_repo_root(), "flexicon")
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if name.endswith(".py"):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


# ---------------------------------------------------------------------------
# A1.3 -- module-scope parser imports
# ---------------------------------------------------------------------------


def _module_scope_parser_imports(source, filename="<src>"):
    """Names of parser imports that sit at MODULE scope in `source`.

    Function-local imports are invisible to this walk by construction: it
    reads `tree.body` only, never descends into a FunctionDef. That is the
    whole point -- a function-local import is the compliant shape.

    Also catches `clr.AddReference("ParserCore")` at module scope, which
    loads the assembly just as effectively as an import statement does.
    """
    tree = ast.parse(source, filename=filename)
    offenders = []

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(PARSER_CLR_NAMESPACE):
                offenders.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PARSER_CLR_NAMESPACE):
                    offenders.append(alias.name)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "AddReference"
                and isinstance(func.value, ast.Name)
                and func.value.id == "clr"
            ):
                for arg in call.args:
                    if isinstance(arg, ast.Constant) and arg.value == PARSER_ASSEMBLY:
                        offenders.append('clr.AddReference("%s")' % PARSER_ASSEMBLY)

    return offenders


def _function_local_parser_imports(source, filename="<src>"):
    """Parser imports that sit INSIDE a function -- the compliant shape."""
    tree = ast.parse(source, filename=filename)
    module_scope = set(id(n) for n in tree.body)
    found = []
    for node in ast.walk(tree):
        if id(node) in module_scope:
            continue
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(PARSER_CLR_NAMESPACE):
                found.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PARSER_CLR_NAMESPACE):
                    found.append(alias.name)
    return found


class TestA13NoModuleScopeParserImport:
    """A1.3 (FR-003) -- loading is triggered by use only."""

    def test_detector_catches_a_planted_violation(self):
        """Self-test: the scan is not vacuous."""
        planted = "import os\n" "from %s import HCParser\n" "def f():\n" "    return HCParser\n" % PARSER_CLR_NAMESPACE
        assert _module_scope_parser_imports(planted) == [PARSER_CLR_NAMESPACE]

    def test_detector_accepts_the_compliant_shape(self):
        """Self-test: a function-local import is NOT reported."""
        compliant = "def f():\n" "    from %s import HCParser\n" "    return HCParser\n" % PARSER_CLR_NAMESPACE
        assert _module_scope_parser_imports(compliant) == []
        assert _function_local_parser_imports(compliant) == [PARSER_CLR_NAMESPACE]

    def test_detector_catches_module_scope_add_reference(self):
        """Self-test: `clr.AddReference("ParserCore")` counts as loading."""
        planted = 'import clr\nclr.AddReference("%s")\n' % PARSER_ASSEMBLY
        assert _module_scope_parser_imports(planted) == ['clr.AddReference("%s")' % PARSER_ASSEMBLY]

    def test_no_module_scope_parser_import_anywhere_in_the_package(self):
        """The ratchet. Zero occurrences across every shipped module."""
        sources = _package_sources()
        assert sources, "scanned nothing -- the package layout moved"

        offenders = {}
        for path in sources:
            with open(path, encoding="utf-8") as handle:
                found = _module_scope_parser_imports(handle.read(), filename=path)
            if found:
                offenders[os.path.relpath(path, _repo_root())] = found

        assert not offenders, (
            "module-scope parser imports found -- `import flexicon` would now "
            "require the parser component, which FR-003 promises it does not: %r" % offenders
        )


class TestA13FacadeLoadsByUse:
    """The positive half of A1.3, once the facade exists."""

    def test_facade_parser_imports_are_function_local(self):
        path = os.path.join(_repo_root(), FACADE_RELPATH)
        if not os.path.exists(path):
            pytest.skip(
                "%s does not exist yet (lands at T010/T011); the negative "
                "ratchet above already covers the whole package" % FACADE_RELPATH
            )
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert _module_scope_parser_imports(source, filename=path) == []
        assert _function_local_parser_imports(source, filename=path), (
            "%s imports the parser nowhere at all -- either it does not bind "
            "the component, or it reaches it by a route this ratchet cannot "
            "see." % FACADE_RELPATH
        )


# ---------------------------------------------------------------------------
# A1.2 -- version comparison
# ---------------------------------------------------------------------------

_ORDERING_OPS = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def _names_in(node):
    """Every identifier mentioned in an expression, lowercased."""
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            out.append(sub.id.lower())
        elif isinstance(sub, ast.Attribute):
            out.append(sub.attr.lower())
    return out


def _version_comparisons(source, filename="<src>"):
    """Ordering comparisons whose operands mention a version.

    An ordering comparison (`<`, `<=`, `>`, `>=`) against something called
    a version IS a floor, whatever it is spelled. Equality is not flagged:
    `== "9.3.10"` in a test assertion or a dispatch table is not a minimum.
    """
    tree = ast.parse(source, filename=filename)
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, _ORDERING_OPS) for op in node.ops):
            continue
        mentioned = _names_in(node.left)
        for comparator in node.comparators:
            mentioned.extend(_names_in(comparator))
        if any("version" in name for name in mentioned):
            offenders.append("%s:%d" % (filename, node.lineno))
    return offenders


class TestA12NoParserVersionFloor:
    """A1.2 (FR-006, SC-002) -- the version is read and never compared."""

    def test_detector_catches_a_planted_floor(self):
        """Self-test: the scan is not vacuous."""
        planted = (
            "def f(detected_version):\n"
            "    if detected_version >= (9, 3):\n"
            "        return True\n"
            "    return False\n"
        )
        assert len(_version_comparisons(planted, filename="planted.py")) == 1

    def test_detector_catches_a_floor_through_an_attribute(self):
        """Self-test: `probe.parser_version < MIN` is the same offence."""
        planted = "def f(probe, MIN):\n    return probe.parser_version < MIN\n"
        assert len(_version_comparisons(planted, filename="planted.py")) == 1

    def test_detector_does_not_flag_equality(self):
        """Self-test: `==` is not a floor, and must not be reported."""
        planted = 'def f(detected_version):\n    return detected_version == "9.3.10"\n'
        assert _version_comparisons(planted, filename="planted.py") == []

    def test_no_parser_version_comparison_in_the_parser_package(self):
        """The ratchet, scoped to the parser surface CP2a owns.

        Scoped rather than package-wide on purpose: flexicon compares its
        OWN version elsewhere for legitimate reasons, and FR-006 is about
        the DETECTED PARSER version. Widening this to the whole package
        would make it noisy and it would be relaxed away.
        """
        parser_dir = os.path.join(_repo_root(), "flexicon", "code", "Parser")
        assert os.path.isdir(parser_dir), (
            "flexicon/code/Parser/ is absent -- T002 created it; if it moved, "
            "this ratchet is now scanning nothing and must be repointed."
        )

        offenders = []
        for dirpath, dirnames, filenames in os.walk(parser_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in sorted(filenames):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as handle:
                    offenders.extend(_version_comparisons(handle.read(), filename=os.path.relpath(path, _repo_root())))

        assert offenders == [], (
            "a detected parser version is compared against a floor at %r. "
            "FR-006: the version is READ and REPORTED, never used to gate. "
            "The gate is the two checks in ParserAvailability -- same install, "
            "and the bound surface exists." % offenders
        )
