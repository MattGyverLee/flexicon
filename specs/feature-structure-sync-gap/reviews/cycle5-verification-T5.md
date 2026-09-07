GATE: PASS

# Cycle 5 -- Verification report: T5 (MakeFeatStruc generalization, closes #256)

**Verdict:** PASS
**Live run:** yes | **run_mode:** live
**Evidence:** specs/feature-structure-sync-gap/evidence/live-cycle5-verification-t5.md
**Project:** Target (presence/lock check) + Sena 3 (writable_project, in-place) + target_sandbox/sena3_sandbox

## Concurrency-collision check (independent, per this cycle's alert)

Re-ran the check the implementer claims to have done myself:
git show --name-only --format= 6643b483 lists exactly five files, all T5's
own (BaseOperations.py, InflectionFeatureOperations.py,
PhonFeatureOperations.py, evidence/live-T5.md,
reviews/cycle5-programmer-T5.md). Nothing from the other crew's fence
(TextsWords/{Paragraph,Segment,Discourse}Operations.py, the
name-field-whitespace-identity / 242-paragraph-whitespace /
tier1-silent-data-loss spec trees, the two whitespace-probe test files)
is present. **No index-collision residue landed in this commit.**

## True parent, re-derived independently

git log -1 --format=%P 6643b483 -> 7bc6d01c568290c3119d8212f7a436b0feef4fce
(single parent; history was linear at this point). NOT assumed as HEAD~1,
NOT trusted from the report -- both were independently re-derived and
match what the report claims.

## Claim vs. observed

| Claim | Observed live | Status |
|---|---|---|
| One generalized _MakeFeatStruc backs both Infl/Phon MakeFeatStruc | Confirmed: single body at BaseOperations.py:2387, two 1-line call-throughs; only other hits are in the excluded, gitignored build/lib/ tree | PASS |
| Owner resolution routed through C1 table, not hasattr(FeaturesOA) | Confirmed by reading the code and grepping; the removed gate only survives in docstring/comment prose | PASS |
| #256 fixed: MSA owner can build a feature struct | Live flip reproduced myself: parent raises FP_ParameterError, head returns a real IFsFeatStruc, both under FLEXLIBS_REQUIRE_LIVE=1 / run_mode: live | PASS |
| Recursive dict AND legacy flat list both work | Legacy list: shipped tests, live, green. Recursive dict: NOT exercised by any shipped test -- I wrote and ran my own live probe against target_sandbox; round-tripped a 2-level nested structure, re-fetched from a fresh object, values matched | PASS |
| slot= disambiguates | Shipped tests only exercise the resolver directly. I wrote and ran my own live probe calling MakeFeatStruc itself with slot="From"/"To" on the same MoDerivAffMsa; both properties populated independently with correct nested values | PASS |
| owner=None still raises | Confirmed live via two shipped, green tests | PASS |
| Live subset identical parent vs head except the #256 flip | Confirmed: 1 failed/77 passed/1 skipped/27 deselected on both sides, run_mode live on every run; only change is item 7's printed evidence | PASS |
| Offline pinned subset delta | 0: 2 failed/350 passed/489 deselected both sides, matching exactly the two known-foreign test_transaction_rollback failures | PASS |
| Determinism | 3 runs (2 same-shell, 1 fresh-shell) at head, all identical | PASS |
| Mutation test (falsifiability) | Forced prop_name to a bogus property inside _MakeFeatStruc; live subset went 1 failed -> 8 failed (7 new real failures across 3 files). Restored from a saved copy (never git checkout); git hash-object matched git rev-parse HEAD:<path> exactly (a32d94151fee1c3c62ccc33e71f3253990b0181a both). Re-ran clean afterward | PASS |
| No hasattr(FeaturesOA) gate, no blanket cast | Confirmed by direct grep + read; InflectionFeatureOperations.py:493's own gate correctly left alone (T11's scope, not T5's) | PASS |
| 5 production callers + 4 test files still work | All 5 call sites confirmed at exact claimed lines, unedited; all 4 test files pass live | PASS |
| tests/conftest.py untouched | diff between parent and head worktrees: byte-identical | PASS |
| #256 closure -- both halves | MSA-owner half confirmed (item 7 + my probe); nested-structure half confirmed (my probe only -- not in shipped suite, honestly disclosed by implementer as a T14 gap) | PASS |

## Incident during verification (disclosed, remediated)

My own mutation-test run left transient residue in the real, shared,
in-place Sena 3 project (writable_project opens it by name directly, not
a sandbox -- same fixture design the implementer's own report flagged).
A post-restore re-run initially showed 10 failed instead of the expected
1, despite BaseOperations.py being hash-verified byte-identical to HEAD.
Ran `python scripts/restore_sena3.py`; re-ran clean: back to
1 failed/77 passed/1 skipped/27 deselected, run_mode live. Target was
never opened by these test files and was confirmed present/unlocked
before and after via `restore_target.py --check`. Full account in the
evidence file, section 4.

## Discrepancy flagged for the lead (non-blocking)

Frozen contract C3's text says specs keys/values accept "a name" as an
operand. This is NOT implemented, and never was: I read the pre-T5 body
at the true parent commit and confirmed `__ResolveFeature`'s non-int
branch is a pure passthrough with no name-lookup in either twin. The
implementer disclosed this openly (report section 3, and in
`_MakeFeatStruc`'s own docstring). It is a pre-existing spec/
implementation wording gap, not a T5 regression, and should not block
this gate -- but spec.md's C3 text should be reconciled (strike "a name"
or file a follow-up) so it stops overclaiming.

## Mock suite (regression, supplementary)

Command: python -m pytest -m "not requires_live_project" -q
Not run bare (retired per spec.md 5.1 / flexicon#264). Pinned subset used
instead (tests/operations tests/contract only); see above -- delta 0,
determinism confirmed 3x.

## Blockers
None.

## Recommendation
APPROVE. One non-blocking documentation item for the lead: reconcile
spec.md C3's "a name" operand-shape claim against the actual (and
historically accurate) implementation.
