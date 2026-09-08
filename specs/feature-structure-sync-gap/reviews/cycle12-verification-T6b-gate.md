# Cycle 12 -- Verification gate, Checkpoint 3b (T6b)

**HEAD:** 84b66c86 | **Verifier:** independent verification agent (not the
programmer). Every measurement below was re-run from scratch in this
cycle; none is copied from the programmer's own report.

**Verdict: CHECKPOINT 3b: PASS**

---

## Leg 1 -- item 1 mutation + differential (THE CLOSING CONDITION)

Pre-mutation hash of `flexicon/code/Lexicon/MSAOperations.py`:
`e7e8f791edb089c0b4ae86f10cca4bcd34900194` -- matches the expected value.
All work done in disposable worktree `wt-t6b-gate` at HEAD, fixture
copied read-only, never touching the shared tree.

Mutation applied: replaced the ClassName-dispatched cast table in
`__GetMsaObject` with an unconditional `return obj` (same shape as
cycle 10's mutation).

Full live file result under the mutation: 2 failed, 6 passed
(`tests/operations/test_issue251_msa_feature_sync.py -m requires_live_project`).

Differential, stated explicitly:

- The two NEW item-1 tests FAILED:
  - `TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_stem_msa`
    -- `AttributeError: 'ICmObject' object has no attribute 'MsFeaturesOA'`
    at `tests/operations/test_issue251_msa_feature_sync.py:1059`
  - `TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_infl_aff_msa`
    -- `AttributeError: 'ICmObject' object has no attribute 'InflFeatsOA'`
    at `tests/operations/test_issue251_msa_feature_sync.py:1078`
- The SIX pre-existing live tests in the file STAYED GREEN under the
  identical mutation (the static `test_get_msa_object_casts_on_hvo_and_guid_path`
  is offline so not part of this live count; the six live survivors are
  the four `TestMSASyncLiveRoundTrip` round-trip tests, the
  unresolved-GUID raise test, and the HVO/GUID entry-path capture test)
  -- reproducing the exact cycle-10 NOT-KILLED result.

Both halves hold: item 1 added genuinely new falsifiability that did not
exist before T6b. Restored, `git hash-object` identical
(`e7e8f791edb089c0b4ae86f10cca4bcd34900194`), full offline+live worktree
suite re-passed clean after restore (25 passed / 8 deselected offline).

Leg 1(f) -- pre-cast assertion is live-real, checked at HEAD (unmutated):
`sandbox.Object(hvo)` for a freshly-created MoStemMsa/MoInflAffMsa
returns a genuine bare ICmObject from ServiceLocator.GetObject (via
FLExProject.Object), NOT a mock and NOT the factory handle held at write
time (the test calls `stem.Hvo`/`str(stem.Guid)` off the factory handle,
then re-enters through `sandbox.Object(hvo)`, a separate call).
`hasattr(bare, "MsFeaturesOA")` and `hasattr(bare, "InflFeatsOA")` were
both confirmed False in the clean (8-passed) live run. The
0-true/2088-false campaign premise still holds.

## Leg 2 -- per-path falsifiability of item 1 (honesty leg)

The lead's pre-committed prediction HOLDS, stated plainly.
`__GetMsaObject` (`flexicon/code/Lexicon/MSAOperations.py:1142-1158`)
funnels BOTH the HVO(int) and GUID(str) paths through the exact same
line, `self.project.Object(msa_or_hvo)` (`isinstance(msa_or_hvo, (int,
str))` is a single branch covering both types), and `FLExProject.Object`
(`flexicon/code/FLExProject.py:3538-3552`) itself only branches
internally to turn a str into a System.Guid before both types reach the
identical `self.project.ServiceLocator.GetObject(hvoOrGuid)` call. After
that, `__GetMsaObject` has exactly ONE
`class_name = getattr(obj, "ClassName", None)` plus cast-dispatch site,
reached identically regardless of entry type. A per-path-only cast
mutation is structurally impossible -- there is only one cast to mutate,
and it cannot be reached by one path without the other also passing
through it.

What actually locks each path separately is NOT inside `__GetMsaObject`
at all: it is `FLExProject.Object`'s own isinstance dispatch (str ->
System.Guid parse -> same GetObject; int -> same GetObject directly) --
i.e. the GUID branch does NOT re-resolve through a separate
repository/factory call inside `__GetMsaObject`; it funnels into the
identical `ServiceLocator.GetObject` the HVO branch uses, just after an
extra string-to-Guid parse one frame up.

Empirical check (not merely predicted): to rule out "the GUID-path
assertion is decorative because the HVO-path assertion fails first and
short-circuits the test," a second disposable worktree (`wt-t6b-gate2`)
was built with (a) the same Leg-1 cast-removal mutation and (b) the
HVO-path assertions in `test_hvo_and_guid_path_cast_to_concrete_stem_msa`
temporarily deleted so ONLY the GUID-path assertion could run. Result:
the isolated GUID-path assertion ALSO failed independently --
`AttributeError: 'ICmObject' object has no attribute 'MsFeaturesOA'` at
line 1059 (now the sole remaining assertion). Neither path's assertion
is decorative -- each is independently load-bearing at the assertion
level, even though both reach the identical single cast site in
production code. No P1 here: the "both paths" wording in item 1's intent
is honestly met (both entry types are exercised and both would catch a
removed cast), it is simply not evidence of two separable cast
mechanisms, because there is only one.

## Leg 3 -- item 3 re-mutation with differential (offline)

Mutation: `__ApplyFeatureStrucProp`'s presence gate
`if key in props or guid_key in props:` (line 1094) changed to
`if props.get(key) or props.get(guid_key):`.

Result on `TestMSASyncApplyPresenceGate` (4 tests, offline,
`-m "not requires_live_project"`): 2 failed, 2 passed.

- NEW tests FAILED:
  - `test_falsy_but_present_feature_struct_key_still_triggers_apply` --
    `AssertionError: A present-but-falsy MsFeatures/MsFeaturesGuid pair
    must still trigger _ApplyFeatureStruc (C6 presence gate, not
    truthiness). assert 0 == 1` at line 715.
  - `test_falsy_but_present_guid_only_key_still_triggers_apply` --
    `AssertionError: A present-but-falsy MsFeaturesGuid (with MsFeatures
    absent) must still trigger _ApplyFeatureStruc. assert 0 == 1` at
    line 751.
- PRE-EXISTING tests STAYED GREEN under the identical mutation:
  `test_guid_only_present_still_triggers_apply_with_empty_spec`,
  `test_neither_key_present_never_calls_apply_feature_struc`.

Both halves hold, reproducing the cycle-10 finding that the two
pre-existing tests cannot separate presence from truthiness. Restored,
`git hash-object` identical (`e7e8f791edb089c0b4ae86f10cca4bcd34900194`).

## Leg 4 -- item 2, the self-declared unmutated item

Mutated the single `on_unresolved="raise"` call site inside
`__ApplyFeatureStrucProp` (line 1105) to `on_unresolved="skip"`.

Ran `TestMSASyncApplyRaisePropagationThroughPublicSurface` (offline).
Result: 1 failed --
`AssertionError: MSAOperations.__ApplyFeatureStrucProp must call
_ApplyFeatureStruc with on_unresolved='raise' unconditionally (C7) --
this is the one assertion in this class that would fail if that were
mutated to 'skip'. assert 'skip' == 'raise'` at line 961.

Finding: KILLED, not NOT-KILLED. The pre-committed ruling anticipated
that a NOT-KILLED result here would be recorded as a P1 constraint on
T7; that contingency did not materialize -- the programmer's own
"reasoned kill" claim (mutation-sensitive by construction, not
independently mutation-run this cycle) is now independently CONFIRMED
correct by an actual mutation run. This is recorded as an informational
P2, not a P1: the programmer's prediction was sound, but the process gap
itself (shipping an un-run "reasoned kill" through a checkpoint gate) is
still worth naming as a standing practice note for T7, which copies
these patterns by design -- future items should get an actual mutation
pass rather than a predicted one wherever it is this cheap, even when
the spec does not strictly require it. Restored, git hash-object
identical.

## Leg 5 -- item 4 AST allowlist non-vacuity

5a (`MSAOperations.__GetMsaObject`): inserted
`hasattr(obj, "MsFeaturesOA")` (disallowed attribute) into the method
body. `test_get_msa_object_hasattr_calls_are_allowlisted` FAILED:
`AssertionError: __GetMsaObject calls hasattr(x, 'MsFeaturesOA') -- only
['ClassName', 'Hvo', '_obj'] are permitted. A subtype-declared LCM
member must be discriminated via .ClassName + explicit cast, never
hasattr (D5).` at line 287 -- names the offending attribute exactly.
Restored, hash identical.

5b (`BaseOperations._ResolveFeatureStrucOwner`): inserted the same
disallowed `hasattr(unwrapped, "MsFeaturesOA")` into the method body (in
`flexicon/code/BaseOperations.py`, pre-mutation hash
`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`).
`test_resolve_feature_struc_owner_hasattr_calls_are_allowlisted` FAILED:
`AssertionError: _ResolveFeatureStrucOwner calls hasattr(x,
'MsFeaturesOA') -- only ['ClassName', 'Hvo', '_obj'] are permitted
(D5).` at line 313. Restored, hash identical
(`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`).

Both AST-allowlist tests walk real call sites, not an empty list --
non-vacuity confirmed for both.

## Leg 6 -- measurement reproduction (shared tree, read-only)

- Offline comparator: 396 passed, 2 failed, 512 deselected -- exact
  match to spec, pinned foreign pair unchanged
  (`TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
  `::test_depth_restored_on_exception`). No third failure.
- Live full file: 8 passed, 25 deselected -- 0 failed, exact match.
- `tests/live_status.json`: `"run_mode": "live"`,
  `"uncategorized_live_tests": []` -- confirmed.
- Both new item-1 tests carry
  `@pytest.mark.live_phase("MSAOperations", "modify")` -- confirmed by
  direct read of the test source (lines 1038, 1065).

## Leg 7 -- claim-honesty scan

(a) No overclaim found. Searched `specs/feature-structure-sync-gap/`
(evidence, reviews, `.crew-handoff.json`, `spec.md`, `STATUS.md`),
`CHANGELOG.md`, and the T6b diff itself
(`git show c9d2a9a9 3af3a47b 84b66c86`) for
"live-proven"/"all four"/"family-wide"/"covers all"-style language tied
to the item-1 direct-cast test. `STATUS.md:1227` ("cast, covering all
four in-scope C1 MSA rows") refers to the PRODUCTION dispatch table
(GetSyncableProperties/ApplySyncableProperties), which genuinely does
cover all four C1 rows via other tests (the fake-object dispatch suite
and the live round-trip suite) -- a different and true claim, not a
claim about item 1's direct-cast test. Both T6b artifacts
(`cycle11-programmer-T6b.md`, `evidence/live-T6b.md`) explicitly
disclose "2 of 4 rows" / "MoDerivAffMsa and MoUnclassifiedAffixMsa are
NOT covered by this direct-cast pattern." No CHANGELOG.md, spec.md, or
`.crew-handoff.json` edits were made by the T6b commits at all
(`git show --stat` on all three: only the test file and the two report
files touched). No overclaim to quote.

(b) Shared-tree state confirmed clean:
`git hash-object flexicon/code/Lexicon/MSAOperations.py` ==
`e7e8f791edb089c0b4ae86f10cca4bcd34900194`;
`git hash-object flexicon/code/BaseOperations.py` ==
`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`; `git diff --stat` on both is
empty; `git worktree list` shows only the main tree;
`git worktree prune --dry-run -v` is silent; both disposable worktrees
(`wt-t6b-gate`, `wt-t6b-gate2`) were removed with
`git worktree remove --force`.

Working-tree attribution: exactly the five expected pre-existing noise
items confirmed present and left untracked/unstaged: deleted
`.claude/ralph-loop.local.md`, untracked `.vscode/settings.json`,
untracked `specs/243-closeproject-save-guard/.spec-context.json`,
untracked `specs/duplicate-signature-harmonisation/evidence/live-issue-246.md`,
untracked `specs/getall-contract-flexicon/.spec-context.json`. None
committed, none attributed to T6b.

## Findings summary

| # | Severity | Finding |
|---|---|---|
| 1 | none (informational) | Leg 2: per-path cast mutation is structurally impossible (single shared cast site); both HVO/GUID assertions independently confirmed load-bearing at the assertion level by isolation test. Not a defect. |
| 2 | P2 (informational, process note for T7) | Leg 4: item 2's "reasoned kill" was NOT independently mutation-run by the programmer this cycle, but this gate ran it and it KILLED cleanly. No blocking issue; record as a standing practice note that T7 should prefer an actual mutation run over a predicted one wherever this cheap. |

No P0/P1 findings. Every claim under test held.

## Final verdict

CHECKPOINT 3b: PASS
