# Cycle 3 -- lex-verification report (issue #542)

**Verdict: PASS**

Worktree: C:\Github\flexicon-542, branch fix/542-affix-slot-readers,
commits c16e8d7, 2d80ff1, 48e394c, 32f73f6 (after e4f3259).
Binding directive honored: live writes only to Sena 3 sandbox copies;
target_project/target_sandbox not run; Target never opened
write-enabled.

## 1. Offline suite + contract test -- PASS

Command: python -m pytest -m "not requires_live_project" -q
Result: 4 failed, 2507 passed, 1041 deselected, 16 warnings in 11.04s

The 4 failures are exactly
tests/operations/test_morphrule_duplicate_deep.py::TestDuplicateDeepGating::
test_default_call_does_not_raise_nameerror,
test_deep_false_does_not_copy_slot_references,
test_deep_true_copies_slot_references,
test_deep_true_keyword_matches_docstring_example -- the pre-existing
set confirmed against origin/main last cycle. No other failures.

Command: python -m pytest tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies -q
Result: 1 passed in 0.47s -- PASS. This test now passes (was failing
before the snapshot regen).

## 2. Snapshot diff -- PASS

Command: git -C C:\Github\flexicon-542 diff e4f3259..HEAD --stat -- tests/contract/snapshots/
Result:
 tests/contract/snapshots/expected_contract.json | 28 +++++-
 tests/contract/snapshots/liblcm_baseline.json    | 123 ++++++++++++++++++++++++

Full diff reviewed. expected_contract.json: adds IMoInflAffixSlot to
the SIL.LCModel per-file import lists for affix_slot.py and
POSOperations.py, to the top-level type-usage list, and a new
code/Grammar/affix_slot.py file entry (imports IPartOfSpeech,
PartOfSpeechTags, ITsString); summary counts increment by exactly one
each (total_files_with_lcm_deps 81->82, total_unique_imports 269->270,
total_interfaces 112->113). liblcm_baseline.json: one new
IMoInflAffixSlot type entry (123 lines), alphabetically placed between
IMoInflAffMsaFactory and IMoInflAffixTemplate. No unrelated drift in
either file.

## 3. Live run (Sena 3, this branch own test file) -- PASS

Commands:
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q

Result: 5 passed in 9.61s

Command: python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"
Result: live

run_timestamp: 2026-09-26T23:18:27Z. Confirmed live, not mock.

## 4. Independent scratchpad script (Sena 3 sandbox copy) -- PASS

Script (not in the repo):
C:\Users\thoua\AppData\Local\Temp\claude\c--Github-flexicon\
22493013-83f0-4b23-88e5-7f8a1f9a8de8\scratchpad\verify542_scratchpad.py

Built its own tempdir sandbox by unzipping
tests/fixtures/Sena 3 2026-06-09 1645.fwbackup (same mechanism as the
sena3_sandbox fixture in tests/flex_plugin.py), replicated
flex_plugin.py session-scoped FieldWorks init (registry read, SIL
assembly load, FwRegistryHelper.Initialize(), FwUtils.InitializeIcu(),
FLExInitialize()) since it runs outside pytest, opened the sandbox
write-enabled, and:

- CreateAffixSlot returned type(slot) ==
  flexicon.code.Grammar.affix_slot.AffixSlot (not a raw
  IMoInflAffixSlot) -- PASS.
- Passed the wrapper directly into MorphRules.AddSlotToTemplate, then
  re-fetched the owning POS AffixTemplatesOS via a fresh
  IPartOfSpeech(project.Object(pos_hvo)) and read PrefixSlotsRS off
  the re-cast template -- slot_hvo 152223 present in the re-fetched set
  {152223} -- PASS (re-queried from the LCM, not the input value).
- Passed the wrapper directly into MSAOperations.SetInflAffMsaSlots,
  then re-queried via the independent inverse lookup
  MSAOperations.GetInflAffMsaSlots -- returned {152223}, matching the
  slot HVO -- PASS.
- Cross-checked POSOperations.GetAffixesInSlot(slot) against the same
  MSA HVO -- GetAffixesInSlot returned {152228} (the created MSA HVO),
  agreeing with the slot found via GetInflAffMsaSlots -- PASS.

All created objects (TEST_542_SCRATCH_pos, its slot, template, and lex
entry) deleted in a finally: block; project closed; tempdir sandbox
removed with shutil.rmtree. Output:

type(slot) = <class 'flexicon.code.Grammar.affix_slot.AffixSlot'>
[PASS] CreateAffixSlot returns AffixSlot wrapper
[PASS] AddSlotToTemplate: slot_hvo 152223 present in re-fetched PrefixSlotsRS {152223}
[PASS] SetInflAffMsaSlots + GetInflAffMsaSlots agree: {152223}
[PASS] GetAffixesInSlot(slot) == msa_hvo == {152228}
[PASS] GetAffixesInSlot and GetInflAffMsaSlots agree on the slot/msa relationship
ALL SCRATCHPAD CHECKS PASSED
Cleaned up created objects and closed project
Removed sandbox tempdir C:\Users\thoua\AppData\Local\Temp\scratchpad_542_sena3_4pbjb3c3

## 5. Grep checks -- PASS

- grep -rn "IMoInflAffixSlot(" --include=*.py . (excluding
  tests/contract/snapshots): every hit is a cast of a raw LCM object
  obtained directly from an LCM collection/project.Object(hvo)
  (POSOperations.py:1523 inside the resolver itself; the live test
  files IMoInflAffixSlot(item) calls operate on raw objects pulled
  from fresh.SlotsRC or similar enumerations, or on item.lcm_object /
  second.lcm_object -- already unwrapped). No caller casts the
  CreateAffixSlot return value directly.
- grep -rn "isinstance(.*IMoInflAffixSlot" --include=*.py . -- no
  matches (no bare isinstance-against-raw-interface check).
- python -m pytest tests/test_flexlibs2_alias_ratchet.py -q -> 5
  passed -- no new flexlibs2 references.
- git diff e4f3259..HEAD | grep -n "target_project" -- every hit is in
  prose (evidence/review markdown describing the binding directive or
  cycle-1 history), not in test code. No live test file in the diff
  itself references target_project. (test_issue258_set_infl_aff_msa_
  slots_live.py uses target_sandbox but is untouched by this diff and
  was not run this cycle, consistent with the directive.)

## 6. Migration guide / CHANGELOG accuracy -- PASS

docs/MIGRATION_GUIDE.md "Change: AffixSlot wrapper (issue #542)"
section states the unwrap attribute is slot.lcm_object. Confirmed
against flexicon/code/Shared/wrapper_base.py: LCMObjectWrapper
defines a public lcm_object property (line 229) returning self._obj,
matching the doc claim and its explicit "not _obj" caveat. CHANGELOG
[Unreleased] #542 entry accurately describes CreateAffixSlot new
AffixSlot wrapper return and GetAffixesInSlot inverse relationship
to GetInflAffMsaSlots (#543).

## 7. Commit message hazard check -- PASS

git log e4f3259..HEAD --format="%H %s"
32f73f6 test: live-verify #542 contract fix and CreateAffixSlot wrapper return
48e394c docs: migration note for CreateAffixSlot AffixSlot return (#542)
2d80ff1 feat(grammar): CreateAffixSlot returns an AffixSlot wrapper (#542)
c16e8d7 test(contract): regenerate LCM snapshot for IMoInflAffixSlot (#542)

git log e4f3259..HEAD --format="%B" | grep -inE "close|fix(es)? #|resolve"
returned one line, from a commit body describing a resolver mechanism --
not adjacent to #542, not a hazard. No subject or body uses
close/fix/resolve directly before an issue number.

## Overall

All 7 items PASS. Live verification reached a real LCM (run_mode:
"live") via both the branch own live test file and an independent,
out-of-repo scratchpad script against a freshly-built Sena 3 sandbox
copy, with every claim re-queried from the LCM after the write and full
cleanup confirmed. No writes to Target at any point.

Recommendation: APPROVE.
