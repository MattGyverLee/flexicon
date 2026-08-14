#
#   scan_unbracketed_mutations.py
#
#   Static AST-based scanner that finds every class method under
#   flexicon/code/ containing an LCM mutation node NOT lexically enclosed by
#   a ``with self._TransactionCM(...)`` block.
#
#   This is the mechanical half of decision D5 / task B2g
#   (specs/write-path-transactions/tasks.md): 294 sites were catalogued by
#   hand in specs/write-path-transactions/reviews/cycle1-explore-b2sweep.md
#   ("B2s"). B2 (specs/write-path-transactions/tasks.md) brackets them in
#   with self._TransactionCM(...) blocks, batched by domain over several
#   spurts, and B2g (this module + the paired baseline/test) is the ratchet
#   that keeps that sweep honest: it must reproduce the cycle-1 total, its
#   frozen baseline shrinks only when a batch actually lands, and it fails
#   on any new (295th, 296th, ...) unbracketed site.
#
#   Runs anywhere -- pure ``ast`` module, no FieldWorks/pythonnet required.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

"""
Scan flexicon/code for LCM mutator calls/assignments not wrapped in
``with self._TransactionCM(...)``.

Method (mirrors cycle1-explore-b2sweep.md verbatim):

  Walk every ``.py`` file under ``flexicon/code``. For each method of every
  class, record any mutation node not lexically enclosed by a
  ``with self._TransactionCM(...)`` block. Mutation indicators:

    - ``factory.Create`` -- any ``.Create(...)`` call (kind label
      "factory.Create" regardless of the actual receiver name; the cycle-1
      inventory uses this label even for ``self.Create(...)`` recursive
      calls, e.g. ``Shared/FilterOperations.py:833 ImportFilter``). Also
      matches ``<var-with-"factory"-in-its-name>.Create<Suffix>(...)`` --
      the one outlier being ``Scripture/ScrSectionOperations.py:129``'s
      ``factory.CreateScrSection(...)``, still labelled "factory.Create"
      in the cycle-1 table.
    - ``.Delete``, ``.Remove``, ``.Add``, ``.MoveTo``, ``.Replace``,
      ``.Clear``, ``.Insert`` -- method calls with these exact (PascalCase)
      names.
    - ``set_String`` / ``SetString`` -- method calls with these exact names.
    - ``MergeObject`` -- method calls with this exact name (present in the
      cycle-1 table for ``LexEntryOperations.__DeduplicateSensesInEntry``
      and ``CatalogBackedMixin.FixGuidsAgainstCatalog``, though not spelled
      out in the B2g task prompt's indicator list).
    - Property assignment to an attribute whose name ends in one of the
      LCM ownership-encoding suffixes ``RA``, ``OA``, ``OS``, ``RS``
      (Reference Atomic / Owning Atomic / Owning Sequence / Reference
      Sequence).

  Exclusions (from cycle-1's "Ambiguous cases" + general design):

    - Pure delegation to a sibling Operations class's public method, of the
      exact call shape ``self.<CapitalizedAttr>.<Method>(...)`` where
      ``<CapitalizedAttr>`` is not ``project`` (the raw FLExProject/LCM
      facade). E.g. ``self.LexEntry.Create(...)``, ``self.Senses.Delete(...)``
      in FLExProject.py's ``Lexicon*`` convenience wrappers. This is a
      call-site-level exclusion, not a whole-method exclusion: a method that
      *also* contains a genuine, non-delegated mutation (e.g.
      ``LexiconDeleteObject``'s ``collection.Remove(obj)`` / ``obj.Delete()``
      fallback branch) is still flagged, just not on account of its
      delegated branches.
      NOTE: this does *not* cover delegation through a local alias, e.g.
      ``sense_ops = self.project.Senses; sense_ops.MergeObject(...)`` in
      ``LexEntryOperations.__DeduplicateSensesInEntry`` -- that call's
      receiver is a bare ``Name``, not ``self.<Cap>``, so it is (correctly,
      per the cycle-1 table) still counted.
    - ``TsStrBldr`` builder calls: ``.Clear()`` / ``.Replace(...)`` where the
      receiver is a local variable whose name contains "bldr"
      (case-insensitive), e.g. ``bldr.Clear()``, ``bldr.Replace(...)``.
    - ``SandboxGenericMSA`` field assignments are excluded *implicitly*: its
      fields (``MsaType``, ``MainPOS``, ``SecondaryPOS``, ...) do not end in
      RA/OA/OS/RS, so the suffix-based property-assignment rule never
      matches them. No special-case code is needed or present.

Usage::

    from tests.write_path_transactions.scan_unbracketed_mutations import scan

    findings = scan()  # list of Finding, one per unbracketed method
"""

import ast
import os
from dataclasses import dataclass, asdict
from pathlib import Path

# --- Configuration -----------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_ROOT = REPO_ROOT / "flexicon" / "code"

# Exact (case-sensitive) method-call attribute names that indicate a
# mutation, EXCLUDING "Create" -- that one is handled separately by
# _is_create_call()/_MethodScanner.scan() because one call site
# (Scripture/ScrSectionOperations.py:129) uses a factory method named
# ``CreateScrSection`` rather than plain ``Create``, and the cycle-1 table
# still labels it "factory.Create".
MUTATION_CALL_ATTRS = {
    "Delete",
    "Remove",
    "RemoveAt",  # PhonologicalRuleOperations.__ClearSequence: seq.RemoveAt(...)
    "Add",
    "MoveTo",
    "Replace",
    "Clear",
    "Insert",
    "SetString",
    "set_String",
    "MergeObject",
}

# LCM ownership-encoding suffixes for owning/reference atomic/sequence props.
PROPERTY_SUFFIXES = ("RA", "OA", "OS", "RS")

# The one bracketing construct recognized as satisfying D5/B1.
TRANSACTION_CM_ATTR = "_TransactionCM"

# Constructors of non-LCM value objects. Fields assigned on a local variable
# bound to one of these are excluded from the property-assignment rule even
# when the field name happens to end in a PROPERTY_SUFFIXES letter pair by
# coincidence (SandboxGenericMSA.MainPOS / .SecondaryPOS end in "OS", but
# are plain Python attributes on a value object, not LCM OwningSequence
# properties). See MSAOperations.py CreateStem/CreateInflAff/
# CreateUnclassifiedAffix in the cycle-1 "Ambiguous cases" section.
NON_LCM_VALUE_CONSTRUCTORS = {"SandboxGenericMSA"}


@dataclass(frozen=True)
class Finding:
    """One unbracketed method: identity + why it was flagged."""

    file: str  # path relative to flexicon/code, forward slashes
    line: int  # def line of the method
    class_name: str
    method_name: str
    kinds: tuple  # sorted tuple of distinct mutation-kind labels

    @property
    def qualified_method(self):
        return f"{self.class_name}.{self.method_name}"

    @property
    def key(self):
        """Stable identity for baseline comparison (no line number --
        lines drift as unrelated code above a method is edited; the
        ratchet must not spuriously fire on line-number churn)."""
        return (self.file, self.class_name, self.method_name)

    def to_dict(self):
        d = asdict(self)
        d["kinds"] = list(self.kinds)
        return d


def _relative_path(filepath):
    return str(Path(filepath).resolve().relative_to(CODE_ROOT)).replace(os.sep, "/")


def _iter_source_files():
    """Yield every real (non-backup, non-cache) .py file under flexicon/code."""
    for root, dirs, files in os.walk(CODE_ROOT):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            if fname.endswith(".backup"):
                continue
            yield Path(root) / fname


def _is_transactioncm_with(with_node):
    """True if a With node's context managers include self._TransactionCM(...)."""
    for item in with_node.items:
        expr = item.context_expr
        if (
            isinstance(expr, ast.Call)
            and isinstance(expr.func, ast.Attribute)
            and expr.func.attr == TRANSACTION_CM_ATTR
            and isinstance(expr.func.value, ast.Name)
            and expr.func.value.id == "self"
        ):
            return True
    return False


def _is_tsstrbldr_builder_call(call_node):
    """Exclude bldr.Clear()/bldr.Replace(...) on a local TsStrBldr-ish var."""
    if call_node.func.attr not in ("Clear", "Replace"):
        return False
    base = call_node.func.value
    return isinstance(base, ast.Name) and "bldr" in base.id.lower()


def _is_sibling_ops_delegation(call_node):
    """
    Exclude self.<CapitalizedAttr>.<Method>(...) -- a call into another
    Operations class's own public method (e.g. self.LexEntry.Create(...)
    inside FLExProject.py's Lexicon* convenience wrappers). That sibling
    method is separately tracked (and separately bracketed) under its own
    class/method identity; the call site here is not itself a raw LCM
    mutation.

    Deliberately narrow: only a *direct* self.<Cap>.<method>() shape.
    self.project.DomainDataByFlid.SetString(...) (3 hops, and "project"
    lower-case) does not match, nor does a call through a local alias like
    ``sense_ops = self.project.Senses; sense_ops.MergeObject(...)``.
    """
    base = call_node.func.value
    return (
        isinstance(base, ast.Attribute)
        and isinstance(base.value, ast.Name)
        and base.value.id == "self"
        and bool(base.attr)
        and base.attr[0].isupper()
        and base.attr != "project"
    )


def _kind_label(attr):
    if attr in ("SetString", "set_String", "MergeObject"):
        return attr
    if attr == "RemoveAt":
        return ".Remove"
    return f".{attr}"


def _is_create_call(call_node):
    """
    True for ``.Create(...)`` (any receiver -- including same-class
    recursion like ``self.Create(...)``, see Shared/FilterOperations.py's
    ``ImportFilter``) and for ``<factory-ish-var>.Create<Suffix>(...)``
    (the one ``factory.CreateScrSection(...)`` outlier).
    """
    attr = call_node.func.attr
    if attr == "Create":
        return True
    if not attr.startswith("Create"):
        return False
    base = call_node.func.value
    return isinstance(base, ast.Name) and "factory" in base.id.lower()


def _is_sandbox_value_construction(node):
    """True for ``var = SandboxGenericMSA(...)`` (or similar non-LCM value
    object constructors) -- used to seed the per-method sandbox-var tracking
    set so later ``var.Field = ...`` assignments on it are recognized as
    plain value-object field sets, not LCM property writes."""
    if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
        return None
    value = node.value
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
    if name in NON_LCM_VALUE_CONSTRUCTORS:
        return node.targets[0].id
    return None


class _MethodScanner:
    """Walks a single method body, tracking with-self._TransactionCM(...)
    protection, and collects distinct mutation-kind labels found outside
    any such block."""

    def __init__(self):
        self.kinds = set()
        # Local variable names bound to a non-LCM value-object constructor
        # (e.g. ``sandbox = SandboxGenericMSA()``). Forward-tracked in
        # source order since the binding assignment always precedes the
        # field assignments in every observed case.
        self.non_lcm_vars = set()

    def scan(self, node, protected):
        if isinstance(node, ast.With):
            this_protected = protected or _is_transactioncm_with(node)
            for child in ast.iter_child_nodes(node):
                self.scan(child, this_protected)
            return

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            is_mutator = attr in MUTATION_CALL_ATTRS or _is_create_call(node)
            if is_mutator and not protected:
                if _is_tsstrbldr_builder_call(node):
                    pass
                elif _is_sibling_ops_delegation(node):
                    pass
                else:
                    label = "factory.Create" if _is_create_call(node) else _kind_label(attr)
                    self.kinds.add(label)

        elif isinstance(node, (ast.Assign, ast.AugAssign)):
            sandbox_var = _is_sandbox_value_construction(node)
            if sandbox_var:
                self.non_lcm_vars.add(sandbox_var)

            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not protected:
                for target in targets:
                    if not (isinstance(target, ast.Attribute) and target.attr.endswith(PROPERTY_SUFFIXES)):
                        continue
                    base = target.value
                    if isinstance(base, ast.Name) and base.id in self.non_lcm_vars:
                        continue
                    self.kinds.add(f"prop assign ({target.attr})")

        for child in ast.iter_child_nodes(node):
            self.scan(child, protected)


def _scan_method(func_node):
    scanner = _MethodScanner()
    for stmt in func_node.body:
        scanner.scan(stmt, protected=False)
    return scanner.kinds


def _scan_file(filepath):
    """Yield Finding for every unbracketed class method in one file."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return

    relpath = _relative_path(filepath)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        class_name = node.name
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            kinds = _scan_method(item)
            if kinds:
                yield Finding(
                    file=relpath,
                    line=item.lineno,
                    class_name=class_name,
                    method_name=item.name,
                    kinds=tuple(sorted(kinds)),
                )


def scan():
    """Scan the whole flexicon/code tree. Returns a list of Finding, sorted
    by (file, line) for stable, readable output."""
    findings = []
    for filepath in _iter_source_files():
        findings.extend(_scan_file(filepath))
    findings.sort(key=lambda f: (f.file, f.line))
    return findings


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Scan flexicon/code for unbracketed LCM mutations (B2g ratchet guard)."
    )
    parser.add_argument("--json", action="store_true", help="Print full findings as JSON.")
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Write findings as the frozen baseline JSON to this path.",
    )
    args = parser.parse_args()

    findings = scan()

    if args.baseline:
        write_baseline(findings, args.baseline)
        print(f"[DONE] Baseline written to {args.baseline} ({len(findings)} entries).")
        return

    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        print(f"Total unbracketed methods: {len(findings)}\n")
        for f in findings:
            print(f"  {f.file}:{f.line} {f.qualified_method} [{', '.join(f.kinds)}]")


def write_baseline(findings, path):
    import json

    payload = {
        "total": len(findings),
        "entries": [f.to_dict() for f in findings],
    }
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
