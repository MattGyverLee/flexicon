# Issue #542 -- cycle 2 verification (lex-verification agent)

**Worktree:** C:\Github\flexicon-542, branch fix/542-affix-slot-readers,
HEAD e4f3259 (confirmed by git log -1). C:\Github\flexicon (main repo)
was not touched.

**Binding directive honored:** all live writes in this verification went
ONLY to a Sena 3 sandbox (sena3_sandbox fixture / an equivalent tempdir
copy). Target was never opened write-enabled; scripts/restore_target.py
was never run.

## Item 1 -- Re-run both required invocations

[PASS]

cd C:\Github\flexicon-542
python -m pytest -m "not requires_live_project" -q
5 failed, 2506 passed, 1040 deselected, 16 warnings in 12.33s

Failures: test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies,
and 4 in test_morphrule_duplicate_deep.py::TestDuplicateDeepGating -- same
5 as reported by the programmer.

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q
4 passed in 7.86s

tests/live_status.json shows "run_mode": "live" (confirmed both after the
programmer's live file and after my own independent script, below).

## Item 2 -- Live test file no longer touches Target

[PASS]

grep -n "target_project|target_sandbox|Target" tests/operations/test_issue542_affix_slot_readers_live.py
(no matches)

## Item 3 -- Confirm the 5 offline failures against a clean origin/main

[PARTIAL FAIL -- one of the five failures is NOT pre-existing]

Detached scratch worktree:

git fetch origin main
git worktree add --detach C:/Github/flexicon-542-scratch-main origin/main
  -> HEAD is now at 5b2631a Merge pull request #554 (fix/543-get-infl-aff-msa-slots)
python -m pytest tests/contract/test_lcm_contract.py tests/operations/test_morphrule_duplicate_deep.py -m "not requires_live_project" -q
4 failed, 24 passed, 2 warnings in 2.36s

The 4 test_morphrule_duplicate_deep.py failures reproduce identically on
origin/main -- genuinely pre-existing, confirmed. [PASS] for those 4.

test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies
did NOT fail on origin/main (ran it in isolation there: 1 passed).
Running the identical test on the fix/542-affix-slot-readers branch
fails with:

Failed: New LCM type dependencies detected (update baseline if intentional):
  + IMoInflAffixSlot

This is a real, branch-introduced contract-stability failure, not
pre-existing. POSOperations.py now does "from ... import IMoInflAffixSlot"
(a real pythonnet cast target for __ResolveSlot), and
tests/contract/snapshots/expected_contract.json was never updated to
accept that new type dependency -- the test's own failure message says
exactly that: update baseline if intentional. Both cycle1's and cycle2's
programmer reports state the failures were "confirmed via git stash +
re-run" -- git stash only reverts uncommitted changes, and by the time
this check was made the branch's commits were already committed, so that
method could not have detected this. Scratch worktree removed after use
(git worktree remove ... --force).

[FAIL] for the claim "all 5 offline failures are pre-existing on
origin/main" -- 4 of 5 are; 1 of 5 is a new contract-stability failure
introduced by this branch's own new LCM type import.

[NOTE] This is an offline/hygiene finding, not a live-LCM defect -- the
actual live behavior of the new methods is correct (see Item 4). It does
not change the live verdict but is a blocker for a clean merge: the
baseline snapshot (tests/contract/snapshots/expected_contract.json) needs
IMoInflAffixSlot added deliberately, or the import needs justifying
inline, before this branch can honestly claim a green offline gate.

## Item 4 -- Independent live script against Sena 3 sandbox

[PASS]

Wrote an independent test (not reusing the programmer's test file),
tests/operations/test_issue542_verification_agent_scratch.py, run via
the sena3_sandbox fixture (fresh tempdir copy of
tests/fixtures/Sena 3 2026-06-09 1645.fwbackup, discarded on teardown).
Also drafted a standalone (non-pytest) script first
(scratchpad/verify_542.py) but it hit FwRegistryHelper.Initialize() /
FLExInitialize() preconditions not met outside the pytest session
fixture (System.ArgumentNullException building ILgWritingSystemFactory)
-- expected, since tests/flex_plugin.py's session-scoped
initialize_flex_for_tests fixture performs that setup. Ran the checks as
a pytest test instead so that fixture applies.

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_verification_agent_scratch.py -m requires_live_project -q
1 passed in 3.26s

tests/live_status.json shows "run_mode": "live", test recorded under
POSOperations.read.

Checks performed and results (all re-queried from the LCM, not asserted
against the value just passed in):

- Read-only pass: every POS's GetAffixSlots() in Sena 3, .name/.optional/
  .affixes accessed without raising, cross-checked against
  GetAffixesInSlot -- PASS, ran over every POS in Sena 3, 0 raised.
- GetSlotName via object == via HVO, both "TEST_542V_req" -- PASS.
- IsSlotOptional reflects creation flags (False/True) -- PASS.
- SetSlotOptional(slot, True) -> fresh
  IMoInflAffixSlot(ServiceLocator.GetObject(hvo)).Optional == True
  (re-fetched, not the passed-in value) -- PASS.
- SetSlotName(slot, "...renamed") -> fresh
  IMoInflAffixSlot(...).Name.get_String(analWs).Text ==
  "TEST_542V_req_renamed" (re-fetched) -- PASS.
- GetAffixesInSlot(slot) vs MSAOperations.GetInflAffMsaSlots(sense) (#543
  inverse) agree on the same HVO set after
  MSA.CreateInflAff(sense, pos, slots=[slot]) -- PASS, both sides
  contained the matching HVO.
- HVO input to GetSlotName/IsSlotOptional/GetAffixesInSlot -- PASS, all
  three accept a bare int HVO.
- Wrapper (AffixSlot) .name/.optional/.affixes from GetAffixSlots() match
  the corresponding direct-method reads -- PASS.
- GetSlotName(non-slot) (an IPartOfSpeech) raises FP_ParameterError --
  PASS.

Cleanup: created slots removed from test_pos.AffixSlotsOC, created entry
deleted, all inside a finally: block; the sandbox tempdir is disposable
regardless (deleted on fixture teardown). The scratch test file
(tests/operations/test_issue542_verification_agent_scratch.py) was
deleted after the run; git status --porcelain on the worktree shows no
stray tracked/untracked file from it.

No writes to Target at any point in this verification -- confirmed by
git status before/after and by grep showing no target_project/
target_sandbox reference anywhere in the tests run.

## Item 5 -- Evidence file meets "Evidence is mandatory"

[PASS]

specs/542-affix-slot-readers/evidence/live-542.md cites run_mode: "live",
both exact commands, and a pre/post table where every "after" value is
explicitly re-fetched via a fresh IMoInflAffixSlot(project.Object(hvo))
or ITsString(...).Text read rather than the Python variable just
assigned -- satisfies CLAUDE.md's "re-querying the object after the
write" requirement. My own independent run (Item 4) reproduces the same
re-fetch pattern and the same pass/fail outcome, corroborating the
evidence file's claims.

## Overall

Live LCM verification: PASS. run_mode: live in both the programmer's run
and my independent re-run; every claim in the issue (GetSlotName with
***/empty normalization, SetSlotOptional/SetSlotName persisted and read
back fresh, GetAffixesInSlot agreeing with GetInflAffMsaSlots, HVO input,
AffixSlot wrapper .name/.optional/.affixes) was independently observed
against a live LCM (Sena 3 sandbox), with cleanup confirmed and zero
writes to Target.

Blocker for merge (not a live-LCM defect): the offline claim "all 5
pre-existing failures are unrelated to this change" is inaccurate for one
of the five -- test_lcm_contract.py::TestContractStability::
test_no_new_type_dependencies fails only on this branch (passes on
origin/main 5b2631a) because POSOperations.py now imports
IMoInflAffixSlot, a type not yet in
tests/contract/snapshots/expected_contract.json. Needs the baseline
updated deliberately (or the import justified) before this is a clean
offline gate.

## Recommendation

FIX ISSUES -- live behavior is fully verified and correct (PASS); fix the
contract-baseline mischaracterization (update expected_contract.json to
accept IMoInflAffixSlot, or otherwise address
test_no_new_type_dependencies) and correct the cycle1/cycle2
"pre-existing" claims before this is ready to merge/PR.
