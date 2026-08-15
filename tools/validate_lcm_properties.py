#!/usr/bin/env python3
"""
validate_lcm_properties.py

Validates that property/method accesses on LibLCM objects in flexicon code
actually exist in the LibLCM API. Catches typos like:
  - HumanApprovedAnalysesRS (wrong) vs HumanApprovedAnalyses (correct)

Usage:
    python tools/validate_lcm_properties.py
    python tools/validate_lcm_properties.py --lcm-index path/to/liblcm_api.json
    python tools/validate_lcm_properties.py --verbose

This tool:
1. Scans flexicon Python files for property/method accesses
2. Identifies accesses on known LibLCM interface types
3. Cross-references against the LibLCM API index
4. Reports any properties that don't exist (potential typos)
"""

import ast
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple, Optional

# Known LibLCM interface prefixes - objects starting with these are LibLCM types
LCM_INTERFACE_PREFIXES = [
    "IWfi",
    "ILex",
    "ICm",
    "IFs",
    "IDs",
    "IText",
    "IScrBook",
    "IScrSection",
    "IStText",
    "IStPara",
    "ISegment",
    "IMo",
    "IPhon",
    "IRnGenericRec",
    "IReversalIndex",
    "IConstChart",
    "IChkRef",
    "IChkTerm",
    "IChkSense",
    "ILangProject",
    "IPartOfSpeech",
    "IAnalysis",
    "IWfiWordform",
]

# Variable names that typically hold LibLCM objects
# Be specific to avoid false positives on Python string variables
LCM_VARIABLE_PATTERNS = [
    r"^wordform$",
    r"^analysis$",
    r"^gloss$",
    r"^entry$",
    r"^sense$",
    r"^bundle$",
    r"^morph$",
    r"^allomorph$",
    r"^pos$",
    r"^category$",
    r"^owner$",
    r"^target$",
    r"^lexeme$",
    r"^msa$",
    r"^example$",
    r"^domain$",
    r"^reference$",
    r"^variant$",
    r"^component$",
    r"^reversal$",
    r"^pronunciation$",
    r"^new_\w+$",
    r"^source_\w+$",
    r"^morph_data$",
    r"^entry_ref$",
    r"_or_hvo$",
]

# Exclude these variable names (commonly hold Python strings, not LCM objects)
EXCLUDE_VARIABLE_PATTERNS = [
    r"^form$",
    r"^text$",
    r"^name$",
    r"^translation$",
    r"_text$",
    r"_name$",
    r"^gloss_text$",
    r"^example_text$",
    r"^pos_name$",
    r"^platform$",
]


class PropertyAccessVisitor(ast.NodeVisitor):
    """AST visitor that extracts property/method accesses."""

    def __init__(self, filename: str):
        self.filename = filename
        self.accesses: List[Tuple[str, str, int]] = []  # (variable, property, line)

    def visit_Attribute(self, node: ast.Attribute):
        """Visit attribute access like obj.property"""
        # Get the variable name being accessed
        var_name = self._get_base_name(node.value)
        if var_name:
            self.accesses.append((var_name, node.attr, node.lineno))
        self.generic_visit(node)

    def _get_base_name(self, node) -> Optional[str]:
        """Extract the base variable name from an expression."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # For chained access like obj.prop1.prop2, get the innermost
            return self._get_base_name(node.value)
        elif isinstance(node, ast.Subscript):
            return self._get_base_name(node.value)
        elif isinstance(node, ast.Call):
            return self._get_base_name(node.func)
        return None


def load_lcm_properties(index_path: Path) -> Dict[str, Set[str]]:
    """
    Load known LibLCM properties from the API index.

    Returns:
        Dict mapping interface name to set of valid property/method names
    """
    properties: Dict[str, Set[str]] = defaultdict(set)

    if not index_path.exists():
        print(f"[WARN] LibLCM index not found: {index_path}")
        return properties

    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities", {})
    for entity_name, entity_data in entities.items():
        # Add methods
        for method in entity_data.get("methods", []):
            method_name = method.get("name", "")
            if method_name:
                properties[entity_name].add(method_name)

        # Add properties
        for prop in entity_data.get("properties", []):
            prop_name = prop.get("name", "")
            if prop_name:
                properties[entity_name].add(prop_name)

    return properties


def load_lcm_properties_enhanced(index_path: Path) -> Tuple[Dict[str, Set[str]], Set[str]]:
    """
    Load LibLCM properties with enhanced extraction.

    Returns:
        Tuple of (interface->properties dict, set of all known properties)
    """
    properties: Dict[str, Set[str]] = defaultdict(set)
    all_properties: Set[str] = set()

    if not index_path.exists():
        print(f"[WARN] LibLCM index not found: {index_path}")
        return properties, all_properties

    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities", {})
    for entity_name, entity_data in entities.items():
        # Add methods
        for method in entity_data.get("methods", []):
            method_name = method.get("name", "")
            if method_name:
                properties[entity_name].add(method_name)
                all_properties.add(method_name)

        # Add properties
        for prop in entity_data.get("properties", []):
            prop_name = prop.get("name", "")
            if prop_name:
                properties[entity_name].add(prop_name)
                all_properties.add(prop_name)

    # Also check method_index for additional properties
    method_index = data.get("method_index", {})
    for method_key in method_index.keys():
        if "." in method_key:
            prop_name = method_key.split(".")[-1]
            all_properties.add(prop_name)

    return properties, all_properties


def is_likely_lcm_variable(var_name: str) -> bool:
    """Check if a variable name likely holds an LCM object."""
    var_lower = var_name.lower()

    # First check exclusions (common Python string variables)
    for pattern in EXCLUDE_VARIABLE_PATTERNS:
        if re.search(pattern, var_lower):
            return False

    # Check against known LCM variable patterns
    for pattern in LCM_VARIABLE_PATTERNS:
        if re.search(pattern, var_lower):
            return True

    # Check for LCM interface type hints in name
    for prefix in LCM_INTERFACE_PREFIXES:
        if var_name.startswith(prefix):
            return True

    return False


def find_suspicious_properties(
    accesses: List[Tuple[str, str, int, str]],  # (var, prop, line, file)
    known_properties: Set[str],
    verbose: bool = False,
) -> List[Tuple[str, str, str, int, List[str]]]:
    """
    Find property accesses that might be typos.

    Returns:
        List of (file, variable, property, line, suggestions)
    """
    suspicious = []

    for var_name, prop_name, line, filename in accesses:
        # Skip if it's a known property
        if prop_name in known_properties:
            continue

        # Skip private/dunder methods
        if prop_name.startswith("_"):
            continue

        # Skip common Python/CLR attributes and methods
        if prop_name in {
            "Count",
            "Add",
            "Remove",
            "Clear",
            "Contains",
            "Insert",
            "append",
            "extend",
            "items",
            "keys",
            "values",
            "get",
            "set",
            "update",
            "pop",
            "copy",
            # Python string methods (false positives on 'form', 'text' vars)
            "strip",
            "lower",
            "upper",
            "split",
            "join",
            "replace",
            "startswith",
            "endswith",
            "find",
            "format",
            "encode",
            # CLR TsString methods (valid LCM patterns)
            "get_String",
            "set_String",
            "GetWsString",
            "SetString",
            # CLR collection methods
            "GetEnumerator",
            "ToArray",
            "CopyTo",
            "ToList",
            # CLR type checking patterns
            "IsInstance",
            "IsAssignableFrom",
            # Tags constants
            "kClassId",
            "kflidOwner",
            # Standard .NET
            "ToString",
            "GetType",
            "Equals",
            "GetHashCode",
            # CLR list append pattern
            "Append",
        }:
            continue

        # Find similar properties (for suggestions)
        suggestions = find_similar_properties(prop_name, known_properties)

        # Only report if we have suggestions (likely typo) or it's a suspicious pattern
        if suggestions or is_suspicious_pattern(prop_name):
            suspicious.append((filename, var_name, prop_name, line, suggestions))

    return suspicious


def find_similar_properties(prop_name: str, known_properties: Set[str]) -> List[str]:
    """Find similar property names that might be what was intended."""
    suggestions = []

    for known in known_properties:
        # Check for close matches
        if levenshtein_distance(prop_name.lower(), known.lower()) <= 3:
            suggestions.append(known)
        # Check for common suffix/prefix issues (like RS suffix)
        elif prop_name.rstrip("RS").rstrip("OC").rstrip("OS") == known:
            suggestions.append(known)
        elif prop_name == known.rstrip("RS").rstrip("OC").rstrip("OS"):
            suggestions.append(known)
        # Check for substring matches
        elif prop_name in known or known in prop_name:
            if abs(len(prop_name) - len(known)) <= 4:
                suggestions.append(known)

    return sorted(set(suggestions))[:5]  # Limit to top 5


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def is_suspicious_pattern(prop_name: str) -> bool:
    """Check if property name has suspicious patterns (common typo indicators)."""
    # Properties ending in RS, OC, OS are LibLCM collection conventions
    # A typo might add/remove these incorrectly
    if prop_name.endswith("RS") or prop_name.endswith("OC") or prop_name.endswith("OS"):
        return True

    # CamelCase with unusual capitalization
    if re.search(r"[a-z][A-Z]{2,}[a-z]", prop_name):
        return True

    return False


def scan_flexicon_code(flexicon_path: Path) -> List[Tuple[str, str, int, str]]:
    """
    Scan flexicon Python code for property accesses.

    Returns:
        List of (variable_name, property_name, line_number, filename)
    """
    all_accesses = []
    code_path = flexicon_path / "flexicon" / "code"

    if not code_path.exists():
        print(f"[ERROR] flexicon code directory not found: {code_path}")
        return all_accesses

    for py_file in code_path.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(py_file))
            visitor = PropertyAccessVisitor(str(py_file))
            visitor.visit(tree)

            # Filter to likely LCM variable accesses
            for var_name, prop_name, line in visitor.accesses:
                if is_likely_lcm_variable(var_name):
                    rel_path = py_file.relative_to(flexicon_path)
                    all_accesses.append((var_name, prop_name, line, str(rel_path)))

        except SyntaxError as e:
            print(f"[WARN] Syntax error in {py_file}: {e}")
        except Exception as e:
            print(f"[WARN] Error processing {py_file}: {e}")

    return all_accesses


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate LibLCM property accesses in flexicon")
    parser.add_argument(
        "--flexicon-path", type=Path, default=Path(__file__).parent.parent, help="Path to flexicon repository"
    )
    parser.add_argument(
        "--lcm-index",
        type=Path,
        default=Path(__file__).parent.parent.parent / "FlexToolsMCP" / "index" / "liblcm" / "liblcm_api.json",
        help="Path to LibLCM API index JSON",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--all", "-a", action="store_true", help="Show all suspicious accesses, not just likely typos")

    args = parser.parse_args()

    print("=" * 60)
    print("flexicon LibLCM Property Validator")
    print("=" * 60)
    print()

    # Load known LibLCM properties
    print(f"[INFO] Loading LibLCM properties from: {args.lcm_index}")
    interface_props, all_properties = load_lcm_properties_enhanced(args.lcm_index)
    print(f"[INFO] Loaded {len(all_properties)} unique property/method names")
    print()

    # Scan flexicon code
    print(f"[INFO] Scanning flexicon code: {args.flexicon_path}")
    accesses = scan_flexicon_code(args.flexicon_path)
    print(f"[INFO] Found {len(accesses)} property accesses on LCM-like variables")
    print()

    # Find suspicious properties
    suspicious = find_suspicious_properties(accesses, all_properties, args.verbose)

    if not suspicious:
        print("[OK] No suspicious property accesses found!")
        print()
        print("All property names appear to match known LibLCM API.")
        return 0

    # Report findings
    print(f"[WARN] Found {len(suspicious)} potentially invalid property accesses:")
    print()

    # Group by file
    by_file: Dict[str, List] = defaultdict(list)
    for filename, var_name, prop_name, line, suggestions in suspicious:
        by_file[filename].append((var_name, prop_name, line, suggestions))

    for filename in sorted(by_file.keys()):
        print(f"  {filename}:")
        for var_name, prop_name, line, suggestions in by_file[filename]:
            print(f"    Line {line}: {var_name}.{prop_name}")
            if suggestions:
                print(f"      -> Did you mean: {', '.join(suggestions)}?")
        print()

    print("-" * 60)
    print(f"Total: {len(suspicious)} suspicious accesses in {len(by_file)} files")
    print()
    print("To investigate, check if these properties exist on the target LCM type.")
    print("Common issues:")
    print("  - Wrong suffix (RS vs OC vs OS)")
    print("  - Typos in property names")
    print("  - Using deprecated property names")

    return 1 if suspicious else 0


if __name__ == "__main__":
    sys.exit(main())
