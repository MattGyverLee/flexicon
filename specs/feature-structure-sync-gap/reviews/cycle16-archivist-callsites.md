# Cycle 16 -- __GetAllomorphObject call-site coverage (pinned HEAD 09fcbf8)

## 1. Wide-instrument file set
Instrument: `git grep -ilE "allomorph|IMoForm|MoStemAllomorph|MoAffixAllomorph|MsEnvFeatures" 09fcbf8 -- tests/`, then filtered to `.py`, `__pycache__` excluded. Yields the lead's floor of 9 plus no additional live candidate:
- test_allomorph_create_morphtype.py, test_morph_type_utils.py, test_wfi_morph_bundle.py, phase3_lexicon_validation_tests.py, test_allomorph_wrappers.py, test_operations_baseline.py, test_prohibition_wrappers.py, test_wrappers.py -- all `.py` but **none carry `requires_live_project`** (grep -c returned 0 for each); read confirms mock/unit style. Excluded as non-live.
- Local-alias sweep `git grep -nE "\.Allomorphs\b" 09fcbf8 -- tests/` finds only the same 9 floor files (incl. `ops = target_sandbox.Allomorphs` in test_lexicon_brackets_live.py:451/464 and `allo_ops = writable_project.Allomorphs` in test_owner_cast_pattern.py:429/462) -- no file outside the floor uses the alias pattern.
- `tests/write_path_transactions/` and `flexicon/sync/tests/`: zero term hits. No allomorph-adjacent live tests there.

**Confirmed set = the 9-file floor, no additions, no exclusions below 9.**

## 2. Per-call-site coverage (method @ line -> covering live test)
| Site line | Method | Live coverage (file::test) |
|---|---|---|
| 345 | Delete | test_allomorphs_live.py::test_create_and_delete_roundtrip, ::test_movedown_then_moveup_restores_order, ::test_form_capture_modify_restore, ::test_delete_preexisting_alternate_in_sandbox; test_owner_cast_pattern.py::test_allomorph_delete_removes_from_alternate_forms |
| 422 | Duplicate | test_owner_cast_pattern.py::test_allomorph_duplicate_attaches_to_alternate_forms |
| 629 | GetForm | test_allomorphs_live.py::test_create_and_delete_roundtrip, ::test_form_capture_modify_restore; test_lexicon_brackets_live.py::TestAllomorphBrackets (both tests) |
| 678 | SetForm | test_allomorphs_live.py::test_form_capture_modify_restore; test_lexicon_brackets_live.py::TestAllomorphBrackets (both tests) |
| 746 | SetFormAudio | **none** |
| 850 | GetFormAudio | **none** |
| 907 | GetMorphType | **none** (all `.GetMorphType(` hits route through `WfiMorphBundles` or `LexEntry`, never `Allomorphs`) |
| 947 | SetMorphType | **none** (same -- `WfiMorphBundleOperations` only) |
| 989 | GetPhoneEnv | **none** |
| 1033 | AddPhoneEnv | **none** |
| 1075 | RemovePhoneEnv | **none** |

Counting method: static read + targeted grep per method name pinned at `git show 09fcbf8:<file>`, cross-checked against each variable's assignment (`ops =`/`allo_ops =`) to exclude same-named methods on other Operations classes (Etymology, Pronunciations, WfiMorphBundles, LexEntry). No `--collect-only` used -- no pytest invocation of any kind was run, per constraint. Repo-wide confirmation (not just the 9-file set): `git grep` for `SetFormAudio(`, `GetFormAudio(`, `GetPhoneEnv(`, `AddPhoneEnv(`, `RemovePhoneEnv(` across all of `tests/` returns **zero hits anywhere in the repository**, not just the candidate set.

test_feature_struc_resolver.py, test_issue251_252_256_feature_struct_probe.py, test_issue254_live_cycle2.py, test_issue254_morphra_probe.py, test_etymologies_live.py, test_pronunciations_live.py were read in full: their allomorph-adjacent hits are a bare `Allomorphs.Create` call (not one of the 11 sites), a string literal class-name probe (`"IMoAffixAllomorph"`), `WfiMorphBundles`-routed `GetMorphType`/`SetMorphType`, or a docstring reference to a future "Phase C." None reach any of the 11 sites.

## 3. Uncovered count
**7 of 11 sites have NO live coverage of any kind**: SetFormAudio (746), GetFormAudio (850), GetMorphType (907), SetMorphType (947), GetPhoneEnv (989), AddPhoneEnv (1033), RemovePhoneEnv (1075). 4 of 11 are covered: Delete (345), Duplicate (422), GetForm (629), SetForm (678). This is not a subset misreported as a superset -- both counts are exact and additive to 11.

## 4. HVO entry-path in test_allomorphs_live.py
**No HVO int path.** `git grep -niE "int\(|as_hvo|\.Hvo\b" 09fcbf8 -- tests/operations/test_allomorphs_live.py` and a full read of every `Allomorphs.*(` call in the file show every argument is the object returned by `.Create()` or `.GetAll()` (e.g. `allomorph`, `allo_a`, `victim`) -- never a bare int/Hvo. This file exercises the **object path only**; it is not a pre-existing live falsifier for prediction P4's HVO-path claim. No other file in the 9-file set passes a raw int to any `Allomorphs.*` call either (same local-alias/direct-call inventory above).
