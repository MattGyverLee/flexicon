# Live verification -- cycle 5, T5 (MakeFeatStruc generalization, closes #256)

**Project:** Target (presence/lock check only) + Sena 3 (in-place, via shipped
writable_project fixture) + Target-backed target_sandbox/sena3_sandbox
(tempdir copies, used by most of the pinned live subset)
**Fixture:** mix -- writable_project (in-place Sena 3), target_sandbox,
sena3_sandbox, per the shipped test files' own design
**Command (PRIMARY):**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_phon_features.py tests/operations/test_phonemes.py \
  tests/operations/test_natural_classes.py tests/operations/test_natural_class_feature_sync.py \
  tests/operations/test_feature_struc_resolver.py tests/operations/test_apply_feature_struc.py \
  tests/operations/test_issue251_252_256_feature_struct_probe.py -m requires_live_project -q
```
**run_mode:** live (confirmed via tests/live_status.json on every run, both sides)
**Date:** 2026-09-07

## Setup: independent worktrees (not the shared, moving main checkout)

Other crews commit to main continuously during this session (HEAD moved
three times while this verification was in progress: 7409ad6 -> eab8ca7 ->
8980286, none of it mine). To get a stable A/B comparison I used disposable
git worktrees instead of stashing/checking out in the shared working tree:

- ../flexicon-t5-parent = 7bc6d01c568290c3119d8212f7a436b0feef4fce
  (T5's TRUE PARENT, re-derived via git log -1 --format=%P 6643b483, NOT
  assumed as HEAD~1 and NOT trusted from the report)
- ../flexicon-t5-head = 6643b4835b941a2a87b6cd74ec899f48c4fe3d0f (T5 itself)

tests/fixtures/*.fwbackup are untracked dev files; copied into both
worktrees from the main checkout before running (not a code difference).
Both worktrees removed (git worktree remove --force) after verification;
confirmed via git worktree list and git status --porcelain on the main
checkout that nothing of mine was left behind.

## Claim under test
T5 generalizes MakeFeatStruc into one BaseOperations._MakeFeatStruc,
routes owner resolution through the C1 table instead of the dead
hasattr(owner, "FeaturesOA") gate, and closes #256 (MSA owners can now
build a feature structure; nested/recursive-dict specs are expressible).

## 0. Concurrency-collision check (independent)
Command: git show --name-only --format= 6643b483
Result:
  flexicon/code/BaseOperations.py
  flexicon/code/Grammar/InflectionFeatureOperations.py
  flexicon/code/Grammar/PhonFeatureOperations.py
  specs/feature-structure-sync-gap/evidence/live-T5.md
  specs/feature-structure-sync-gap/reviews/cycle5-programmer-T5.md

All five are T5's own work. No file under the other crew's fence
(TextsWords/{Paragraph,Segment,Discourse}Operations.py,
specs/name-field-whitespace-identity/, specs/242-paragraph-whitespace/,
specs/tier1-silent-data-loss/, the two whitespace-probe test files) is
present. No index-collision residue landed in this commit.

## 1. PRIMARY -- live subset, both sides, same shell (worktrees)

| Side | Result | run_mode |
|---|---|---|
| Parent 7bc6d01c | 1 failed, 77 passed, 1 skipped, 27 deselected | live |
| Head 6643b483 (T5) | 1 failed, 77 passed, 1 skipped, 27 deselected | live |

Identical counts. The one failure on both sides is the documented
known-foreign test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target
(NaturalClassOperations.py:1270, pre-existing C2/HVO-cast symptom, T10's
territory). No other status changed.

### #256 probe flip -- printed evidence (assertion-free by design; pytest status is unchanged pass on both sides)

test_issue251_252_256_feature_struct_probe.py::test_item7_reproduce_256_makefeatstruc_on_msa_owner -s:

- Parent: [ITEM 7] MakeFeatStruc([], owner=stem) result: FP_ParameterError: owner has no FeaturesOA property; cannot attach FsFeatStruc.
- Head (T5): [ITEM 7] MakeFeatStruc([], owner=stem) result: NO EXCEPTION -- returned <SIL.LCModel.IFsFeatStruc object at 0x...>

Flip confirmed exactly as predicted.

## 2. SECONDARY -- pinned offline subset, delta only

Command: python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider

| Side | Result |
|---|---|
| Parent | 2 failed, 350 passed, 489 deselected |
| Head (T5) | 2 failed, 350 passed, 489 deselected |

Delta: 0. Both failures are the documented known-foreign
test_transaction_rollback.py::TestPhase2JoinOrOpen tests (rollback flag,
depth restored). No third or fourth failure.

## 3. DETERMINISM CHECK

At head worktree, same command run three times: twice in the same shell,
once in a fresh shell (separate tool invocation, cwd/env reset).

All three: 2 failed, 350 passed, 489 deselected. Comparator valid.

## 4. FALSIFIABILITY -- mutation test (mandatory)

Backup taken first: copied BaseOperations.py to scratchpad before mutating.
Pre-mutation blob hash: git rev-parse HEAD:flexicon/code/BaseOperations.py
= a32d94151fee1c3c62ccc33e71f3253990b0181a (matches the hash the
programmer's own report quotes -- confirms we are mutating the actual
committed file, not a stale copy).

Mutation: inserted, immediately after the _ResolveFeatureStrucOwner call
inside _MakeFeatStruc (BaseOperations.py:2527-2529):
  prop_name = "MUTATION_TEST_BOGUS_PROP"
This defeats the owner-resolution fix specifically (forces every owner's
struct to attach to a property that does not exist on any real LCM type),
without touching _ResolveFeatureStrucOwner itself.

Result: live subset went from 1 failed to 8 failed, 70 passed, 1 skipped,
27 deselected -- 7 NEW real failures:
  test_phon_features.py::TestPhonFeatureOperations::test_make_featstruc_owned
  test_phonemes.py::TestPhonemeSync::test_getsyncable_surfaces_feature_specs
  test_natural_classes.py::TestNaturalClassFeatureBased::test_create_feature_based_with_specs_populates_featuresoa
  test_natural_classes.py::TestNaturalClassFeatureBased::test_get_features_returns_featstruc_when_set
  test_natural_classes.py::TestNaturalClassFeatureBased::test_set_features_replaces_existing
  test_natural_classes.py::TestNaturalClassDuplicateDispatch::test_duplicate_features_returns_features_clone
  test_natural_classes.py::TestNaturalClassSync::test_getsyncable_surfaces_feature_specs
plus the 1 pre-existing known-foreign failure. Confirmed RED for real
reasons, not incidental breakage.

Restore: copied the pre-mutation backup back over BaseOperations.py
(never git checkout). git hash-object flexicon/code/BaseOperations.py
= a32d94151fee1c3c62ccc33e71f3253990b0181a, matching
git rev-parse HEAD:flexicon/code/BaseOperations.py exactly. Byte-identical
restore confirmed. git status --porcelain in the worktree showed no diff
after restore.

Clean re-run after restore (first attempt): 10 failed, 68 passed -- WORSE
than the pre-mutation baseline of 1 failed, despite the code being
byte-identical to HEAD. Root cause (disclosed, matches the programmer's
own account in section 5 of their report): test_phon_features.py,
test_phonemes.py, and test_natural_classes.py's writable_project fixture
opens the real, shared, in-place Sena 3 project by name (candidate list is
Sena 3, Test, SampleLexicon, SampleLexicon3) -- not a sandbox -- so the
mutation run's broken writes left transient residue in the one real Sena 3
project shared by every worktree on this machine.

Remedy: ran python scripts/restore_sena3.py (restored from
tests/fixtures/Sena 3 2018-09-11 1145.fwbackup), then re-ran the live
subset clean:
  1 failed, 77 passed, 1 skipped, 27 deselected, run_mode: live
Matches the pre-mutation baseline exactly. The real Target project was
never opened by any of these test files (candidate list never includes
Target; target_sandbox/sena3_sandbox are per-test tempdir copies).
python scripts/restore_target.py --check confirmed Target present and
unlocked both before and after this entire verification.

## 5. CONTRACT C3 -- independent structural + live-behavioural check

- Exactly ONE _MakeFeatStruc/MakeFeatStruc implementation under tracked
  flexicon/: BaseOperations.py:2387 (real body),
  InflectionFeatureOperations.py:970 and PhonFeatureOperations.py:553
  (1-line call-throughs). The only other hits are inside the untracked,
  gitignored build/lib/ duplicate tree (git check-ignore -v build shows
  .gitignore line 12: build/), correctly excluded per instructions.
- Both spec shapes verified live, end-to-end, by a NEW probe I wrote
  (tests/operations/test_verify_t5_c3_gate.py, run against target_sandbox,
  not committed -- disposable, in the now-removed flexicon-t5-head
  worktree only):
  - Recursive dict {agreement_feat.Hvo: {number_feat.Hvo: sg_val.Hvo}}
    passed to InflectionFeatures.MakeFeatStruc(specs, owner=bare MoStemMsa
    ICmObject) against a live target_sandbox MoStemMsa. Re-fetched via a
    FRESH IMoStemMsa(sandbox.Object(stem_hvo)).MsFeaturesOA (never the
    original reference): top-level spec's FeatureRA.Name equals
    TEST_c3_agreement; its IFsComplexValue.ValueOA, cast to IFsFeatStruc,
    has one nested spec whose FeatureRA.Name equals TEST_c3_number and
    IFsClosedValue.ValueRA.Name equals TEST_c3_sg. PASS.
  - Legacy flat list already covered live by the shipped suite
    (test_phonemes.py line 672, test_phon_features.py line 501, both
    green, section 1).
  - slot= disambiguation exercised THROUGH MakeFeatStruc itself, not just
    _ResolveFeatureStrucOwner: created one live MoDerivAffMsa, called
    MakeFeatStruc with slot="From" then, against a FRESH
    sandbox.Object(deriv_hvo), MakeFeatStruc with slot="To". Re-fetched
    IMoDerivAffMsa(sandbox.Object(deriv_hvo)): FromMsFeaturesOA.Hvo does
    not equal ToMsFeaturesOA.Hvo, From's closed value equals
    TEST_c3slot_sg, To's closed value equals TEST_c3slot_pl. Two
    independent owning properties on the SAME owner, correctly
    disambiguated. PASS.
  - owner=None still raises FP_ParameterError unconditionally --
    confirmed live via the two shipped tests
    (test_make_featstruc_rejects_owner_none,
    test_make_featstruc_unowned_requires_empty_specs), both green in
    section 1's run.

Output of the two new probe tests:
  [C3-NESTED] MakeFeatStruc(recursive dict, owner=MoStemMsa) round-tripped: top=TEST_c3_agreement -> nested=TEST_c3_number=TEST_c3_sg
  2 passed, 30 warnings in 3.98s

## 6. ANTI-REGRESSION

- No hasattr(owner, "FeaturesOA") gate remains inside _MakeFeatStruc or
  its private helpers -- the only matches for that string inside
  BaseOperations.py are docstring/comment prose describing the REMOVED
  pre-T5 pattern (grep -n for the pattern across flexicon/, confirmed by
  reading each hit).
- No blanket cast introduced: _ResolveFeatureStrucOwner (T2, unchanged by
  T5) casts via a ClassName-keyed concrete interface lookup per C1, not a
  universal cast.
- InflectionFeatureOperations.py line 493 still carries its own
  hasattr(parent, "FeaturesOA") gate -- confirmed still present, correctly
  OUT OF SCOPE (that is T11's territory per spec.md, needs T1+T2 and is
  listed as a separate task; T5 did not touch this line).

## 7. Callers, test files, conftest.py

- All 5 production call sites confirmed present, unedited, at the exact
  claimed lines: NaturalClassOperations.py 463, 867, 1034,
  PhonemeOperations.py 1886, PhonFeatureOperations.py 106 (docstring
  example).
- All 4 test files pass live (section 1's numbers).
- tests/conftest.py: diff between the parent and head worktrees is
  identical, byte-for-byte. Not modified by T5.

## 8. Issue #256 closure check

Both halves independently confirmed:
1. Documented owner type (MSA) now works -- item 7's live flip
   (FP_ParameterError to NO EXCEPTION) plus my own MoStemMsa round-trip
   (section 5), reached via MsFeaturesOA per the C1 resolver, not the
   impossible FeaturesOA.
2. Nested feature structures CAN be expressed -- my own recursive-dict
   probe (section 5), which is NOT present anywhere in the shipped suite
   (the programmer's own report flags this as a T14 gap, honestly
   disclosed rather than silently skipped).

Both halves hold. #256 closure is justified.

## 9. Discrepancy noted (does not fail the gate)

Frozen contract C3 states specs keys/values accept "a name" as an
operand. Read live: plain name-string resolution is NOT implemented --
passing a bare string (e.g. TEST_c3_agreement) to MakeFeatStruc raises
FP_ParameterError: Invalid parameter, hvoOrGuid (confirmed by my first,
failing probe attempt before I switched to HVO operands). This is
disclosed in both the programmer's cycle-5 report (section 3,
Name-string operand support row) and in _MakeFeatStruc's own docstring
Notes.

Independently verified this is NOT a T5 regression: read the pre-T5
InflectionFeatureOperations.py line 1024 body at the true parent commit --
__ResolveFeature's non-int branch is a pure passthrough (return
feature_or_hvo), no Find-style name lookup. Neither pre-T5 twin ever
resolved bare name strings; C3's "a name" language was aspirational
relative to what either implementation actually did, and T5 preserves
that gap unchanged rather than silently guessing which Find-style lookup
a bare string should hit. Recommend the lead reconcile spec.md C3's
wording (strike "a name" or open a follow-up task) -- this should not
block T5's own gate since it is a pre-existing, disclosed, non-regressive
limitation, not something T5 introduced.

## Cleanup

- Mutation reverted; hash-verified (section 4).
- Sena 3 restored via scripts/restore_sena3.py; re-verified clean
  (section 4).
- Target never touched; restore_target.py --check confirms present and
  unlocked.
- Both disposable worktrees (flexicon-t5-parent, flexicon-t5-head)
  removed via git worktree remove --force; git worktree list and
  git status --porcelain on the main checkout show no trace of my work
  and no file of mine staged or modified.

## Result
PASS -- every claim in scope observed live on both sides of T5's true
parent/HEAD boundary; mutation test falsifies the claim as required;
restore verified byte-identical; #256 closure justified on both halves;
one pre-existing, disclosed spec/implementation wording mismatch (C3 "a
name") noted for the lead, not gate-failing.
