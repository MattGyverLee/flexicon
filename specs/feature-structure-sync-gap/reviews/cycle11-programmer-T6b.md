# Cycle 11 -- Programmer report, T6b (coverage-honesty follow-up to T6)

Test-only. `flexicon/code/Lexicon/MSAOperations.py` was never edited in
the shared tree (`git hash-object` == `e7e8f791edb089c0b4ae86f10cca4bcd34900194`
throughout, confirmed both before and after work). All mutation was
done inside a disposable `git worktree`, reverted and hash-verified,
then removed. Commits: `c9d2a9a9` (tests), `3af3a47b` (evidence).

## Item 1 -- direct C2 cast test (the item Checkpoint 3b gates on)

Added `TestMSASyncLiveGetMsaObjectCast` (Section D) with two live
tests, each calling `sandbox.MSA._MSAOperations__GetMsaObject(...)`
directly on both the HVO(int) and GUID(str) paths, for MoStemMsa
(`MsFeaturesOA`) and MoInflAffMsa (`InflFeatsOA`) -- both C1 rows as
required. Each test also asserts the PRE-cast bare object
(`sandbox.Object(hvo)`) LACKS the subtype member (lead ruling 3) --
this passed, so the campaign's 0-true/2088-false premise still holds.

**Mutation result: KILLED.** Removing the cast (unconditional
`return obj`) made both new tests fail with
`AttributeError: 'ICmObject' object has no attribute 'MsFeaturesOA'`
/ `'InflFeatsOA'`. Restored, hash-verified identical inside the
worktree. Both tests marked `@pytest.mark.live_phase("MSAOperations",
"modify")`; confirmed absent from `live_status.json`'s
`uncategorized_live_tests`.

**Narrower-than-it-reads note:** these two tests cover exactly the two
C1 rows I built factories for (MoStemMsa, MoInflAffMsa) -- MoDerivAffMsa
and MoUnclassifiedAffixMsa are NOT covered by this direct-cast pattern
(the latter has no feature-struct member to read at all, so a
parallel test would have nothing to assert). The spec's "at least TWO"
threshold is met, not exceeded.

## Item 2 -- rename + on_unresolved assertion

Renamed `TestMSASyncApplyRaisesOnUnresolvedGuid` ->
`TestMSASyncApplyRaisePropagationThroughPublicSurface`. Kept the
propagation assertion, added a recorded-call assertion that
`on_unresolved == "raise"` (per lead ruling 2 -- the spy itself was NOT
changed to branch on the policy string).

**Mutation result: NOT independently re-verified in this cycle** --
the spec's item 2 did not require a fresh live/offline mutation run for
this item specifically (the offline comparator run already includes
it: this test still passes at 396/2/512, i.e. no regression). Reasoned
kill: the new `on_unresolved == "raise"` assertion is a direct read of
a value the mutation (raise->skip) would change, so it is
mutation-sensitive by construction, but I did not run a separate
before/after mutation pass for it as the spec only asked for
mutation-verification on items 1 and 3.

**Narrower-than-it-reads note:** this class still only propagates
through a MOCKED `_ApplyFeatureStruc` -- it does not touch real LCM
policy. The docstring states, and I repeat here, that C7's real
enforcement lock remains the live test
`test_apply_raises_on_unresolved_feature_guid`.

## Item 3 -- falsy-but-present presence-gate tests

Added two tests to `TestMSASyncApplyPresenceGate`: struct key present
with `{}`, and Guid-only key present with `""`.

**Mutation result: KILLED (offline, in the same worktree).** Presence
gate -> truthiness gate mutation failed both new tests
(`assert 0 == 1`) while the two PRE-EXISTING tests in the same class
stayed green under the identical mutation -- directly confirming the
cycle-10 finding that those two cannot separate presence from
truthiness. Restored, hash-verified.

## Item 4 -- allowlisted hasattr AST test

Added `_hasattr_second_args` (ast walk over `hasattr(...)` call sites)
and two new static tests: one for `__GetMsaObject` (allows `_obj`,
`ClassName`, `Hvo`; found one call, `"_obj"`, which passes), one for
`BaseOperations._ResolveFeatureStrucOwner` (three calls: `"_obj"` x2,
`"ClassName"` x1, all pass). I chose to COVER `_ResolveFeatureStrucOwner`
rather than merely stating the boundary, since the lead's ruling
already confirmed all three of its calls are legitimate and the
allowlist is identical -- cheap to enforce, not a scope expansion in
practice.

**Narrower-than-it-reads note:** per the explicit exclusion in the
brief, I did NOT extend this to `ChangeAffixVariant`'s hasattr sites
(`MSAOperations.py:545/550/555`) -- those remain outside this rule
entirely, by design, not by oversight.

## Item 5 -- no new test, docstring-only

Updated docstrings on `TestMSASyncApplyUnclassifiedAffixNoRaise` and
the live `test_unclassified_affix_msa_capture_and_apply_do_not_raise`
to record the cycle-10 finding (structurally impossible to distinguish
presence/absence of the short-circuit) and name the two static AST
tests as the real lock. No assertions added or changed.

## Measurement summary

Offline: 392->396 passed, 2->2 failed (same two foreign
`TestPhase2JoinOrOpen` tests, unchanged message), 510->512 deselected.
+4 accounted for by name (2x item 4, 2x item 3); item 2 is a rename
(net 0); item 1's 2 new tests are `requires_live_project` (the +2
deselected). Live: 8/8 pass in the target file, `run_mode: live`, zero
uncategorized live tests. Full detail, exact failure messages, and
read-back values in
`specs/feature-structure-sync-gap/evidence/live-T6b.md`.

## Overall narrowness disclosure (the reason T6b exists)

Every item's fix is scoped to exactly the failure mode the cycle-10
mutation report named -- I did not generalize any of them into a
broader property-based or exhaustive test. In particular: item 1
covers 2 of the 4 C1 MSA rows (not MoDerivAffMsa or the no-op
UnclassifiedAffix case); item 2's kill was reasoned from the
assertion's construction, not independently mutation-run this cycle;
item 4's allowlist is a closed set of 3 names chosen from the lead's
ruling, not derived from a broader audit of every `hasattr` call in
the codebase. None of this contradicts the spec, which asked for
exactly these five bounded fixes -- but it is worth stating plainly
rather than leaving only in docstrings, per the instruction that
motivated this whole task.
