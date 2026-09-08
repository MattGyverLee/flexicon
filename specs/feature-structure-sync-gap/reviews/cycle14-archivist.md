# Cycle 14 -- Archivist audit of Checkpoint 4 (T7, #252)

**Role:** Independent auditor, a second pass after lex-verification's cycle-14
gate (`reviews/cycle14-verification.md`, `evidence/live-cycle14-gate.md`,
both PASS). This report does not read verdicts back from
`specs/feature-structure-sync-gap/STATUS.md` -- STATUS.md was consulted only
to learn what each condition says, never for its MET/NOT MET column. Every
row below rests on my own grep/read/offline-pytest run, or explicitly cites
the gate's live measurement where live execution was required and I am
forbidden from running it.

**Commits under audit:** production `4e9d152`, tests `4b746a0`, CHANGELOG
`3eff177`, report `c26a017`, pre-T7 parent `1d88aa4`.

**No live test was run by this audit.** Every offline command below used
`-m "not requires_live_project" -p no:cacheprovider`. `FLEXLIBS_REQUIRE_LIVE`
was never set by me.

## Provenance key
- FIRST-HAND = I ran the grep/pytest/git command myself and report the raw
  output.
- CITED (gate) = the check can only be settled live; I read the gate's
  evidence file and report its measurement, not my own.

## Checkpoint 4 closing conditions 1-8, 10

| # | Condition | Provenance | Verdict | Evidence |
|---|---|---|---|---|
| 1 | Routes through existing C5 helpers; no fifth FEATURE_STRUC_OWNER_TABLE copy | FIRST-HAND | MET | grep -rn FEATURE_STRUC_OWNER_TABLE flexicon/ (scoped to the package, not the untracked build/lib/flexicon/ copy): one definition, flexicon/code/Shared/lcm_constants.py:116; every other hit in BaseOperations.py, POSOperations.py, MSAOperations.py is a comment/docstring reference. Zero second tables. |
| 2 | Slot disambiguation: both slots explicit at every call site; ambiguous-without-slot raises | FIRST-HAND (source) + CITED (live raise) | MET | Read POSOperations.py lines 1150-1400: all four call sites (__CaptureFeatureStrucProp / __ApplyFeatureStrucProp x2 each) pass "Default" / "InherFeatVal" literally, never None. test_ambiguous_owner_without_slot_raises (live) asserts FP_ParameterError naming "PartOfSpeech" and "slot", then re-fetches a fresh IPartOfSpeech to confirm no partial attach -- read the source myself; its live pass/fail (and M4's kill of it) is the gate's measurement (live-cycle14-gate.md LEG 1, M4). |
| 3 | Zero hasattr on feature-struct properties, AST allowlist test targets the right functions | FIRST-HAND | MET | Read test_issue252_pos_feature_sync.py lines 173-227: test_get_syncable_properties_hasattr_calls_are_allowlisted caps GetSyncableProperties's hasattr to exactly Name/Abbreviation/Description/CatalogSourceId; test_zero_hasattr_in_apply_and_feature_helpers asserts zero hasattr in ApplySyncableProperties, _POSOperations__CaptureFeatureStrucProp, _POSOperations__ApplyFeatureStrucProp, _POSOperations__ResolveObject -- the exact five functions named in the dispatch. Ran offline myself: pytest tests/operations/test_issue252_pos_feature_sync.py -m "not requires_live_project" -> 20 passed, 6 deselected (includes both these tests). |
| 4 | C2 direct mutation-resistant cast test ships in the same task | FIRST-HAND (source+task) + CITED (live kill) | MET | TestPOSSyncLiveResolveObjectCast::test_hvo_path_casts_to_concrete_pos (test_issue252_pos_feature_sync.py lines 837-864) reads .DefaultFeaturesOA/.InherFeatValOA directly off the object returned by __ResolveObject, asserting the pre-cast bare object lacks the attribute first. Committed at 4b746a0, same task/date as production 4e9d152. Its live kill under M1 (AttributeError on DefaultFeaturesOA) is the gate's measurement (live-cycle14-gate.md LEG 1, M1). |
| 5 | Keys popped before super(); presence not truthiness; falsy-but-present value from the start; T6b residual disclosed unchanged | FIRST-HAND | MET (residual disclosed) | Read source: base_props filters out self.__FEATURE_STRUC_KEYS, then super().ApplySyncableProperties(...) runs after -- pop precedes the super call. __ApplyFeatureStrucProp gates "if key in props or guid_key in props" (presence, not "if value:"). Ran TestPOSSyncApplyPresenceGate offline myself: both test_falsy_but_present_* tests pass. The T6b-known residual (guid-only-truthy / neither-present survive M2 because truthy fixtures cannot separate presence from truthiness) is disclosed in the class docstrings in the same shape as T6b -- unchanged, not silently dropped. M2's kill/survival split itself is the gate's live-adjacent worktree measurement (live-cycle14-gate.md LEG 1, M2); I did not re-run the mutation myself, only confirmed the current (unmutated) offline suite is green and the disclosure text is present and matches T6b's wording. |
| 6 | Unresolvable GUIDs raise through the real on_unresolved, not an unconditional spy | FIRST-HAND (source) + CITED (live enforcement) | MET | TestPOSSyncApplyRaisePropagationThroughPublicSurface's own docstring self-labels "C7 raise-PROPAGATION coverage only -- NOT enforcement coverage"; its spy asserts the recorded call carried on_unresolved == "raise" (propagation only). Real enforcement is test_apply_raises_on_unresolved_feature_guid (live), which passes a bogus GUID with no spy and expects the real _ApplyFeatureStruc to raise. Source shows __ApplyFeatureStrucProp calls _ApplyFeatureStruc(..., on_unresolved="raise", ...) unconditionally, no branch anywhere. Live pass/fail and M3's kill are the gate's measurement (live-cycle14-gate.md LEG 1, M3). |
| 7 | Cycle-7 binding rider: multistring alts route through _apply_props_loop, no new {ws.Id: ws.Handle} map, line 1222 is the pre-existing capture map not a fourth resolution site, ratchet test green offline | FIRST-HAND | MET | git show 4e9d152 -- flexicon/code/Grammar/POSOperations.py, grepped for ws.Id / ws.Handle / dict.get: returns nothing -- the diff adds zero such lines. The only {ws.Id: ws.Handle ...} map in the file is at line 1222 (all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}), inside GetSyncableProperties, and confirmed NOT part of the diff (grepping the diff hunk itself for all_ws returns nothing) -- pre-existing, one of the 13 protected map-build sites, not a new resolution site. Ran pytest tests/operations/test_issue250_defect4_ws_resolution.py -m "not requires_live_project" myself: 21 passed. |
| 8 | Live evidence, run_mode: live, values re-read from the LCM via fresh re-fetch | CITED (gate) -- cannot run live myself | MET (per gate) | evidence/live-cycle14-gate.md LEG 4: FLEXLIBS_REQUIRE_LIVE=1 pytest tests/operations/test_issue252_pos_feature_sync.py -m requires_live_project -q -> 6 passed, 20 deselected, run_mode: live, uncategorized_live_tests: []. LEG 1's round-trip re-reads are confirmed via sandbox.Object(hvo) fresh fetches by reading the test source myself (lines 882-948: tgt_bare = sandbox.Object(tgt_pos.Hvo) after every write, never the held reference). I did not execute this myself; citing the gate's run_mode and pass count verbatim. |
| 10 | Comparator red set of 2 against 416/2/518 (moved baseline; 396/392 stale) | FIRST-HAND | MET | Ran myself: pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q -> 2 failed, 416 passed, 518 deselected at HEAD, red set exactly TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception plus test_depth_restored_on_exception (the pinned pre-existing foreign pair). Matches the gate's number exactly, not the stale 396/392. |

**Bookkeeping (non-blocking, not one of the ten):** __ResolveObject call
sites -- grepped myself: grep -n "self\.__ResolveObject(" flexicon/code/Grammar/POSOperations.py
returns 16 lines (273, 401, 439, 474, 511, 555, 617, 673, 674, 711, 751, 792,
841, 913, 1216, 1305), matching the gate's LEG 6 count exactly and
contradicting cycle13-programmer.md's "15".

## Provenance summary

- Re-derived FIRST-HAND by this audit (no reliance on the gate's own
  numbers, though several corroborate them): conditions 1, 3, 5 (source /
  offline half), 7, 10, plus the call-site bookkeeping count, plus G9 and
  G10 below.
- Re-derived from source but the pass/fail outcome cites the gate (the
  condition requires a live LCM to execute): conditions 2, 4, 6.
- Rests entirely on the gate's live measurement (I ran no live pytest at
  all, per the task's hard constraint): condition 8.

No condition came back NOT MET under my own re-derivation. No P0 was found
in this audit. One pre-existing P2 is corroborated (see G10) and the 16-vs-15
bookkeeping correction is corroborated independently.

## Task B -- prediction verdicts

### G9 -- Pyright diagnostics are pre-existing, not T7's

**HELD**, verified by diff region myself:

```
git show 4e9d152 -- flexicon/code/Grammar/POSOperations.py | grep "^@@"
@@ -1112,13 +1112,53 @@ ...
@@ -1126,11 +1166,28 @@ ...
@@ -1145,6 +1202,16 @@ ...
@@ -1172,20 +1239,166 @@ ...
```

All four hunks start at old-file line 1112 or later -- nothing below ~1100
(where the lines-206/208/241/372 diagnostics live) is touched by this
commit, so those diagnostics predate T7. Additionally confirmed the
super().ApplySyncableProperties call shape: POSOperations.py line 1314
reads super().ApplySyncableProperties(pos, base_props, ws_map,
fill_gaps=fill_gaps), argument-shape identical to MSAOperations.py line
1001's super().ApplySyncableProperties(msa, base_props, ws_map,
fill_gaps=fill_gaps) -- the same diagnostic shape T6 already carried
through a PASSED gate.

### G10 -- CompareTo side effect is real; CHANGELOG does not disclose it

**HELD**, verified myself:

```
git show 3eff177 -- CHANGELOG.md | grep -i "compareto\|struct.*guid"
(no output, exit code 1)
```

Read the full 3eff177 CHANGELOG diff: it documents the capture/apply fix
and the HVO-entry-path bug in detail, with zero mention of CompareTo or the
new key-plus-Guid struct-identity comparison side effect. Also confirmed
TestPOSSyncCompareToStructGuidPinning (test_issue252_pos_feature_sync.py
lines 770-816) is the only place this behaviour is pinned -- its own
docstring explicitly frames it as a documented behaviour change, not a
defect, with a candidate follow-up (compare spec content, not struct
identity) named but not filed. This corroborates the gate's G10
adjudication and its P2 finding.

## Conclusion

Independently re-derived, all nine source/git/offline-verifiable closing
conditions (1-7, 10) come back MET; condition 8, which requires live LCM
execution, is reported MET on the strength of the gate's own citation, not
mine. G9 and G10 both HELD under my own re-verification. No P0. The one
genuine P2 (CompareTo/CHANGELOG omission) and the 16-vs-15 bookkeeping
correction are both corroborated independently, not merely repeated from
the gate's report.

**Checkpoint 4's condition 9 (the independent verification gate) was
discharged by lex-verification's cycle-14 report, not by this audit** --
this document is a second, separately-sourced pass over the same closing
conditions, run after the gate token was released, and it reaches the same
PASS conclusion via independently-run commands.
