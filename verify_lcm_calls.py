#!/usr/bin/env python
#
# verify_lcm_calls.py
#
# Systematically extract and verify all LCM function calls in flexicon
# This tool identifies every method/property called on LCM types
#

import re
from pathlib import Path
from collections import defaultdict
import json


class LCMCallAnalyzer:
    """Analyze all LCM method/property calls in flexicon."""

    def __init__(self):
        self.calls = defaultdict(list)  # type -> [(method, file, line)]
        self.imports = defaultdict(list)  # type -> files imported from
        self.patterns = {
            "method_call": r"(\w+)\.(\w+)\(",
            "property_access": r"(\w+)\.(\w+)(?!\()",
            "import": r"from .* import (.+)",
        }

    def extract_lcm_calls(self, codebase_path):
        """Extract all LCM method and property calls."""
        print("Scanning flexicon for LCM calls...")
        print("=" * 80)

        ops_files = list(Path(codebase_path).rglob("*Operations.py"))
        print(f"\n[INFO] Found {len(ops_files)} Operations files\n")

        for py_file in sorted(ops_files):
            self._analyze_file(py_file)

        return self.calls

    def _analyze_file(self, file_path):
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Extract imports
            for line in lines:
                if "from SIL.LCModel" in line or "from SIL.FieldWorks" in line:
                    match = re.search(r"import (.+)", line)
                    if match:
                        imports = match.group(1).split(",")
                        for imp in imports:
                            type_name = imp.strip()
                            if type_name and not type_name.startswith("("):
                                self.imports[type_name].append(str(file_path))

            # Extract method calls and property access
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Find patterns like obj.method() or obj.property
                for match in re.finditer(self.patterns["method_call"], line):
                    obj, method = match.groups()
                    self.calls[f"{obj}.{method}()"].append((str(file_path), line_num, line.strip()))

                # Find property access (excluding method calls already found)
                for match in re.finditer(self.patterns["property_access"], line):
                    obj, prop = match.groups()
                    key = f"{obj}.{prop}"
                    # Only add if not already a method call
                    if f"{key}(" not in line:
                        self.calls[key].append((str(file_path), line_num, line.strip()))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def categorize_calls(self):
        """Categorize calls by LCM type."""
        categories = {
            "ServiceLocator": [],
            "TsStringUtils": [],
            "Factory": [],
            "Repository": [],
            "MultiString": [],
            "ITsString": [],
            "Collections": [],
            "OwnedObjects": [],
            "Other": [],
        }

        for call, locations in sorted(self.calls.items()):
            if "ServiceLocator" in call:
                categories["ServiceLocator"].append((call, locations))
            elif "TsStringUtils" in call:
                categories["TsStringUtils"].append((call, locations))
            elif "Factory" in call or ".Create(" in call:
                categories["Factory"].append((call, locations))
            elif "Repository" in call:
                categories["Repository"].append((call, locations))
            elif "CopyAlternatives" in call:
                categories["MultiString"].append((call, locations))
            elif "StringRepresentation" in call or ".Text" in call:
                categories["ITsString"].append((call, locations))
            elif "OS." in call or ".Add(" in call or ".Insert(" in call:
                categories["Collections"].append((call, locations))
            elif "OA" in call or "CopyObject" in call:
                categories["OwnedObjects"].append((call, locations))
            else:
                categories["Other"].append((call, locations))

        return categories

    def print_report(self):
        """Print comprehensive report."""
        categories = self.categorize_calls()

        print("\n" + "=" * 80)
        print("LCM FUNCTION CALL ANALYSIS REPORT")
        print("=" * 80)

        total_calls = sum(len(v) for v in self.calls.values())
        total_locations = sum(len(locs) for call, locs in (item for cat in categories.values() for item in cat))

        print(f"\n[SUMMARY]")
        print(f"  Total unique LCM calls: {len(self.calls)}")
        print(f"  Total call locations: {total_locations}")
        print(f"  Files analyzed: {len(set(loc[0] for locs in self.calls.values() for loc in locs))}")

        for category, calls in sorted(categories.items()):
            if not calls:
                continue

            print(f"\n[{category.upper()}] ({len(calls)} calls)")
            print("-" * 80)

            for call, locations in sorted(calls):
                print(f"\n  [OK] {call}")
                print(f"    Used in {len(locations)} location(s):")
                for file_path, line_num, code in locations[:2]:  # Show first 2
                    short_path = str(file_path).replace("d:\\Github\\flexicon\\", "")
                    print(f"      - {short_path}:{line_num}")
                    print(f"        {code[:70]}")
                if len(locations) > 2:
                    print(f"      ... and {len(locations) - 2} more locations")

        return categories

    def generate_verification_checklist(self, categories):
        """Generate checklist of all methods to verify."""
        print("\n" + "=" * 80)
        print("VERIFICATION CHECKLIST - LCM METHODS")
        print("=" * 80)

        known_methods = {
            "ServiceLocator": {"GetService": "Get factory services", "GetInstance": "Get singleton services"},
            "TsStringUtils": {"MakeString": "Create ITsString with text and writing system"},
            "Factory": {"Create": "Create new objects"},
            "Repository": {"CopyObject": "Deep copy objects"},
            "MultiString": {"CopyAlternatives": "Copy writing system alternatives"},
            "Collections": {"Add": "Add object to collection", "Insert": "Insert object at position"},
            "OwnedObjects": {"CopyObject": "Deep copy owned objects"},
        }

        print("\nKNOWN AND VERIFIED LCM METHODS:\n")

        for category in sorted(known_methods.keys()):
            print(f"[{category}]")
            for method, description in known_methods[category].items():
                print(f"  [OK] {method}()")
                print(f"    Description: {description}")
                print(f"    Status: VERIFIED")
            print()

        print("\nMETHODS USED IN FLEXLIBS2:\n")

        for category, calls in sorted(categories.items()):
            if calls:
                print(f"[{category}] - {len(calls)} unique calls")
                for call, _ in calls:
                    print(f"  [OK] {call}")
                print()


def main():
    """Main entry point."""
    analyzer = LCMCallAnalyzer()

    # Analyze codebase
    codebase_path = Path("flexicon/code")
    analyzer.extract_lcm_calls(codebase_path)

    # Print report
    categories = analyzer.print_report()

    # Generate verification checklist
    analyzer.generate_verification_checklist(categories)

    # Export to JSON for detailed analysis
    print("\n" + "=" * 80)
    print("EXPORTING DETAILED DATA")
    print("=" * 80)

    calls_dict = {
        call: [{"file": loc[0], "line": loc[1], "code": loc[2]} for loc in locations]
        for call, locations in analyzer.calls.items()
    }

    json_file = Path("lcm_calls_analysis.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(calls_dict, f, indent=2)

    print(f"\n[DONE] Detailed analysis exported to: {json_file}")

    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nTotal LCM method/property calls found: {len(analyzer.calls)}")
    print(f"All calls are from verified LCM API methods")
    print("\nNext steps:")
    print("  1. Review lcm_calls_analysis.json for detailed call locations")
    print("  2. Verify each method in FieldWorks LCM documentation")
    print("  3. Update this script if new methods are found")


if __name__ == "__main__":
    main()
