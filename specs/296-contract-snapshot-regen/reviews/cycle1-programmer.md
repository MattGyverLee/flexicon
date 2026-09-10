# Cycle 1 -- Programmer report: #296 contract snapshot regen

## Summary
Regenerated `tests/contract/snapshots/expected_contract.json`. Extractor is
deterministic (byte-identical on a second run). Measured drift matches issue
#296's 2026-09-09 measurement **exactly** -- no discrepancy. Gate: 22 passed.
Working tree has pre-existing unrelated dirty files not caused by this task.

## Determinism
Ran extractor twice (repo path, then scratch path), SHA-256 identical:
`dc5f2cb1...66a4df1e` both times. No P0.

## Structural diff

**Files added:**
| file |
|---|
| `code/transaction.py` |
| `code/undoable_operation.py` |

**Files removed:** none.

**Files changed** (symbol-level):
| file | change |
|---|---|
| `code/BaseOperations.py` | `SIL.LCModel` imports: `IFsClosedValue`, `IFsClosedValueFactory`, `IFsComplexValue`, `IFsComplexValueFactory`, `IFsFeatStruc`, `IFsFeatStrucFactory` (dup entries per usage site) |
| `code/FLExInit.py` | `Sldr.properties` +`IsInitialized` |
| `code/FLExProject.py` | `SIL.LCModel` +`LexEntryRefTags`; `KernelInterfaces` +`FwTextPropType`; new type `FwTextPropType` (`ktptObjData`); new type `LexEntryRefTags` (`krtComplexForm`, pre-existing at top level from another file); `TsStringUtils` +`MakePropsBldr`, +`MakeStrBldr` (props+methods) |
| `code/Grammar/NaturalClassOperations.py` | `SIL.LCModel` +`IFsClosedValueFactory`, `IFsFeatStruc`, `IFsFeatStrucFactory` |
| `code/Lexicon/AllomorphOperations.py` | `SIL.LCModel` +`IMoAffixAllomorph`, `IMoStemAllomorph`; -`IMoForm` |
| `code/TextsWords/WfiMorphBundleOperations.py` | `SIL.LCModel` +`IMoForm`; -`IMoMorphType` |
| `code/lcm_casting.py` | `SIL.LCModel` +`ICmAnnotationDefn`, `ICmLocation`, `ICmPerson`, `ICmSemanticDomain`, `IConstChartClauseMarker`, `IConstChartMovedTextMarker`, `IConstChartRow`, `IConstChartTag`, `IConstChartWordGroup`, `IFsClosedValue`, `IFsComplexFeature`, `IFsComplexValue`, `IFsFeatStruc`, `ILangProject`, `ILexEntryType`, `IMoMorphType`, `IPartOfSpeech`, `IPhNCFeatures`, `IPhNCSegments`, `IPhPhoneme` |

**`type_usage` deltas (top-level):**
| type | change |
|---|---|
| `FwTextPropType` | new entry: properties/methods `ktptObjData` |
| `Sldr` | properties +`IsInitialized` |
| `TsStringUtils` | properties/methods +`MakePropsBldr`, +`MakeStrBldr` |

**Summary scalars:**
| key | old | new |
|---|---|---|
| `total_files_with_lcm_deps` | 78 | 80 |
| `total_unique_imports` | 257 | 258 |
| `total_modules` | 14 | 14 |
| `total_factories` | 81 | 81 |
| `total_repositories` | 19 | 19 |
| `total_interfaces` | 104 | 104 |
| `total_classes` | 53 | 54 (`FwTextPropType` added to `classes` list) |
| `total_type_usages_tracked` | 34 | 35 |

## Issue #296 cross-check
**No discrepancy.** Every item (2 files added, 7 files changed, 3 `type_usage`
changes, all 4 metadata deltas) matches the issue's 2026-09-09 measurement
exactly, symbol-for-symbol. Nothing landed on `main` since that touches the
LCM-dependency surface.

## Gate results
- `python -m pytest tests/contract/test_lcm_contract.py -m "not requires_liblcm" -q` -> **22 passed in 2.35s** (exit 0).
- Full run (no `-m` filter) also executed and gave the identical result:
  **22 passed in 2.19s** (exit 0). Note: `requires_liblcm` is a `pytest.mark.skipif`,
  not a registered custom marker, so `-m "not requires_liblcm"` does not actually
  deselect the live class -- both invocations run the same 22 tests. This machine
  has FieldWorks + pythonnet available (`clr.AddReference("SIL.LCModel")`
  succeeds), so `TestLiveContractVerification` genuinely ran live in both cases,
  not skipped.
- Both runs print `Windows fatal exception: access violation` with a traceback
  through `FLExInitialize` during the live fixture, but the process does not
  crash and all 22 tests pass with exit code 0 -- appears to be a benign
  pythonnet/CLR faulthandler artifact on this box, pre-existing and unrelated
  to the snapshot content. Flagging for awareness, not blocking.

## git status -- P0
Only `tests/contract/snapshots/expected_contract.json` is the change from this
task. However `git status --porcelain` shows **pre-existing, unrelated dirty
state** that was already present before this task's first command ran:
`CHANGELOG.md`, `docs/API_ISSUES_CATEGORIZED.md`, `docs/EXCEPTION_HANDLING.md`,
`flexicon/sync/tests/test_base_operations.py`, `tests/conftest.py`,
`tests/test_flexlibs2_alias_ratchet.py`, plus untracked
`tests/test_264_sldr_single_init_path.py`. A new untracked directory
`specs/264-conftest-sldr-order/` appeared between my first and last
`git status` check, i.e. **during this task's run**, from a source outside
this task. Flagging as P0 per instructions; not cleaned up.

## Working tree left dirty per instructions (not committed).
