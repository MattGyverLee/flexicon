# LibLCM Contract Testing

FlexLibs2 depends on ~226 types from SIL's LibLCM assemblies across 72 source files. The contract test suite verifies that these dependencies stay consistent -- both within flexlibs2 code and against installed versions of LibLCM.

## Quick Start

**Install the pre-commit hook (one time per machine):**

```bash
python hooks/install.py
```

That's it. Every `git commit` now runs a sub-second contract check before committing.

## What It Does

The contract test system works in two modes:

### Mode 1: Static Analysis (runs anywhere, no FieldWorks needed)

Parses every `.py` file in `flexlibs2/code/` using Python's AST module and extracts:

- Every `from SIL.LCModel import ...` statement
- Which properties and methods are called on those types
- Which factories and repositories are used

This produces an "expected contract" -- what flexlibs2 *needs* from LibLCM.

The pre-commit hook compares this against a checked-in baseline and catches:

- **New LCM dependencies** you may have added unintentionally
- **Removed LCM dependencies** that signal refactoring (warning only)
- **Dramatic structural changes** (>20% file count shift)

### Mode 2: Live Verification (requires FieldWorks + pythonnet)

Connects to actual LibLCM assemblies via pythonnet and checks that every type, property, and method flexlibs2 expects actually exists. This mode:

- Verifies all 226 types are present in the installed LibLCM
- Checks that every property/method access in your code has a matching member
- Produces a compatibility score (target: 100%)
- Saves snapshots for regression tracking across LibLCM versions

## Usage

### Pre-commit hook (automatic)

After `python hooks/install.py`, it runs on every commit:

```
$ git commit -m "Add new feature"
[INFO] Running LCM contract tests...
10 passed, 6 skipped in 0.29s
[PASS] LCM contract tests passed.
```

If it fails:

```
[FAIL] LCM contract tests failed.
  If you added new SIL.LCModel imports, update the baseline:
    python -m tests.contract.extract_lcm_contract -o tests/contract/snapshots/expected_contract.json
  To skip this check once:
    SKIP_CONTRACT_TESTS=1 git commit ...
```

### Running tests manually

```bash
# Static tests only (works anywhere)
pytest tests/contract/ --override-ini="confcutdir=tests/contract" -v

# Full verification (on a machine with FieldWorks)
pytest tests/contract/ --override-ini="confcutdir=tests/contract" -v
```

### Updating the baseline

After intentionally adding or removing LCM imports:

```bash
python -m tests.contract.extract_lcm_contract -o tests/contract/snapshots/expected_contract.json
```

Commit the updated `expected_contract.json` alongside your code changes.

### Quick summary of current dependencies

```bash
python -m tests.contract.extract_lcm_contract --summary-only
```

Output:

```json
{
  "total_files_with_lcm_deps": 72,
  "total_unique_imports": 226,
  "total_modules": 12,
  "total_factories": 70,
  "total_repositories": 19,
  "total_interfaces": 96,
  "total_classes": 41,
  "total_type_usages_tracked": 23
}
```

## Workflow: Upgrading FieldWorks / LibLCM

1. **Before upgrading**, generate a snapshot from the current version:

   ```bash
   python -m tests.contract.generate_lcm_snapshot \
     -o tests/contract/snapshots/liblcm_9.1.json
   ```

2. **Install the new FieldWorks version.**

3. **Generate a snapshot from the new version:**

   ```bash
   python -m tests.contract.generate_lcm_snapshot \
     -o tests/contract/snapshots/liblcm_9.3.json
   ```

4. **Diff the two snapshots:**

   ```bash
   python -m tests.contract.compare_contracts diff \
     --old tests/contract/snapshots/liblcm_9.1.json \
     --new tests/contract/snapshots/liblcm_9.3.json -v
   ```

   Output shows exactly what changed:

   ```
   LibLCM Contract Test: [FAIL]
   ==================================================
   Old version: 9.1.22.0
   New version: 9.3.1.0
   Regressions: 3
   Additions:   12

   REGRESSIONS:
     [WARN] ILexEntry.SomeOldProperty removed
     [WARN] IWfiAnalysis.DeprecatedMethod() removed
     ...

   ADDITIONS:
     [INFO] ILexEntry.NewProperty added
     ...
   ```

5. **Check impact on your code:**

   ```bash
   python -m tests.contract.compare_contracts check \
     --contract tests/contract/snapshots/expected_contract.json \
     --snapshot tests/contract/snapshots/liblcm_9.3.json -v
   ```

   This maps every breakage back to the specific flexlibs2 source files affected.

## File Structure

```
tests/contract/
    __init__.py
    conftest.py                  # Overrides parent fixture (no FW needed)
    extract_lcm_contract.py      # AST-based static extractor
    generate_lcm_snapshot.py     # Runtime LibLCM introspector
    compare_contracts.py         # Diff engine + report formatter
    test_lcm_contract.py         # Pytest runner (16 tests)
    snapshots/
        expected_contract.json   # Baseline: what flexlibs2 expects

hooks/
    pre-commit                   # Git hook script
    install.py                   # Hook installer/uninstaller
```

## Escape Hatches

```bash
# Skip the hook for one commit
SKIP_CONTRACT_TESTS=1 git commit -m "WIP"

# Uninstall the hook entirely
python hooks/install.py --remove
```

## Why Not CI?

The full verification (Mode 2) requires FieldWorks installed, which means Windows + .NET assemblies loaded via pythonnet. This cannot run in a typical CI environment. The static analysis (Mode 1) *can* run in CI and does not require any special dependencies beyond Python 3.8+.
