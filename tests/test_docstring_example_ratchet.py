#
#   test_docstring_example_ratchet.py
#
#   Class: TestDocstringExamplesNameRealApi
#          TestCheckerHasTeeth
#          TestStaticAuthorityIsIntact
#
#          Ratchet guard: every `>>>` example in a public docstring must
#          name API that actually exists on this library. A docstring
#          example is a user-facing contract -- and it is the same text
#          FlexToolsMCP indexes and serves verbatim to an AI assistant, so
#          a stale name here is re-emitted into generated user scripts.
#
#          The failure mode is asymmetric. When a method is renamed, the
#          call sites break loudly and get fixed; the examples describing
#          them keep looking plausible forever. Nothing in the toolchain
#          reads them: they are text inside strings, invisible to the type
#          checker, and never executed (they need a live FLEx project).
#
#          This check is entirely STATIC -- AST over our own source, plus
#          the FLExProject.pyi stub for accessor types. No FieldWorks, no
#          pythonnet, no LCM. It runs anywhere pytest runs.
#
#   Scope: `flexicon/code/**/*.py`. The ratchet is a baseline of known
#          findings (tests/docstring_example_baseline.json): a NEW finding
#          fails, and a baseline entry that no longer reproduces also
#          fails, so the debt can only shrink. Every baseline entry is a
#          documented example that lies to a user -- keep the file
#          shrinking.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import json
import pathlib
import re
import textwrap

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CODE_ROOT = REPO_ROOT / "flexicon" / "code"
PYI_PATH = CODE_ROOT / "FLExProject.pyi"
INIT_PATH = REPO_ROOT / "flexicon" / "__init__.py"
BASELINE_PATH = pathlib.Path(__file__).resolve().parent / "docstring_example_baseline.json"

# Attributes of FLExProject that examples reach through but that are
# internal plumbing, not the public surface. An example built on these
# cannot be run by the reader who copies it.
INTERNAL_RECEIVERS = {"lp", "project", "lexDB", "cache"}

# Members every LCM-backed object carries; never a typo, and not ours to
# enumerate.
UNIVERSAL_MEMBERS = {"Guid", "Hvo", "ClassID", "ClassName"}

_SKIP_DIR_NAMES = {"__pycache__", "build", "dist", ".git"}

# Findings of these kinds are not merely stale text: the example cannot
# run at all. Listed separately in the failure message so they get fixed
# first when working the baseline down.
PRIORITY_KINDS = ("syntax", "refusing-method")


# ---------------------------------------------------------------------------
# Reading our own source
# ---------------------------------------------------------------------------

def _iter_source_files():
    for path in sorted(CODE_ROOT.rglob("*.py")):
        if any(part in _SKIP_DIR_NAMES for part in path.parts):
            continue
        yield path


def _param_arity(node):
    """(min, max) call arity for a def, excluding self/cls."""
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    if positional and positional[0].arg in ("self", "cls"):
        positional = positional[1:]
    total = len(positional) + len(args.kwonlyargs)
    defaulted = len(args.defaults) + sum(1 for d in args.kw_defaults or [] if d is not None)
    low = max(total - defaulted, 0)
    high = 99 if (args.vararg or args.kwarg) else total
    return (low, max(high, low))


def _body_always_raises_notimplemented(node):
    """True when the whole body is `raise NotImplementedError(...)`.

    A member that exists but always refuses is the one class of rot no
    existence check can see -- the name still resolves. flexicon can read
    the body, so it catches what a downstream consumer cannot.
    """
    body = [stmt for stmt in node.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str))]
    if len(body) != 1 or not isinstance(body[0], ast.Raise):
        return False
    exc = body[0].exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    return isinstance(exc, ast.Name) and exc.id == "NotImplementedError"


def build_class_index():
    """{class_name: {"members": {...}, "bases": [...], "file": path}}."""
    index = {}
    for path in _iter_source_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:  # pragma: no cover - our own source always parses
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            members = {}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    members[item.name] = {
                        "arity": _param_arity(item),
                        "refuses": _body_always_raises_notimplemented(item),
                        "is_property": any(
                            isinstance(d, ast.Name) and d.id == "property"
                            for d in item.decorator_list
                        ),
                    }
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            members.setdefault(target.id, {
                                "arity": (0, 99), "refuses": False, "is_property": False,
                            })
            bases = [ast.unparse(b).split(".")[-1] for b in node.bases]
            # A class defined twice (platform variants) merges rather than
            # shadows: a member on either definition is a real member.
            if node.name in index:
                index[node.name]["members"].update(members)
                index[node.name]["bases"] = list(
                    dict.fromkeys(index[node.name]["bases"] + bases)
                )
            else:
                index[node.name] = {"members": members, "bases": bases, "file": path}
    return index


def members_of(class_name, class_index, _seen=None):
    """Members of a class plus every base class's, transitively."""
    seen = _seen if _seen is not None else set()
    if class_name in seen or class_name not in class_index:
        return {}
    seen.add(class_name)
    out = {}
    for base in class_index[class_name]["bases"]:
        for name, info in members_of(base, class_index, seen).items():
            out.setdefault(name, info)
    for name, info in class_index[class_name]["members"].items():
        out[name] = info
    return out


def build_accessor_map():
    """({accessor: OperationsClass}, {every FLExProject member name}).

    Two authorities, deliberately split:

    - EXISTENCE comes from `FLExProject.py` itself. The stub types only 46
      accessors while the class exposes 177 members, so judging existence
      from the stub alone turned ~370 valid accessor references in our own
      docstrings into reported typos when this check was first run.
    - TYPING (which Operations class an accessor returns) comes from
      `FLExProject.pyi` first, since a stub annotation is unambiguous, and
      falls back to the docstring `Returns:` line for accessors the stub
      does not carry.
    """
    py_path = CODE_ROOT / "FLExProject.py"
    py_tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    pyi_tree = ast.parse(PYI_PATH.read_text(encoding="utf-8"), filename=str(PYI_PATH))

    def _class_defs(tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "FLExProject":
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        yield item

    accessors = {}
    for item in _class_defs(pyi_tree):
        if item.returns is None:
            continue
        returned = ast.unparse(item.returns).strip().strip("'\"").split(".")[-1]
        if returned.endswith("Operations"):
            accessors[item.name] = returned

    members = set()
    returns_re = re.compile(r"^\s*([A-Za-z_]\w*Operations)\s*:", re.M)
    for item in _class_defs(py_tree):
        members.add(item.name)
        if item.name in accessors:
            continue
        doc = ast.get_docstring(item) or ""
        if "Returns:" in doc:
            tail = doc.split("Returns:", 1)[1]
            match = returns_re.search(tail)
            if match:
                accessors[item.name] = match.group(1)
    members |= set(accessors)
    return accessors, members


def build_alias_map():
    """{alias: canonical} from `_op_aliases.OP_NAMESPACE_ALIASES`.

    These accessors are real -- installed onto FLExProject at import time --
    so an example using one is not a typo. It is still a defect of a milder
    kind: every alias emits a DeprecationWarning naming the canonical
    spelling (issue #200), and documentation that teaches the deprecated
    form is what keeps users guessing it.
    """
    path = CODE_ROOT / "_op_aliases.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "OP_NAMESPACE_ALIASES"
                   for t in node.targets):
            continue
        if isinstance(node.value, ast.Dict):
            return {
                k.value: v.value
                for k, v in zip(node.value.keys, node.value.values)
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
            }
    return {}


def build_flexicon_exports():
    """Names importable as `from flexicon import X`, read statically."""
    tree = ast.parse(INIT_PATH.read_text(encoding="utf-8"), filename=str(INIT_PATH))
    exports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                exports.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                exports.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.add(target.id)
                    if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        for element in node.value.elts:
                            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                exports.add(element.value)
    return exports


# ---------------------------------------------------------------------------
# Reading the examples
# ---------------------------------------------------------------------------

def _doctest_code(docstring):
    """The runnable half of a docstring: `>>>` / `...` lines, dedented."""
    lines = []
    for raw in textwrap.dedent(docstring).splitlines():
        stripped = raw.strip()
        if stripped.startswith(">>> "):
            lines.append(stripped[4:])
        elif stripped == ">>>":
            lines.append("")
        elif stripped.startswith("... "):
            lines.append(stripped[4:])
        # anything else is expected output, not code
    return "\n".join(lines)


def iter_examples():
    """(symbol, relative_path, def_lineno, example_code) per documented example."""
    for path in _iter_source_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:  # pragma: no cover
            continue
        stack: list = [(None, tree)]  # (enclosing class name, node)
        while stack:
            class_name, node = stack.pop()
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    stack.append((child.name, child))
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(child) or ""
                    if ">>>" in doc:
                        symbol = ("%s.%s" % (class_name, child.name)
                                  if class_name else child.name)
                        yield symbol, rel, child.lineno, _doctest_code(doc)
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                if ">>>" in doc:
                    yield node.name, rel, node.lineno, _doctest_code(doc)


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------

def _elided(call):
    return any(isinstance(a, ast.Constant) and a.value is Ellipsis for a in call.args)


def check_example(symbol, rel_path, lineno, code, ctx):
    """Findings for one example block."""
    accessors, project_methods, class_index, exports, aliases = ctx
    findings = []

    def add(kind, detail):
        findings.append({
            "kind": kind, "symbol": symbol, "file": rel_path,
            "def_line": lineno, "detail": detail,
        })

    if not code.strip():
        return findings
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        add("syntax", "example does not parse: %s" % exc.msg)
        return findings

    # Locally constructed Operations instances: `ops = LexEntryOperations(project)`
    local_ops = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            name = func.id if isinstance(func, ast.Name) else None
            if name and name.endswith("Operations") and name in class_index:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local_ops[target.id] = name

    calls = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            calls[node.func] = (len(node.args) + len(node.keywords), _elided(node))

    def check_member(owner_class, member, node, shown_as):
        members = members_of(owner_class, class_index)
        if not members or member in UNIVERSAL_MEMBERS:
            return
        if member not in members:
            add("unknown-method", "%s does not exist on %s" % (shown_as, owner_class))
            return
        info = members[member]
        if info["refuses"]:
            add("refusing-method", "%s always raises NotImplementedError" % shown_as)
            return
        if node in calls and not info["is_property"]:
            nargs, elided = calls[node]
            low, high = info["arity"]
            if not elided and (nargs < low or nargs > high):
                add("arity", "%s called with %d arg(s); def takes %d..%d"
                    % (shown_as, nargs, low, high))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "") == "flexicon":
            for alias in node.names:
                if alias.name != "*" and alias.name not in exports:
                    add("bad-import", "from flexicon import %s -- not exported"
                        % alias.name)
            continue
        if not isinstance(node, ast.Attribute):
            continue

        # ops.Method(...) where ops = SomeOperations(project)
        if isinstance(node.value, ast.Name) and node.value.id in local_ops:
            owner = local_ops[node.value.id]
            check_member(owner, node.attr, node, "%s.%s" % (node.value.id, node.attr))
            continue

        if isinstance(node.value, ast.Name) and node.value.id == "project":
            attr = node.attr
            if attr in INTERNAL_RECEIVERS:
                add("internal-leak",
                    "project.%s is internal plumbing; the example cannot be run "
                    "from a user's FLExProject" % attr)
            elif attr in aliases:
                add("deprecated-alias",
                    "project.%s is a deprecated alias for project.%s and warns "
                    "on use" % (attr, aliases[attr]))
            elif attr not in accessors and attr not in project_methods:
                add("unknown-accessor", "project.%s is not on FLExProject" % attr)
            continue

        if (isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "project"):
            accessor_name = aliases.get(node.value.attr, node.value.attr)
            owner = accessors.get(accessor_name)
            if owner:
                check_member(owner, node.attr, node,
                             "project.%s.%s" % (node.value.attr, node.attr))
    return findings


def collect_findings():
    accessors, project_methods = build_accessor_map()
    class_index = build_class_index()
    exports = build_flexicon_exports()
    aliases = build_alias_map()
    ctx = (accessors, project_methods, class_index, exports, aliases)
    findings = []
    for symbol, rel, lineno, code in iter_examples():
        findings.extend(check_example(symbol, rel, lineno, code, ctx))
    return findings


def finding_key(finding):
    """Stable identity: kind + symbol + detail. Line numbers deliberately
    excluded so unrelated edits above a docstring do not churn the baseline."""
    return "%s|%s|%s" % (finding["kind"], finding["symbol"], finding["detail"])


def load_baseline():
    if not BASELINE_PATH.exists():
        return {}
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDocstringExamplesNameRealApi:
    """
    A `>>>` example is a promise that this code runs. Verify the names in
    it against our own source, and ratchet the known-bad set downward.
    """

    @pytest.fixture(scope="class")
    def findings(self):
        return collect_findings()

    def test_no_new_broken_examples(self, findings):
        baseline = set(load_baseline().get("known_findings", []))
        current = {finding_key(f): f for f in findings}
        new = [current[key] for key in sorted(set(current) - baseline)]
        assert not new, (
            "Docstring examples name API that does not exist.\n"
            "Fix the example (preferred), or -- only if this is pre-existing "
            "debt being recorded -- add the key to\n"
            "  %s\n\n" % BASELINE_PATH.relative_to(REPO_ROOT).as_posix()
            + "\n".join(
                "  [%s] %s (%s:%s)\n      %s"
                % (f["kind"], f["symbol"], f["file"], f["def_line"], f["detail"])
                for f in new
            )
        )

    def test_baseline_has_no_stale_entries(self, findings):
        """A fixed example must leave the baseline, or the ratchet loosens.

        Without this the baseline only ever grows: entries whose examples
        were repaired keep sitting there, silently re-permitting the same
        defect if it comes back.
        """
        baseline = set(load_baseline().get("known_findings", []))
        current = {finding_key(f) for f in findings}
        stale = sorted(baseline - current)
        assert not stale, (
            "These baseline entries no longer reproduce -- remove them from "
            "%s so the ratchet stays tight:\n  "
            % BASELINE_PATH.relative_to(REPO_ROOT).as_posix() + "\n  ".join(stale)
        )

    def test_examples_are_actually_being_read(self):
        """Guards the extractor: an empty corpus reports zero findings,
        which reads exactly like a clean one."""
        examples = list(iter_examples())
        assert len(examples) > 100, (
            "only %d docstring examples found -- the extractor is probably "
            "broken, not the corpus clean" % len(examples)
        )

    def test_priority_debt_is_visible(self, findings):
        """Not a gate -- a standing report of the entries to fix first.

        `syntax` and `refusing-method` examples cannot run at all, as
        opposed to naming something that merely moved.
        """
        priority = [f for f in findings if f["kind"] in PRIORITY_KINDS]
        baseline = set(load_baseline().get("known_findings", []))
        unrecorded = [f for f in priority if finding_key(f) not in baseline]
        assert not unrecorded, (
            "New example(s) that cannot run at all:\n" + "\n".join(
                "  [%s] %s (%s:%s) %s"
                % (f["kind"], f["symbol"], f["file"], f["def_line"], f["detail"])
                for f in unrecorded
            )
        )


class TestCheckerHasTeeth:
    """
    A gate that silently stops detecting is worse than none, because the
    green run is read as evidence. Each planted defect below is one this
    check found for real in flexicon's own docstrings.
    """

    @pytest.fixture(scope="class")
    def ctx(self):
        accessors, project_methods = build_accessor_map()
        return (accessors, project_methods, build_class_index(),
                build_flexicon_exports(), build_alias_map())

    def _kinds(self, code, ctx):
        return {f["kind"] for f in check_example("T", "t.py", 1, code, ctx)}

    def test_catches_unknown_accessor(self, ctx):
        assert "unknown-accessor" in self._kinds(
            "project.LexiconGetAllEntries()\n", ctx)

    def test_catches_unknown_method(self, ctx):
        assert "unknown-method" in self._kinds(
            "project.Agents.CreateHumanAgent('parser')\n", ctx)

    def test_catches_internal_receiver(self, ctx):
        assert "internal-leak" in self._kinds("x = project.lp.LexDbOA\n", ctx)

    def test_catches_wrong_arity(self, ctx):
        assert "arity" in self._kinds("project.Filters.Create('name')\n", ctx)

    def test_catches_unparseable_example(self, ctx):
        assert "syntax" in self._kinds("if x\n    pass\n", ctx)

    def test_catches_deprecated_alias(self, ctx):
        """Our own docs teach the singular form 204 times; that is what
        keeps users guessing it (issue #200)."""
        assert "deprecated-alias" in self._kinds("project.Sense.GetGloss(s)\n", ctx)

    def test_alias_receiver_still_resolves_its_members(self, ctx):
        """An alias is a real accessor, so member checking must continue
        through it rather than silently stopping."""
        assert "unknown-method" in self._kinds("project.Sense.GetGlosss(s)\n", ctx)

    def test_catches_import_of_unexported_name(self, ctx):
        assert "bad-import" in self._kinds(
            "from flexicon import ReversalOperations\n", ctx)

    def test_catches_local_operations_instance_typo(self, ctx):
        code = ("ops = LexEntryOperations(project)\n"
                "ops.GetHeadwordd(entry)\n")
        assert "unknown-method" in self._kinds(code, ctx)

    def test_accepts_correct_usage(self, ctx):
        code = ("from flexicon import LexEntryOperations\n"
                "for entry in project.LexEntry.GetAll():\n"
                "    print(project.LexEntry.GetLexemeForm(entry))\n")
        assert not self._kinds(code, ctx)

    def test_inherited_members_resolve(self, ctx):
        """Move*/Sort come from BaseOperations; without transitive base
        resolution these are dozens of phantom failures."""
        assert not self._kinds("project.Senses.MoveUp(entry, sense)\n", ctx)

    def test_elided_calls_do_not_trip_arity(self, ctx):
        assert not self._kinds("project.Senses.Create(...)\n", ctx)


class TestStaticAuthorityIsIntact:
    """
    The checks are only as good as the maps they read. If the stub stops
    typing accessors, or the class walk finds nothing, every example
    silently passes.
    """

    def test_accessor_map_is_populated(self):
        accessors, _ = build_accessor_map()
        assert len(accessors) > 30, (
            "FLExProject.pyi typed only %d accessors -- the stub or this "
            "reader is broken" % len(accessors)
        )
        assert accessors.get("LexEntry") == "LexEntryOperations"

    def test_class_index_resolves_inheritance(self):
        index = build_class_index()
        assert "BaseOperations" in index
        members = members_of("LexSenseOperations", index)
        assert "MoveUp" in members, "base-class members did not resolve"

    def test_refusing_members_are_detected(self):
        """PhonologicalRuleOperations.SetLeftContext refuses since #142."""
        index = build_class_index()
        members = members_of("PhonologicalRuleOperations", index)
        assert members.get("SetLeftContext", {}).get("refuses") is True


# ---------------------------------------------------------------------------
# Report / baseline maintenance
#
#   python tests/test_docstring_example_ratchet.py             # report
#   python tests/test_docstring_example_ratchet.py --baseline  # record debt
#
# ASCII only: this runs on Windows consoles.
# ---------------------------------------------------------------------------

def _report(findings):
    from collections import Counter, defaultdict
    counts = Counter(f["kind"] for f in findings)
    print("=" * 72)
    print("Docstring example check -- %d example block(s) read"
          % len(list(iter_examples())))
    for kind in sorted(counts):
        print("  %-18s %d" % (kind, counts[kind]))
    print("  %-18s %d" % ("TOTAL", len(findings)))
    print("")
    by_file = defaultdict(list)
    for finding in findings:
        by_file[finding["file"]].append(finding)
    for path in sorted(by_file):
        print("-- %s" % path)
        for finding in sorted(by_file[path], key=lambda f: (f["def_line"], f["kind"])):
            print("   [%s] %s (L%s): %s"
                  % (finding["kind"], finding["symbol"], finding["def_line"],
                     finding["detail"]))
        print("")


def _write_baseline(findings):
    from collections import Counter
    payload = {
        "_comment": [
            "Known-bad docstring examples, recorded so the ratchet can go",
            "green on pre-existing debt while blocking anything new.",
            "Every entry is an example that lies to a user. Removing entries",
            "is the point: fix the example, then regenerate with",
            "python tests/test_docstring_example_ratchet.py --baseline",
        ],
        "counts": dict(Counter(f["kind"] for f in findings)),
        "known_findings": sorted(finding_key(f) for f in findings),
    }
    BASELINE_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print("[OK] wrote %d entries to %s"
          % (len(payload["known_findings"]), BASELINE_PATH.name))


if __name__ == "__main__":
    import sys as _sys

    _findings = collect_findings()
    if "--baseline" in _sys.argv:
        _write_baseline(_findings)
    else:
        _report(_findings)
