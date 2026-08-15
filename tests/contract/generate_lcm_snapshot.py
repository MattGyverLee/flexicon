#
#   generate_lcm_snapshot.py
#
#   Runtime introspector that connects to actual liblcm assemblies
#   via pythonnet and discovers the "provided contract" -- what liblcm
#   actually exposes.
#
#   Requires: FieldWorks installed, pythonnet, Windows (or Mono).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#   Copyright 2025
#

"""
Generate a snapshot of what the installed liblcm actually provides.

This module loads the SIL.LCModel assemblies via pythonnet and introspects
every type that flexicon depends on, recording which properties and methods
actually exist.

Usage::

    # From command line (on a machine with FieldWorks):
    python -m tests.contract.generate_lcm_snapshot -o snapshots/liblcm_9.1.22.json

    # Programmatically:
    from tests.contract.generate_lcm_snapshot import generate_snapshot
    snapshot = generate_snapshot(expected_contract)
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def _get_lcm_version():
    """Try to determine the liblcm/FieldWorks version."""
    try:
        import clr
        from SIL.LCModel import LcmCache

        asm = LcmCache.__class__.__module__
        # Try to get assembly version
        for a in clr.ListAssemblies():
            name = str(a)
            if "SIL.LCModel," in name:
                # Extract version from "SIL.LCModel, Version=X.Y.Z.W, ..."
                for part in name.split(","):
                    part = part.strip()
                    if part.startswith("Version="):
                        return part.split("=")[1]
        return "unknown"
    except Exception:
        return "unknown"


def _introspect_signatures(obj):
    """
    Best-effort deep reflection pass over an LCM type, on top of the
    dir()/GetMethods()-based member listing in ``_introspect_type``.

    ``_introspect_type`` answers "does this member name exist?" -- enough to
    catch a renamed or removed member (e.g. issue #235's non-existent
    ``LcmCache.UndoStack``). It cannot answer "does this member have the
    shape my code assumes?" -- the class of error behind issue #233
    (``BeginUndoTask`` called with 1 arg against a 2-arg API) and #236
    (``RollbackToMark``, an API that exists nowhere, called as if it did).

    This function uses ``clr.GetClrType()`` to get a real ``System.Type``
    and records, additively:
      - ``constructors``: list of parameter-type-name lists, one per ctor
        overload
      - ``method_signatures``: {method_name: [param-type-name lists]},
        one entry per overload
      - ``interfaces``: full names of interfaces the type implements
        (e.g. "System.IDisposable")
      - ``implements_idisposable``: convenience bool derived from the above
      - ``reflected_properties``: {prop_name: {"type": ..., "can_read": bool,
        "can_write": bool}}, straight from ``Type.GetProperties()``. This is
        deliberately kept separate from the top-level ``properties`` list
        (which comes from a Python ``dir()`` fallback for types whose CLR
        metatype isn't directly reflectable -- see ``_introspect_type``).
        That fallback misses write-only properties like
        ``UndoableUnitOfWorkHelper.RollBack`` ({private get; set;}) under
        their plain name, surfacing only a ``set_RollBack`` accessor. Use
        this field, not ``properties``, when a check needs to know whether a
        property exists at all regardless of read/write direction.

    Returns an empty-shaped dict (all fields present, empty/False) on any
    failure -- this is a best-effort enrichment, not required for
    ``_introspect_type`` to succeed.
    """
    empty = {
        "constructors": [],
        "method_signatures": {},
        "interfaces": [],
        "implements_idisposable": False,
        "reflected_properties": {},
    }

    try:
        import clr

        net_type = clr.GetClrType(obj)
    except Exception:
        return empty

    try:
        constructors = []
        for ctor in net_type.GetConstructors():
            constructors.append([str(p.ParameterType.Name) for p in ctor.GetParameters()])

        method_signatures = {}
        for method in net_type.GetMethods():
            name = str(method.Name)
            if name.startswith(("get_", "set_", "add_", "remove_")):
                continue
            if name in ("ToString", "GetHashCode", "Equals", "GetType", "ReferenceEquals"):
                continue
            params = [str(p.ParameterType.Name) for p in method.GetParameters()]
            method_signatures.setdefault(name, []).append(params)

        interfaces = sorted(str(i.FullName) for i in net_type.GetInterfaces())

        reflected_properties = {}
        for prop in net_type.GetProperties():
            reflected_properties[str(prop.Name)] = {
                "type": str(prop.PropertyType.Name),
                "can_read": bool(prop.CanRead),
                "can_write": bool(prop.CanWrite),
            }

        return {
            "constructors": constructors,
            "method_signatures": method_signatures,
            "interfaces": interfaces,
            "implements_idisposable": "System.IDisposable" in interfaces,
            "reflected_properties": reflected_properties,
        }
    except Exception:
        return empty


def _introspect_type(type_name, namespace_hint=None):
    """
    Introspect a single LCM type and return its members.

    Args:
        type_name: The type name (e.g. "ILexEntry", "TsStringUtils").
        namespace_hint: Full namespace to look in (e.g. "SIL.LCModel").

    Returns:
        dict with properties, methods, whether the type was found, and
        (best-effort) constructors/method_signatures/interfaces from
        ``_introspect_signatures``.
    """
    result = {
        "found": False,
        "properties": [],
        "methods": [],
        "error": None,
        "constructors": [],
        "method_signatures": {},
        "interfaces": [],
        "implements_idisposable": False,
        "reflected_properties": {},
    }

    try:
        import clr

        # Try to resolve the type from CLR
        obj = None
        if namespace_hint:
            try:
                mod = __import__(namespace_hint, fromlist=[type_name])
                obj = getattr(mod, type_name, None)
            except (ImportError, AttributeError):
                pass

        if obj is None:
            # Try common SIL namespaces
            for ns in [
                "SIL.LCModel",
                "SIL.LCModel.Core.KernelInterfaces",
                "SIL.LCModel.Core.Text",
                "SIL.LCModel.Core.Cellar",
                "SIL.LCModel.Infrastructure",
                "SIL.LCModel.Utils",
            ]:
                try:
                    mod = __import__(ns, fromlist=[type_name])
                    obj = getattr(mod, type_name, None)
                    if obj is not None:
                        break
                except (ImportError, AttributeError):
                    continue

        if obj is None:
            result["error"] = f"Type {type_name} not found in any SIL namespace"
            return result

        result["found"] = True

        # Best-effort deep reflection (constructors/signatures/interfaces).
        # Additive only -- does not alter the properties/methods derivation
        # below, so it cannot shift existing baseline entries for the
        # ~246 types already tracked.
        result.update(_introspect_signatures(obj))

        # Get members via .NET reflection
        clr_type = None
        if hasattr(obj, "__class__") and hasattr(obj.__class__, "GetMembers"):
            clr_type = obj.__class__
        elif hasattr(obj, "GetMembers"):
            clr_type = obj
        else:
            # For static classes and interfaces, try to get the type object
            try:
                import System

                clr_type = obj if hasattr(obj, "GetProperties") else type(obj)
            except Exception:
                pass

        if clr_type is not None and hasattr(clr_type, "GetProperties"):
            try:
                for prop in clr_type.GetProperties():
                    result["properties"].append(str(prop.Name))
            except Exception:
                pass

            try:
                for method in clr_type.GetMethods():
                    name = str(method.Name)
                    # Skip property accessors and standard object methods
                    if not name.startswith(("get_", "set_", "add_", "remove_")):
                        if name not in ("ToString", "GetHashCode", "Equals", "GetType", "ReferenceEquals"):
                            result["methods"].append(name)
            except Exception:
                pass
        else:
            # Fallback: use Python dir()
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                try:
                    attr = getattr(obj, attr_name)
                    if callable(attr):
                        result["methods"].append(attr_name)
                    else:
                        result["properties"].append(attr_name)
                except Exception:
                    result["properties"].append(attr_name)

        result["properties"] = sorted(set(result["properties"]))
        result["methods"] = sorted(set(result["methods"]))

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"

    return result


def generate_snapshot(expected_contract):
    """
    Generate a snapshot of the installed liblcm, checking every type
    that flexicon expects.

    Args:
        expected_contract: The contract dict from extract_lcm_contract.

    Returns:
        dict with snapshot data including which types/members exist.
    """
    # Initialize FLEx/pythonnet
    try:
        from flexicon.code.FLExInit import FLExInitialize

        FLExInitialize()
    except ImportError:
        # Try direct pythonnet init
        import clr

        clr.AddReference("SIL.LCModel")
        clr.AddReference("SIL.LCModel.Core")

    version = _get_lcm_version()

    # Build namespace hints from imports
    name_to_namespace = {}
    for module, names in expected_contract.get("imports", {}).items():
        for name in names:
            name_to_namespace[name] = module

    # Introspect every imported type
    types = {}
    all_names = set()
    for names in expected_contract.get("imports", {}).values():
        all_names.update(names)

    for type_name in sorted(all_names):
        ns_hint = name_to_namespace.get(type_name)
        types[type_name] = _introspect_type(type_name, namespace_hint=ns_hint)

    # Check expected member access patterns
    member_checks = {}
    for type_name, usage in expected_contract.get("type_usage", {}).items():
        if type_name not in types:
            continue
        provided = types[type_name]
        if not provided["found"]:
            continue

        provided_props = set(provided["properties"])
        provided_methods = set(provided["methods"])

        expected_props = set(usage.get("properties", []))
        expected_methods = set(usage.get("methods", []))

        missing_props = sorted(expected_props - provided_props)
        missing_methods = sorted(expected_methods - provided_methods)
        extra_props = sorted(provided_props - expected_props)
        extra_methods = sorted(provided_methods - expected_methods)

        if missing_props or missing_methods:
            member_checks[type_name] = {
                "missing_properties": missing_props,
                "missing_methods": missing_methods,
                "extra_properties": extra_props,
                "extra_methods": extra_methods,
            }

    # Count results
    found_types = [t for t, info in types.items() if info["found"]]
    missing_types = [t for t, info in types.items() if not info["found"]]

    snapshot = {
        "metadata": {
            "liblcm_version": version,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "python_version": sys.version,
            "platform": sys.platform,
        },
        "types": types,
        "member_checks": member_checks,
        "summary": {
            "total_types_checked": len(types),
            "types_found": len(found_types),
            "types_missing": len(missing_types),
            "types_with_member_mismatches": len(member_checks),
        },
        "missing_types": missing_types,
    }
    return snapshot


def save_snapshot(snapshot, output_path):
    """Save snapshot to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(snapshot, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main():
    """CLI entry point: generate and save a liblcm snapshot."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate liblcm API snapshot from installed assemblies.")
    parser.add_argument(
        "--contract",
        "-c",
        default=None,
        help="Path to expected contract JSON (from extract_lcm_contract). " "If omitted, extracts contract first.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output JSON file for the snapshot.",
    )
    args = parser.parse_args()

    # Load or generate expected contract
    if args.contract:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    else:
        from tests.contract.extract_lcm_contract import extract_contract

        contract = extract_contract()

    snapshot = generate_snapshot(contract)
    save_snapshot(snapshot, args.output)

    print(f"[DONE] Snapshot written to {args.output}")
    print(f"  LibLCM version: {snapshot['metadata']['liblcm_version']}")
    s = snapshot["summary"]
    print(f"  Types checked: {s['total_types_checked']}")
    print(f"  Types found:   {s['types_found']}")
    print(f"  Types missing: {s['types_missing']}")
    print(f"  Member mismatches: {s['types_with_member_mismatches']}")

    if snapshot["missing_types"]:
        print("\n  Missing types:")
        for t in snapshot["missing_types"]:
            print(f"    - {t}")


if __name__ == "__main__":
    main()
