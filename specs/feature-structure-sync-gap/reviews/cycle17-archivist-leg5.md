# Cycle-17 Checkpoint 5 gate -- Archivist LEG 5 (static half, task A)

HEAD at gate time: 8691c65 (predictions commit, parent e7f1048).

## LEG 5 -- evidence durability (condition 8)

### (a) live-T8.md: key-level quote, NOT a verbatim JSON block [PASS as PARTIAL predicted]
live-T8.md:17: "1 passed. `tests/live_status.json` -> `\"run_mode\": \"live\"`."
live-T8.md:60-63: "Result: `6 passed, 21 deselected`. `tests/live_status.json` ->
`\"run_mode\": \"live\"`, `\"run_timestamp\": \"2026-09-08T04:08:50Z\"`,
`\"uncategorized_live_tests\": []` (all 6 carry an explicit
`live_phase(\"AllomorphOperations\", \"modify\")` marker)."
No fenced `{...}` block copy of live_status.json appears anywhere in the
file. These are inline key:value quotes, not a verbatim dump. G5's PARTIAL
branch is confirmed, not the clean-PASS branch.

### (b) in-cycle-ness proven from git, not prose [PASS]
`git log --oneline -- specs/feature-structure-sync-gap/evidence/live-T8.md`
returns exactly one commit: `bd98c6b docs(feature-structure-sync-gap):
cycle-16 T8 live evidence + mutation testing`. Matches the predicted SHA
exactly; the run_mode/timestamp quote was committed in cycle 16, not
manufactured later. tests/live_status.json itself was not consulted for
this sub-item (correctly -- it is a one-run scratch artifact).

### (c) fresh re-fetch, not assertion-on-write-value [PASS]
`test_ms_env_features_capture_apply_roundtrip`
(tests/operations/test_t8_allomorph_feature_sync.py:894-930):
line 917 `src_bare = sandbox.Object(src_allo.Hvo)` (fresh fetch before
first read), line 923 `ApplySyncableProperties(tgt_allo, props)` (the
write), line 925 `tgt_bare = sandbox.Object(tgt_allo.Hvo)` (FRESH re-fetch
of the target AFTER the write), line 926-927 assertion is on
`GetSyncableProperties(tgt_bare)`, not on `props` (the value just written).
This matches evidence/live-T8.md:69-73 verbatim in substance.
`test_hvo_path_casts_to_concrete_affix_allomorph` (:866-881) similarly
re-resolves via `hvo` (a plain int) rather than reusing the `allo`
reference held at creation. All four requires_live_project classes
(TestT8LiveHasattrTrap:818, TestT8LiveDirectCast:855,
TestT8LiveRoundTrip:884, TestT8LiveStemAllomorphNoFeatureKeys:981)
confirmed present at those line numbers.

### (d) cf2fdfe provenance -- PARTIAL, count discrepancy found
`git log --oneline 09fcbf8..e7f1048` returns 8 commits, not six:
e7f1048, fdd8694, 6484d81, 191556f, bd98c6b, 016a97a, df37e35, cf2fdfe.
`--reverse` confirms cf2fdfe IS chronologically first (df37e35, 016a97a,
bd98c6b, 191556f, 6484d81, fdd8694, e7f1048 follow, in that order) --
that half of (d) HOLDS. But the prompt's premise "the six T8 commits" is
factually wrong; the range holds 8 T8-related commits. This is a minor
prose-accuracy defect in the gate prompt, not a defect in the evidence
chain itself -- flagging per instruction not to take anyone's word for it.

## LEG 4 static arithmetic (no pytest run)
`git show --numstat 016a97a` -> single file, `1007  0
tests/operations/test_t8_allomorph_feature_sync.py`, all-new (1007
insertions, 0 deletions -- the whole file was added in this commit).
Grep count of `    def test_` in that file at HEAD: 27 total. Of those,
6 fall within the Section D live classes (lines 818-1008, all under
`@pytest.mark.requires_live_project`); 27 - 6 = 21 offline tests. This
matches the commit message's own claim ("21 offline tests pass locally
(6 live deselected)") and independently reproduces the predicted split:
416 + 21 = 437 [OK], 518 + 6 = 524 [OK]. G4's arithmetic premise is
internally consistent; group 2's own new offline tests should move
`passed` by exactly their own count with `failed` unchanged at 2, per the
prediction file's falsifier.

## G5 adjudication: HELD (PASS-WITH-QUALIFIER, not clean PASS)
Sub-items (a)-(c) all confirm the lead's PARTIAL characterization exactly:
key-level quotes, correctly in-cycle, genuine fresh re-fetch semantics.
G5's two-sided falsifier is NOT triggered in either direction (no full
verbatim JSON block exists; run_mode/timestamp ARE quoted and ARE from
cycle 16). Condition 8 is met in substance, not in the literal
"verbatim" sense -- PASS-WITH-QUALIFIER stands as predicted.

## P0/P1
No P0. One P1 (documentation-accuracy, not code/evidence): the cycle-17
gate prompt's claim of "six T8 commits" in range 09fcbf8..e7f1048 is
wrong -- actual count is 8. Does not affect any prediction's truth value
and does not reopen Checkpoint 5; noted for the record only.
