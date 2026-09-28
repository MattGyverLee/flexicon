# Issue #217 - ApplySyncableProperties test coverage

File: `tests/operations/test_apply_syncable_properties.py` (43 tests total:
38 run, 5 gated/skipped in this env). Production code untouched.

## Run result
`python -m pytest tests/operations/test_apply_syncable_properties.py -q -m "not requires_live_project"`
-> 38 passed, 5 deselected. `--collect-only` confirms all 43 collect with no
errors.

## Mock vs live split
- **Section A** (`TestApplyPropsLoop*`, 21 tests): call `_apply_props_loop`
  directly with fake item/`_FakeMultiString`/`_FakeTsStringUtils` objects.
  No `SIL.LCModel` import touched. Runs everywhere.
- **Section B** (`TestApplySyncablePropertiesGuards`, 4 tests): call the
  real `ApplySyncableProperties()` method via a bare `BaseOperations`
  instance + fake `project.writeEnabled`. Works because `_EnsureWriteEnabled`
  / `FP_NullParameterError` / `FP_ParameterError` all fire before the
  method's lazy `from SIL.LCModel.Core.Text import TsStringUtils` import.
- **Section C** (`TestSyncTypeCorrectionsStatic` + `...ApplySide`, 9 tests):
  source-inspection locks (style of `test_owner_cast_pattern.py`) pinning
  the 171a9a7 IMultiString-vs-ITsString field shapes per class. This DOES
  import the real Lexicon Operations modules, which succeeds here because
  FieldWorks 9 happens to be installed on this machine and `flexicon`'s
  package init wires up the pythonnet CLR bindings for `SIL.LCModel`
  on first import (confirmed: bare `import SIL.LCModel` fails, but
  `import flexicon; import SIL.LCModel` succeeds). Elsewhere without
  FieldWorks, these 9 tests would fail at collection/import time -
  flagging this as an environment note for `/lex-lead`/QC, not something
  fixed here (test-only task).
- **Section D** (`TestApplySyncablePropertiesLive`, 5 tests, marked
  `requires_live_project`): true apply -> `GetSyncableProperties` round
  trips against a real writable project (`writable_project` fixture,
  `_CANDIDATE_PROJECTS` convention). These WRITE throwaway senses/
  examples/etymologies/pronunciations and REQUIRE a `-restore`'d project
  afterward. Per task instruction I did not execute this section even
  though a writable `Sena 3`-style project is technically reachable here.

## Requirement -> test mapping
1. multistring dict round-trip: `TestApplyPropsLoopMultistring.test_multistring_apply_and_readback_identity` (+ws-not-on-target/missing-prop/fill-gaps siblings)
2. plain str setattr: `TestApplyPropsLoopPlainStr.test_plain_str_setattr_path` (+missing-prop/fill-gaps/object-ref-mismatch/unrelated-TypeError-reraise siblings)
3. bool setattr: `TestApplyPropsLoopBoolInt.test_bool_setattr_path` (+fill-gaps-always-skip/missing/setattr-failure/bool-before-int siblings)
4. ITsString coercion via `TsStringUtils.MakeString`: `TestApplyPropsLoopTsStringFallback.test_tsstring_prop_coerced_via_make_string` (+no-utils-supplied / no-default-ws siblings, both proving skip-not-raise)
5. ws_map identity vs remap: `TestApplyPropsLoopWsMap` (3 tests: None=identity, remap, unmapped-target-skip)
6. 171a9a7 type-parity across Etymology/Example/LexEntry/LexSense/Pronunciation: `TestSyncTypeCorrectionsStatic.test_get_syncable_properties_field_shape` parametrized over Etymology.Source (multistring), LexSense.{Source,ScientificName,ImportResidue} (tsstring), LexEntry.ImportResidue (tsstring), Example.Reference (tsstring), Pronunciation.Form (multistring); plus `TestSyncTypeCorrectionsApplySide` pinning Example's `TsStringUtils.MakeString(ref_text...)` apply path and LexSense's *non*-special-casing of its ITsString fields (they fall through to the base fallback tested under requirement 4).

Files: `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_apply_syncable_properties.py`
