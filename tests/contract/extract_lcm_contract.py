#
#   extract_lcm_contract.py
#
#   Static AST-based extractor that discovers every LCM type, method,
#   and property that flexlibs2 depends on. Produces the "expected
#   contract" -- what flexlibs2 *needs* from liblcm.
#
#   Runs anywhere (no FieldWorks/pythonnet required).
#
#   Platform: Python 3.8+
#   Copyright 2025
#

"""
Extract the LCM API contract that flexlibs2 depends on.

This module walks the flexlibs2 source tree, parses each Python file's AST,
and extracts:

  1. **Imports**: Every ``from SIL.LCModel... import X`` statement
  2. **Attribute access**: Every ``obj.SomeLCMProperty`` or ``obj.SomeLCMMethod(...)``
     called on objects known to originate from LCM imports
  3. **Factory/Repository usage**: Which factories and repositories are used

The output is a JSON-serialisable dict suitable for snapshotting and diffing.

Usage::

    from tests.contract.extract_lcm_contract import extract_contract

    contract = extract_contract()
    # contract = {
    #   "imports": { "SIL.LCModel": ["ILexEntry", "ILexSense", ...], ... },
    #   "type_usage": { "ILexEntry": {"properties": [...], "methods": [...]}, ... },
    #   "factories": ["ILexEntryFactory", ...],
    #   "repositories": ["ILexEntryRepository", ...],
    #   "files": { "Grammar/POSOperations.py": { ... }, ... },
    # }
"""

import ast
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# SIL namespace prefixes that indicate LCM dependencies
SIL_PREFIXES = (
    "SIL.LCModel",
    "SIL.FieldWorks",
    "SIL.WritingSystems",
    "SIL.Core",
)


def _is_sil_module(module_name):
    """Check if a module name is from the SIL/LCM ecosystem."""
    if module_name is None:
        return False
    return any(module_name.startswith(p) for p in SIL_PREFIXES)


def _relative_path(filepath, base):
    """Return filepath relative to base, using forward slashes."""
    try:
        return str(Path(filepath).relative_to(base)).replace(os.sep, "/")
    except ValueError:
        return str(filepath)


class LCMContractVisitor(ast.NodeVisitor):
    """AST visitor that extracts LCM dependencies from a single file."""

    def __init__(self):
        # module -> [imported_names]
        self.imports = defaultdict(list)
        # set of names known to be LCM types (from imports)
        self.lcm_names = set()
        # type_name -> {"properties": set, "methods": set}
        self.type_usage = defaultdict(lambda: {"properties": set(), "methods": set()})
        # local variable -> LCM type name (best-effort tracking)
        self.local_bindings = {}

    def visit_ImportFrom(self, node):
        """Capture ``from SIL.LCModel... import X, Y, Z``."""
        module = node.module or ""
        if _is_sil_module(module):
            for alias in node.names or []:
                name = alias.name
                local = alias.asname or name
                self.imports[module].append(name)
                self.lcm_names.add(local)
        self.generic_visit(node)

    def visit_Import(self, node):
        """Capture ``import SIL.LCModel...``."""
        for alias in node.names or []:
            if _is_sil_module(alias.name):
                local = alias.asname or alias.name
                self.imports[alias.name]  # ensure key exists
                self.lcm_names.add(local)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Track simple assignments like ``entry = factory.Create()``."""
        # Best-effort: if RHS is a call to a known factory, bind the target
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute):
                # e.g. factory.Create() -- we track the result type heuristically
                pass
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """
        Track attribute access on LCM objects.

        Captures patterns like:
          - ITsString.Text  (direct type attribute)
          - entry.LexemeFormOA  (on a variable known to hold an LCM object)
          - ILexEntryRepository (used as a type reference)
        """
        # Direct attribute on an LCM name: e.g. TsStringUtils.MakeString
        if isinstance(node.value, ast.Name) and node.value.id in self.lcm_names:
            type_name = node.value.id
            self.type_usage[type_name]["properties"].add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Track method calls on LCM types."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                caller = node.func.value.id
                if caller in self.lcm_names:
                    method = node.func.attr
                    self.type_usage[caller]["methods"].add(method)
        self.generic_visit(node)


def extract_file_contract(filepath):
    """
    Extract LCM contract from a single Python file.

    Args:
        filepath: Path to the .py file.

    Returns:
        dict with imports, type_usage, or None if file has no LCM deps.
    """
    try:
        source = Path(filepath).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return None

    visitor = LCMContractVisitor()
    visitor.visit(tree)

    if not visitor.imports:
        return None

    return {
        "imports": {mod: sorted(names) for mod, names in visitor.imports.items()},
        "type_usage": {
            typ: {
                "properties": sorted(info["properties"]),
                "methods": sorted(info["methods"]),
            }
            for typ, info in visitor.type_usage.items()
            if info["properties"] or info["methods"]
        },
    }


#: A small AST-parseable file, checked in alongside this extractor, that
#: registers LCM dependencies flexicon/code is specified to acquire soon
#: but does not yet import anywhere (e.g. the write-path-transactions
#: rewrite of transaction.py, tasks.md item B1). Scanned by the *same*
#: mechanism as flexicon/code -- not a parallel one -- so the contract test
#: suite can cover a type/member's shape before the real call site lands,
#: per tasks.md item CB ("Must land before B1"). See its module docstring.
PENDING_SEEDS_PATH = Path(__file__).resolve().parent / "pending_contract_seeds.py"


def extract_contract(source_root=None, pending_seeds_path=PENDING_SEEDS_PATH):
    """
    Extract the full LCM contract from the flexicon source tree.

    Args:
        source_root: Path to ``flexicon/code/``. Auto-detected if None.
        pending_seeds_path: Optional extra single file scanned with the same
            AST extractor, for anticipated dependencies not yet organic to
            source_root. Pass None to disable. Defaults to
            ``PENDING_SEEDS_PATH`` (``tests/contract/pending_contract_seeds.py``).

    Returns:
        dict with the complete contract:
        - imports: {module: [names]}  (deduplicated across all files)
        - type_usage: {type: {properties: [], methods: []}}
        - factories: [factory_names]
        - repositories: [repository_names]
        - files: {relative_path: per-file contract}
        - summary: {total_files, total_imports, total_types, ...}
    """
    if source_root is None:
        # Auto-detect: look for flexicon/code/ relative to this file.
        # flexicon/ is the post-rename package (was flexlibs2/ pre-9b82ffa);
        # both candidates are kept so this still works against older
        # checkouts/branches that predate the rename.
        here = Path(__file__).resolve().parent
        candidates = [
            here.parent.parent / "flexicon" / "code",
            here.parent / "flexicon" / "code",
            Path.cwd() / "flexicon" / "code",
            here.parent.parent / "flexlibs2" / "code",
            here.parent / "flexlibs2" / "code",
            Path.cwd() / "flexlibs2" / "code",
        ]
        for c in candidates:
            if c.is_dir():
                source_root = c
                break
        if source_root is None:
            raise FileNotFoundError("Cannot find flexicon/code/ (or legacy flexlibs2/code/). Pass source_root explicitly.")

    source_root = Path(source_root)

    # Aggregate contract
    all_imports = defaultdict(set)
    all_type_usage = defaultdict(lambda: {"properties": set(), "methods": set()})
    files = {}

    scan_targets = [(pyfile, _relative_path(pyfile, source_root.parent)) for pyfile in sorted(source_root.rglob("*.py"))]

    if pending_seeds_path is not None:
        pending_seeds_path = Path(pending_seeds_path)
        if pending_seeds_path.is_file():
            scan_targets.append((pending_seeds_path, f"_pending/{pending_seeds_path.name}"))

    for pyfile, relpath in scan_targets:
        file_contract = extract_file_contract(pyfile)
        if file_contract is None:
            continue

        files[relpath] = file_contract

        for mod, names in file_contract["imports"].items():
            all_imports[mod].update(names)

        for typ, info in file_contract["type_usage"].items():
            all_type_usage[typ]["properties"].update(info["properties"])
            all_type_usage[typ]["methods"].update(info["methods"])

    # Classify imports
    all_names = set()
    for names in all_imports.values():
        all_names.update(names)

    factories = sorted(n for n in all_names if n.endswith("Factory"))
    repositories = sorted(n for n in all_names if n.endswith("Repository"))
    interfaces = sorted(n for n in all_names if n.startswith("I") and n not in factories and n not in repositories)
    classes = sorted(n for n in all_names if not n.startswith("I") and n not in factories and n not in repositories)

    contract = {
        "imports": {mod: sorted(names) for mod, names in sorted(all_imports.items())},
        "type_usage": {
            typ: {
                "properties": sorted(info["properties"]),
                "methods": sorted(info["methods"]),
            }
            for typ, info in sorted(all_type_usage.items())
        },
        "factories": factories,
        "repositories": repositories,
        "interfaces": interfaces,
        "classes": classes,
        "files": files,
        "summary": {
            "total_files_with_lcm_deps": len(files),
            "total_unique_imports": len(all_names),
            "total_modules": len(all_imports),
            "total_factories": len(factories),
            "total_repositories": len(repositories),
            "total_interfaces": len(interfaces),
            "total_classes": len(classes),
            "total_type_usages_tracked": len(all_type_usage),
        },
    }
    return contract


def save_contract(contract, output_path):
    """Save contract to a JSON file."""
    Path(output_path).write_text(
        json.dumps(contract, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main():
    """CLI entry point: extract and save the contract."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract LCM API contract from flexlibs2 source.")
    parser.add_argument(
        "--source-root",
        default=None,
        help="Path to flexlibs2/code/ (auto-detected if omitted)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output JSON file (default: stdout)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary section",
    )
    args = parser.parse_args()

    contract = extract_contract(source_root=args.source_root)

    if args.summary_only:
        print(json.dumps(contract["summary"], indent=2))
        return

    if args.output:
        save_contract(contract, args.output)
        print(f"[DONE] Contract written to {args.output}")
        print(json.dumps(contract["summary"], indent=2))
    else:
        print(json.dumps(contract, indent=2))


if __name__ == "__main__":
    main()
