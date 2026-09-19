# Live verification -- T4.7 (issue #259, checkpoint 4)

**Project:** Sena 3 | **Fixture:** sena3_sandbox (tempdir copy of the
.fwbackup -- the real Sena 3 was never opened; every write below targets
that sandbox copy only, discarded by pytest teardown after each test)

**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q -k TestPart8InflClassLive -s
```

**run_mode:** live (confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`
-> `live`)

**Date:** 2026-09-18

## IMPORTANT: scope drift discovered mid-verification

This dispatch's brief described SetInflectionClass as still BLOCKED
(raises AttributeError, per cycle-4/T4.4's finding, pending a domain
ruling on Q2) and asked item 5 to pin that AttributeError. While this
verification was in progress, the campaign progressed concurrently: a
domain ruling (C11, "warn") and a T4.5 implementation landed in the same
working tree, unblocking SetInflectionClass to write through to the
shared stem MSA and raise FP_ParameterError (not AttributeError) for a
null-MsaRA or non-stem-MSA bundle. The concurrent edit also modified the
SAME test file this task was asked to extend (evidence: git diff line
counts for tests/operations/test_lcm_member_truth_sweep.py grew from
674 to 680 to 732 insertions across the course of this single
verification session, and specs/lcm-member-truth-sweep/.crew-handoff.json
plus a new cycle5-domain.md appeared mid-task).

Per this agent's mandate (did this change actually do what it claims,
against a real FieldWorks database), item 5 below verifies the ACTUAL
CURRENT SetInflectionClass behaviour (T4.5's "warn" fix), not the stale
"stays BLOCKED" expectation from the original brief -- pinning a
requirement that the code has already moved past would not be a
meaningful verification. Flagging this drift explicitly for the lead:
another concurrent process modified this file while this task was open;
the two edits were reconciled (see "Additional live findings" below for
bugs surfaced by that reconciliation), and the final file compiles and
passes, but a filesystem-level coordination hazard occurred and should be
noted for the crew's process.

## Claim under test

Cycle 4 (T4.1/T4.2/T4.3/T4.6) routed
WfiMorphBundleOperations.GetInflectionClass /
GetSyncableProperties through a new
get_inflection_class_from_msa() helper (flexicon/code/lcm_casting.py),
and deleted three dead InflClassRA copy lines in
WfiMorphBundleOperations.Duplicate, WfiAnalysisOperations.Duplicate
(deep=True), and WordformOperations.Duplicate (deep=True), on the
theory that MsaRA is copied by reference so the inflection class rides
along for free. Cycle 4 shipped this offline-only, self-reported
FAIL: unverified. This is the live verification.

## Pre-state (read from LCM, Sena 3 sandbox)

- Total IWfiMorphBundle instances: 1932 (via
  IWfiMorphBundleRepository.AllInstances())
- Null MsaRA: 94
- Non-stem MSA (MoInflAffMsa/MoDerivAffMsa/MoUnclassifiedAffixMsa):
  1144 (1109/32/3)
- Stem MSA (MoStemMsa): 694, all 694 with InflectionClassRA is None
  today (T4.4 measurement 5; re-confirmed here)

## Action + post-state (re-queried from the LCM after each write)

### Item 1 -- loud path stops raising (test_8a)

Iterated all 1932 bundles through
project.WfiMorphBundles.GetInflectionClass(bundle). Zero exceptions.
None returned for all 94 null-MsaRA and all 1144 non-stem-MSA bundles
(each individually asserted). Non-None count: 0 (matches T4.4's
observation that stock Sena 3 has no positive data -- proves nothing
about the write-then-read path by itself, which is why item 3 plants a
real value).

```
[T4.7-1] total=1932 null_msa=94 non_stem=1144 stem=694 non_none=0 exceptions=0
```

### Item 2 -- silent drop stops dropping (test_8b)

Iterated all 1932 bundles through
project.WfiMorphBundles.GetSyncableProperties(bundle). Zero exceptions,
zero key-presence/GUID mismatches against an INDEPENDENT raw-LCM
computation (cast_to_concrete + direct .InflectionClassRA read, not the
production helper). "InflClassRA" key absent for all 1932 (no class set
anywhere pre-plant) -- structurally consistent with "absent iff no
class."

```
[T4.7-2] key_present=0 key_absent=1932 exceptions=0 mismatches=0
```

This required a monkeypatch workaround for an unrelated, pre-existing,
live-discovered defect -- see "Additional live findings" below.
Without the workaround, GetSyncableProperties raises AttributeError on
all 1932/1932 bundles, for a reason that has nothing to do with
InflClassRA.

### Item 3 -- THE TRAP: planted positive path (test_8c)

Planted a real IMoInflClass (TEST_T4.7_InflClass, hvo=152222) directly
on the stem MSA (hvo=116694) of bundle hvo=320, via raw LCM
(source_msa.InflectionClassRA = new_cls) -- NOT via SetInflectionClass.
Re-read the MSA fresh by HVO (IMoStemMsa(project.Object(116694))):
InflectionClassRA.Hvo == 152222 -- confirmed persisted. Re-read the
bundle fresh by HVO (IWfiMorphBundle(project.Object(320))) and called
GetInflectionClass: returned guid
10020aec-69bc-4d78-8535-0b7b1067df96, matching the planted class -- the
read path now surfaces a real positive value, not just None everywhere.

```
[T4.7-3] planted class hvo=152222 on msa hvo=116694; GetInflectionClass(bundle hvo=320) re-read guid=10020aec-69bc-4d78-8535-0b7b1067df96 -- MATCH
```

GetSyncableProperties on the same re-read bundle now returns
props["InflClassRA"] == "10020aec-69bc-4d78-8535-0b7b1067df96" -- the
key is present with the correct GUID once the class exists.

### Item 4 -- case-(a) deletion proof, all three Duplicate sites (test_8c)

Using the bundle/MSA planted in item 3:

- WfiMorphBundleOperations.Duplicate: dup bundle hvo=152223,
  duplicate.MsaRA.Hvo == 116694 (same MSA as source, by reference) and
  GetInflectionClass(duplicate) returns the SAME class guid
  (10020aec-...) as the source.
  ```
  [T4.7-4a] WfiMorphBundleOperations.Duplicate: dup bundle hvo=152223 MsaRA hvo=116694 (== source) infl class guid=10020aec-69bc-4d78-8535-0b7b1067df96 -- MATCH
  ```
- WfiAnalysisOperations.Duplicate(deep=True): dup analysis
  hvo=152224; 2 nested morph bundles in the duplicate referenced the same
  source MSA (hvo=116694; the source analysis already contained 2
  bundles pointing at it, including the item-4a duplicate from the same
  test run), both re-read GetInflectionClass matches.
  ```
  [T4.7-4b] WfiAnalysisOperations.Duplicate(deep=True): dup analysis hvo=152224, 2 nested bundle(s) matched source MSA, all carry the planted class -- MATCH
  ```
- WordformOperations.Duplicate(deep=True): dup wordform
  hvo=152228; 6 nested morph bundles (across all duplicated analyses)
  referenced the shared source MSA, all matched.
  ```
  [T4.7-4c] WordformOperations.Duplicate(deep=True): dup wordform hvo=152228, 6 nested bundle(s) matched source MSA across all duplicated analyses, all carry the planted class -- MATCH
  ```

All three sites covered end-to-end (none skipped).

### Item 5 -- SetInflectionClass (INVERTED from the brief -- see scope-drift note above)

The domain ruling (C11, "warn") landed T4.5 concurrently with this
verification: SetInflectionClass no longer raises AttributeError. It
now writes through to the shared stem MSA (mirroring
GetInflectionClass's navigation) and raises FP_ParameterError -- not
AttributeError, and not a silent no-op -- for a null-MsaRA or
non-stem-MSA bundle. Verified all three branches live:

- Positive path: planted a second class (hvo=152246) via
  SetInflectionClass(bundle, infl_class_hvo) itself (not raw LCM this
  time). Re-read the MSA fresh by HVO: InflectionClassRA.Hvo == 152246
  -- the write landed on the LCM, not just in-process state. Re-read
  GetInflectionClass(bundle) observed the same new value.
  ```
  [T4.7-5a] SetInflectionClass(bundle hvo=320, infl_class hvo=152246) succeeded; re-read MSA hvo=116694 InflectionClassRA hvo=152246 -- MATCH
  ```
- Null-MsaRA bundle (hvo=417): SetInflectionClass raised
  FP_ParameterError (not AttributeError).
  ```
  [T4.7-5b] SetInflectionClass(bundle hvo=417 [null MsaRA], infl_class) raised FP_ParameterError as expected
  ```
- Non-stem-MSA bundle (hvo=42, ClassName=MoInflAffMsa):
  SetInflectionClass raised FP_ParameterError; re-read the non-stem
  MSA's hvo afterward -- unchanged, no state change from the rejected
  write.
  ```
  [T4.7-5c] SetInflectionClass(bundle hvo=42 [ClassName=MoInflAffMsa], infl_class) raised FP_ParameterError as expected
  ```

The qualitative fan-out warning fires as specified (C11 point 3):
```
NOTE: inflection class is stored on the shared MSA, not the bundle; this change will be visible to every other morph bundle and sense referencing the same MSA.
```

### Item 6 -- regression

- python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q
  (FLEXLIBS_REQUIRE_LIVE=1): 23 passed (all Parts 1-8 of this file,
  including the pre-existing Part 1-7 reflection/read tests).
- python -m pytest tests/operations/test_issue254_live_cycle2.py -m requires_live_project -q
  (FLEXLIBS_REQUIRE_LIVE=1): 8 passed.
- Offline baseline, non-path-scoped exactly as instructed:
  python -m pytest -m "not requires_live_project" -q: 1878 passed,
  809 deselected, 0 failed -- matches the programmer's cycle-4 reported
  1878/0 exactly.

## Cleanup

All test_8c writes target sena3_sandbox (tempdir copy, discarded by
pytest fixture teardown regardless). Best-effort in-test cleanup was
still performed and confirmed via the passing run: both planted
IMoInflClass objects removed from pos.InflectionClassesOC, the
source MSA's InflectionClassRA cleared, and the three duplicate objects
(WfiMorphBundle, WfiAnalysis, WfiWordform) deleted, all inside
try/finally. The real Sena 3 project (tests/fixtures/Sena 3
2018-09-11 1145.fwbackup) was never opened.

## Additional live findings (out of scope for #259, flagging for a new issue)

1. GetSyncableProperties is broken for every WfiMorphBundle call,
   unconditionally, and unrelated to InflClassRA. Its very first
   line -- props["Form"] = self.project.GetMultiStringDict(item.Form)
   -- calls a method that does not exist anywhere on the real
   FLExProject class (confirmed: grep -n "def.*MultiString\|def.*Dict"
   flexicon/code/FLExProject.py returns nothing). Measured live:
   1932/1932 Sena 3 bundles raised
   AttributeError: 'FLExProject' object has no attribute
   'GetMultiStringDict' before ever reaching this cycle's InflClassRA
   line. The SAME dead call appears, unmodified, in at least 7 other
   Operations classes' GetSyncableProperties:
   flexicon/code/Shared/MediaOperations.py:489,
   flexicon/code/TextsWords/DiscourseOperations.py:1182,
   flexicon/code/TextsWords/SegmentOperations.py:1555,1558,
   flexicon/code/TextsWords/TextOperations.py:376,379,382,
   flexicon/code/TextsWords/WfiGlossOperations.py:286,
   flexicon/code/TextsWords/WordformOperations.py:932. It is only
   satisfied under a MagicMock (see
   tests/test_segment_baseline_text.py:203-204,
   ops.project.GetMultiStringDict.return_value = {}), which
   auto-vivifies missing attributes instead of raising -- a textbook
   example of the exact hazard CLAUDE.md's Live LCM Verification section
   exists to catch. This is not something T4.1-T4.6 introduced (the
   Form line is untouched by cycle 4's diff), but it means item 2 above
   could not be genuinely exercised without a monkeypatch workaround
   isolating the InflClassRA-specific claim from this unrelated crash.
   Recommend filing a new issue; this affects the syncable-properties
   surface across (at least) 8 Operations classes.

2. project.Object(hvo) returns a bare ICmObject; any
   derived-interface property access on it raises AttributeError
   without an explicit cast, and several WfiMorphBundleOperations
   methods that resolve bundle_or_hvo via __GetBundleObject inherit
   this when called with an int. Confirmed live: GetMSA(hvo)
   (untouched by this cycle) raises
   AttributeError: 'ICmObject' object has no attribute 'MsaRA', and the
   identical failure reproduces on GetInflectionClass(hvo) /
   SetInflectionClass(hvo, ...) for the same reason -- bundle.MsaRA
   is read after __GetBundleObject resolves an int via
   project.Object(), which returns the bare, gate-limited object.
   Every doc example in this file already avoids the failure by passing
   objects, never HVO ints, to these methods (e.g.
   morphBundleOps.Duplicate(bundles[0])) -- so the documented calling
   convention works, but the bundle_or_hvo signature's HVO half is
   silently broken for several methods. This is pre-existing
   (confirmed via the unmodified GetMSA), not introduced by cycle 4/5.
   The live test suite here (test_8c) was written to pass objects, not
   ints, to these methods to avoid the defect while still re-fetching by
   HVO + explicit interface cast wherever a genuine "did the write land"
   check was needed. Recommend filing a new issue on
   __GetBundleObject/ServiceLocator.GetObject()-based HVO resolution
   across the affected methods.

## Result

[PASS] -- live run against the Sena 3 sandbox, run_mode: live.
Items 1-4 and 6 pass exactly as specified. Item 5 passes against the
CURRENT (T4.5, cycle-5 "warn" ruling) SetInflectionClass behaviour,
which superseded the original brief's "stays BLOCKED" expectation while
this verification was in progress -- see the scope-drift note above.
Two unrelated, pre-existing, live-confirmed defects were discovered and
worked around/documented rather than silently absorbed: (1)
GetSyncableProperties's GetMultiStringDict call is broken everywhere,
in at least 8 files; (2) HVO-int resolution via
project.Object()/__GetBundleObject is broken for any
derived-interface property access, reproduced on the untouched GetMSA.
Neither blocks this cycle's InflClassRA claims once worked around, but
both warrant new issues.
