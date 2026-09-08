# Cycle 14 -- Independent Verification Gate on T7 (#252), Checkpoint 4

## 1. VERDICT

**PASS.** Checkpoint 4 CAN CLOSE -- condition 9 (this independent gate)
is now MET. All nine other closing conditions independently re-derived
to MET (see section on G8 below). No P0 was found. One genuine P2
(CompareTo/CHANGELOG omission, disclosed but undocumented) and one
non-blocking bookkeeping correction (call-site count is 16, not 15) are
recorded.

Full run details, exact commands and verbatim outputs are in
specs/feature-structure-sync-gap/evidence/live-cycle14-gate.md --
this report summarizes and adjudicates.

Live token was held exclusively by this gate throughout. Every mutation
ran in its own disposable git worktree; the shared working tree was never
mutated (git diff --stat empty at the end, only pre-existing foreign
noise items remain untracked/modified).

## 2. G1-G10 adjudication table

| # | Prediction | Adjudication | Measurement |
|---|---|---|---|
| G1 | M1's asymmetric split reproduces exactly (BLOCKING) | HELD | Fresh worktree re-run: 3 failed (offline cast-shape lock, direct-cast test, HVO-entry-Name test), 4 relevant survivors (both feature-struct round trips, C7-raise, slot-ambiguity). Central falsifier (either round trip dying) did NOT fire. |
| G2 | M2-M5 each reproduce their reported kills/survivals (BLOCKING) | HELD | M2: 3 offline kills, 2 disclosed survivors unchanged. M3: offline propagation test + live C7-raise both killed. M4: live slot-ambiguity killed, nothing else moves. M5: 3 offline + 1 live (InherFeatVal) killed, Default round trip survives. All exactly as reported. |
| G2a | M4's disclosed co-kill on T14a test 3 is REAL | HELD | Ran (not reasoned): test_ambiguous_owner_without_slot_raises_through_makefeatstruc FAILED under the same M4 mutation. |
| G3 | P2 live-half set is non-empty, delta is ZERO (BLOCKING) | HELD | Own enumeration: 16 files / 81 node-ids (a superset of the 12-file floor list). Ran at 1d88aa4 and at HEAD (=c26a017 for every file in the set): 89 passed / 1 skipped on BOTH sides, byte-identical per-file pattern. Zero flips. |
| G3a | Any flip's direction is diagnostic (RED->GREEN predicted; GREEN->RED is a P0) | not-applicable | No flip occurred (G3's zero-delta result), so there is no direction to adjudicate. The P0 falsifier condition did not fire. |
| G4 | The "15 call sites" figure is wrong by one (non-blocking) | HELD | grep finds 16 (14 pre-existing at lines 273,401,439,474,511,555,617,673,674,711,751,792,841,913 + 2 new at 1216,1305), exactly matching the dispatch's own pre-committed line list. |
| G5 | P1 re-derives at 1d88aa4 in tracked form (0/4, then 4/4 at c26a017) | HELD | Tracked probe (git-added+committed in each disposable worktree) against the SAME Sena-3 hvo=42183: literal {} at 1d88aa4, all four keys at c26a017. |
| G6 | Comparator lands on the new baseline (2/416/518) | HELD | Confirmed at HEAD: 2 failed/416 passed/518 deselected. Delta vs 1d88aa4 in the same shell: +20 passed/+6 deselected/failed unchanged at 2, same red set both sides. |
| G7 | The live T7 file re-runs clean as committed | HELD | 6 passed/20 deselected, run_mode: live, uncategorized_live_tests: [] (no D4-T7 telemetry defect recurrence). |
| G8 | Closing conditions 1-8,10 independently re-derive to MET (BLOCKING) | HELD | See section 5 below; all nine re-derived to MET from source/git/tests, not read back from STATUS.md. |
| G9 | Pyright diagnostics are pre-existing, not T7's | HELD | Diff's four hunks all start at old-line >=1112 (nothing below ~1100 touched); the super().ApplySyncableProperties diagnostic shape at POSOperations.py:1314 is identical to the pre-existing one at MSAOperations.py:1000 (already carried through a PASSED T6 gate). |
| G10 | CompareTo side effect is real; CHANGELOG does NOT disclose it | HELD | grep of the 3eff177 CHANGELOG diff for "compareto"/"struct.*guid" returns nothing. Recorded as a genuine P2. |

## 3. Full mutation table (fresh worktree wt-4b746a0 at 4b746a0)

| # | Mutation | Killed | Survived | Restore hash verified |
|---|---|---|---|---|
| M1 | __ResolveObject cast removed | offline cast-shape test; live: direct-cast test, HVO-entry-Name test | live: both slot round-trips, C7-raise, slot-ambiguity | f94b4d97efb54ac9f78a1a1c5b3a034303bac951 |
| M2 | presence gate -> truthiness (__ApplyFeatureStrucProp) | offline: source-shape lock + both falsy-but-present tests | offline: guid-only-truthy, neither-present (T6b-known truthy-fixture residual) | f94b4d97efb54ac9f78a1a1c5b3a034303bac951 |
| M3 | on_unresolved raise->skip | offline propagation test; live C7-raise test | -- | f94b4d97efb54ac9f78a1a1c5b3a034303bac951 |
| M4 | ambiguous-no-slot picks rows[0] (BaseOperations.py) | live POS slot-ambiguity test; T14a test 3 (LEG 1a, G2a) | -- | a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db |
| M5 | InherFeatVal calls forced to slot="Default" | offline both-slots tests; live InherFeatVal round-trip | live Default round-trip (mis-routing invisible to it) | f94b4d97efb54ac9f78a1a1c5b3a034303bac951 |

All five re-run from scratch in ONE disposable worktree (git worktree add
<tmpdir> 4b746a0), Target .fwbackup copied read-only. Each mutation
reverted and git hash-object re-verified before the next. Final clean
check after all five restores: 26 passed (20 offline + 6 live),
run_mode: live. Worktree removed via git worktree remove --force;
git worktree prune -v silent.

Note: M4's first mutation attempt was FUNCTIONALLY WRONG (the for/else
raise still fired on an empty-iterable fallthrough) and was caught and
corrected before any kill/survival measurement was taken -- recorded here
for transparency, not hidden.

## 4. LEG 2's enumerated live set and both-sides results (verbatim summary)

Own enumeration (git grep + AST pass, transitively following helpers
_first_pos/_locate_pos_hvo and fixtures): 16 files, 81 node-ids -- a
STRICT SUPERSET of the 12-file main-session floor list. Additional files
my enumeration found that the floor list did not: test_abort_session_live.py,
test_apply_feature_struc.py, test_issue251_msa_feature_sync.py,
test_makefeatstruc_c3_live.py, test_segment_analysis_traversal.py. My
enumeration also correctly EXCLUDES test_natural_classes.py, whose only
"POS" hit is prose inside a docstring, not code that touches
project.POS/POSOperations -- confirmed by reading the surrounding source.
Full node-id list is in evidence/live-cycle14-gate.md LEG 2(a).

BEFORE (worktree at 1d88aa4): 89 passed, 1 skipped, run_mode: live.
AFTER  (HEAD 5efebb6, = c26a017 for every file in the set): 89 passed,
1 skipped, run_mode: live. Per-file dot-pattern diffed byte-identical.
The single skip (test_d4c_separator_divergent_resolves, a data-dependent
LOUD SKIP unrelated to POS) is identical on both sides.

ZERO FLIPS. G3/G3a HELD; P2's live half is now genuinely closed (it was
the cycle's one real residual per the dispatch).

Risk note: six of the sixteen files (test_set_pos_msa_dispatch.py,
test_msa_kind_and_change_variant.py, test_pos_catalog.py,
test_owner_cast_pattern.py, test_lexsense_operations.py,
test_segment_analysis_traversal.py) open a REAL, in-place, named FieldWorks
project directly (their own pre-existing writable_project/live_project
fixtures -- "Sena 3" in practice), not a sandbox copy. This is pre-existing
test-suite design, not something introduced by this gate; every test that
writes cleans up its own TEST_/qZ_-prefixed object in a finally: block, and
both runs (before/after) produced the identical pass/skip pattern, which is
itself evidence no residue accumulated between the two runs.

## 5. P0/P1/P2 findings

**P0: NONE FOUND.** G1's central falsifier (a feature-struct round trip
dying under M1) did not fire; G3a's GREEN->RED flip falsifier did not
fire (zero flips at all).

**P1: NONE FOUND** beyond what T7 already fixed and cycle 13 already
disclosed (the HVO-entry-path silent-drop bug, now closed and re-verified
independently in LEG 3).

**P2 findings:**
1. **CompareTo/CHANGELOG omission (flexicon/code/Grammar/POSOperations.py,
   CompareTo method; CHANGELOG.md, commit 3eff177).** T7's
   GetSyncableProperties now emits DefaultFeaturesGuid/InherFeatValGuid
   key-pairs, which changes CompareTo's observable behaviour for any
   caller comparing two POS with identical feature specs but
   independently-created structs (previously invisible, now reported as
   a difference on the "<key>Guid" key). This is disclosed in
   reviews/cycle13-programmer.md section 6 and pinned by
   TestPOSSyncCompareToStructGuidPinning, but the 3eff177 CHANGELOG entry
   does not mention it at all -- a caller reading "closes #252" from the
   CHANGELOG would not discover this behaviour change. Recommend the #252
   closure comment name it explicitly.
2. **Bookkeeping: __ResolveObject has 16 call sites, not 15**
   (flexicon/code/Grammar/POSOperations.py lines 273, 401, 439, 474, 511,
   555, 617, 673, 674, 711, 751, 792, 841, 913, 1216, 1305).
   reviews/cycle13-programmer.md section 5 and
   .crew-handoff.json's checkpoint_4.residual_named both say 15. This is
   the denominator for the risk P2's live half (LEG 2) exists to bound,
   and it is now correctly measured AND bounded (LEG 2 covered a live
   test set that reaches many, though not exhaustively every one, of
   these 16 sites -- no flip was observed on any of them).

## 6. Worktree / tree-cleanliness confirmation

Worktrees created and removed during this gate (all via
git worktree add <tmpdir> <commit>, disposed via
git worktree remove --force + git worktree prune -v after each leg):
wt-4b746a0 (4b746a0, LEG 1/1a/LEG4), wt-1d88aa4 (1d88aa4, LEG 2),
wt-1d88aa4-leg3 and wt-1d88aa4-leg3b (1d88aa4, LEG 3),
wt-c26a017-leg3 (c26a017, LEG 3), wt-1d88aa4-leg5 (1d88aa4, LEG 5).

Final state, checked after all legs:
```
git worktree list        -> D:/Github/_Projects/_LEX/flexicon  5efebb6 [main]  (only the main worktree)
git worktree prune -v     -> (silent)
git status --porcelain    -> D .claude/ralph-loop.local.md
                             ?? .vscode/
                             ?? specs/243-closeproject-save-guard/.spec-context.json
                             ?? specs/duplicate-signature-harmonisation/
                             ?? specs/getall-contract-flexicon/.spec-context.json
```
These are the five pre-existing foreign noise items named in the
dispatch -- none staged, none touched by this gate. git diff --stat
shows only .claude/ralph-loop.local.md (pre-existing deletion, not ours).
No file under flexicon/ or tests/ (outside the disposed worktrees) was
modified in the shared tree at any point during this gate.

## 7. Recommendation

**APPROVE.** Checkpoint 4's condition 9 (independent verification gate)
is MET. All ten closing conditions are now MET (nine re-derived
independently, the tenth discharged by this report). Recommend the #252
closure draft additionally name the CompareTo struct-GUID behaviour
change explicitly (P2 finding above) before posting.
