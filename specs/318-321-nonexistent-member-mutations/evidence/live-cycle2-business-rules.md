# Live verification -- cycle 2 business rules (#319, #320)

**Project:** Sena 3 (full shutil.copytree copy of the real, populated
project directory into a tempdir -- no tests/fixtures/Sena 3*.fwbackup
exists in this repo, so the standard sena3_sandbox fixture could not be
used; this mirrors the prior cycle approach of copying the live project
tree directly).
**Fixture:** ad hoc sena3_full_copy_sandbox (custom, defined inline in a
throwaway pytest file, deleted after the run -- see Cleanup).
**Command:**

    FLEXLIBS_REQUIRE_LIVE=1 PYTHONIOENCODING=utf-8 python -m pytest \
      tests/operations/test_zz_cycle2_probe_live_business_rules.py \
      -m requires_live_project -q -s

**run_mode:** live (session fixture initialize_flex_for_tests completed
full FieldWorks/LCM initialization; ModelVersion 7000072 read from the
live cache; test result: 1 passed)
**FLEx/LCM version:** ModelVersion 7000072 (FieldWorks 9 installation at
C:\Program Files\SIL\FieldWorks 9\)
**Date:** 2026-09-18

**Isolation method:** every mutation in this probe ran against a
shutil.copytree of C:\ProgramData\SIL\FieldWorks\Projects\Sena 3 into a
fresh tempfile.mkdtemp() directory, opened by absolute path
(FLExProject.OpenProject(str(fwdata), writeEnabled=True, undoable=False)).
No flexicon Operations classes were imported or called -- every object was
obtained and mutated via raw SIL.LCModel factories/repositories/interfaces
(ICmOverlayFactory, IRnGenericRecFactory, ICmPersonFactory,
ServiceLocator.GetObject, etc.), per the isolation requirement (three
programmer agents are concurrently editing OverlayOperations.py and
DataNotebookOperations.py).

## Claim under test

Two UNVERIFIED business rules from the cycle-1 domain review
(specs/318-321-nonexistent-member-mutations/reviews/cycle1-domain.md):

1. #320 -- does LCM enforce that an ICmPossibility added to
   overlay.PossItemsRC must already be a member of the list referenced by
   overlay.PossListRA?
2. #319 -- the roled-participant creation path
   (DefaultRoledParticipants / MakeDefaultRoledParticipant() /
   ParticipantsOC / ParticipantsRC) that AddParticipant/
   RemoveParticipant must be rewritten onto.

---

## QUESTION 1 -- #320 overlay element membership rule

### Pre-state (read from LCM)

- IDsConstChartRepository.AllInstances(): 4 charts in Sena 3. None of
  them exposes an OverlaysOC property at all (DsConstChart's own
  members are only HeaderFooterSetsOC, PublicationsOC, RowsOS), and
  neither does the chart's owner (DsDiscourseData) -- confirming the
  cycle-1 domain review's finding that OverlaysOC does not exist
  anywhere reachable from a chart.
- A project-wide ICmOverlayRepository.AllInstances() probe found one
  pre-existing live overlay in Sena 3, independent of any chart
  navigation path: HVO 13787.
- overlay.PossListRA HVO: 139977. Walking PossListRA.PossibilitiesOS
  (and every level of SubPossibilitiesOS beneath it) enumerates 859
  possibility HVOs -- this is the "membership tree" the fix is meant to
  validate against.
- overlay.PossItemsRC before the experiment: 859 items (pre count: 859
  in the raw log).
- Chosen "foreign" possibility, deliberately not in the 859-item
  membership tree: HVO 34.

### Action

    overlay.PossItemsRC.Add(foreign)   # foreign.Hvo == 34, NOT in PossListRA tree

No _TransactionCM/UOW wrapper beyond the ambient session-long
non-undoable task from OpenProject(..., undoable=False).

### Post-state (re-queried from LCM)

- add_exception: None -- the Add() call raised nothing.
- Re-fetched the overlay fresh by HVO via
  cache.ServiceLocator.GetObject(overlay.Hvo) (not the stale handle held
  before the call -- the #317 trap):
  - foreign persisted: True (HVO 34 is present in the fresh PossItemsRC)
  - fresh count: 860 (up from 859 -- the add genuinely took effect, it
    was not a silent no-op)

### Cleanup

overlay_fresh.PossItemsRC.Remove(foreign) ran immediately after
confirming persistence (cleanup removed foreign item in the log),
returning the sandbox copy's overlay to 859 items. The whole exercise ran
against the tempdir copy only; irrelevant to the original project's state,
but done anyway for tidiness.

### Result

VERDICT: PERMISSIVE. LCM raised no exception and durably persisted an
ICmPossibility added to overlay.PossItemsRC that is not a member of
the possibility list referenced by overlay.PossListRA. The LCM data layer
does not enforce list-membership as an invariant on this reference
collection. This does not rule out FLEx's UI enforcing the constraint at a
higher layer (out of scope for this probe -- no UI was exercised), but at
the LCM/liblcm layer the fix's proposed validation guard is not backed by
any LCM-side rejection.

---

## QUESTION 2 -- #319 roled-participant creation

A fresh, raw IRnGenericRec was created directly under
project.lp.ResearchNotebookOA.RecordsOC (bypassing DataNotebookOperations
entirely) to guarantee a record starting with no participant group, and
to avoid any ambiguity from pre-existing production data.

- Record HVO: 152328

### (a) DefaultRoledParticipants on a record with no group

- Pre-state: record.DefaultRoledParticipants returned None (genuine
  Python None, not an empty/zero-valued object).
- record.ParticipantsOC.Count before: 0.

Confirmed: the accessor returns a true null, not an empty placeholder
object.

### (b) MakeDefaultRoledParticipant() creates and owns a new IRnRoledPartic

- record.MakeDefaultRoledParticipant() returned grp1, HVO 152329. No
  exception.
- record.ParticipantsOC.Count in-memory: before 0, after 1.
- Fresh re-fetch via
  IRnGenericRec(cache.ServiceLocator.GetObject(record.Hvo)):
  ParticipantsOC.Count == 1, members [152329] -- the creation is
  genuinely durable in the cache, not a stale-handle illusion.
- grp1.Owner.Hvo == record.Hvo (152328 == 152328) -- grp1 is owned by
  the record, confirming ParticipantsOC is the owning collection for the
  new group.
- After the first call, record_fresh.DefaultRoledParticipants resolved
  to "RnRoledPartic : 152329", matching grp1.Hvo exactly
  (b_drp2_matches_grp1: True).

Confirmed: MakeDefaultRoledParticipant() both creates and owns the
new IRnRoledPartic under ParticipantsOC, and DefaultRoledParticipants
picks it up immediately afterward.

### (c) Transaction requirement

The project was opened with undoable=False, which per
flexicon/code/FLExProject.py holds one session-long
BeginNonUndoableTask() envelope open for the whole session
(CurrentDepth read back as 1 at the end of the script, confirming the
ambient task was open throughout). MakeDefaultRoledParticipant() was
called with no additional, explicit unit-of-work wrapper on top of that
ambient task, and it succeeded without raising.

Partially confirmed, with a caveat: this shows the call works fine
inside an open write task -- consistent with the fix wrapping it in
_TransactionCM alongside the other mutating Operations methods, the way
DataNotebookOperations.Create() already does for
IRnGenericRecFactory.Create(). It does not by itself prove what
happens with zero open action-handler depth (e.g. undoable=True mode
with no active per-operation UOW), because undoable=False always keeps
one ambient task open for the session's lifetime and no code path was
exercised that closes it first. Settling that residual sub-question would
require a second experiment opened with undoable=True and no
_TransactionCM/manual BeginUndoTask wrapper around the call -- not
performed here since the practical answer needed by the fix (call it
inside a transaction) is already confirmed.

### (d) Calling MakeDefaultRoledParticipant() twice

- Second call returned grp2, HVO 152330.
- d_same_as_grp1: False -- a different object, not the same one
  returned again.
- Fresh re-fetch: ParticipantsOC.Count == 2, members
  [152329, 152330].
- d_created_new_group: True.

Confirmed and important: MakeDefaultRoledParticipant() is NOT
idempotent. Calling it twice creates two separate IRnRoledPartic
groups owned by the same record. The #319 fix MUST guard against this
explicitly -- e.g. check "if record.DefaultRoledParticipants is None"
before calling MakeDefaultRoledParticipant(), and reuse the existing
group otherwise -- rather than calling MakeDefaultRoledParticipant()
unconditionally on every AddParticipant() call, or every second
participant added to a record will silently spawn a duplicate default
group.

### (e) ParticipantsRC.Remove unlinks without deleting the person

- Raw ICmPerson created (HVO 152331) and owned via
  project.lp.PeopleOA.PossibilitiesOS.Add(person).
- group.ParticipantsRC.Add(person) -> count 1.
- group.ParticipantsRC.Remove(person) -> count 0.
- Re-fetch: cache.ServiceLocator.GetObject(person.Hvo) still resolves,
  ClassName == "CmPerson" -- the person object was not deleted by
  removal from the reference collection.

Confirmed: ParticipantsRC.Remove (an ILcmReferenceCollection) only
unlinks; it is not destructive to the referenced ICmPerson.

Observed only, not performed: removal from the owning collection
(project.lp.PeopleOA.PossibilitiesOS.Remove(person)) was NOT
exercised -- per the task's explicit instruction not to perform a
destructive operation, and because this was already the well-understood
asymmetry the domain review flagged (owning OS/OC removal deletes;
reference RC removal only unlinks). No new evidence was needed here
beyond confirming the non-destructive RC side, which is done above.

---

## Cleanup

- All mutations (new overlay-list membership on HVO 13787, notebook record
  152328, roled-partic groups 152329/152330, person 152331) were made
  only inside the tempdir copy
  (%TEMP%\sena3_full_copy_w58s0wwd\Sena 3\Sena 3.fwdata), which was
  deleted (shutil.rmtree) by the fixture's finally: block on test
  teardown, then re-confirmed deleted and removed by hand afterward.
- The throwaway pytest file used to run this probe
  (tests/operations/test_zz_cycle2_probe_live_business_rules.py) was
  deleted after the run; git status on tests/operations/ shows no
  trace of it.
- Original-project integrity check: grep -c "TEST_probe" against
  both C:\ProgramData\SIL\FieldWorks\Projects\Sena 3\Sena 3.fwdata and
  Sena 3.bak returned 0 matches in both files -- none of this probe's
  test markers leaked into the real project.
- The real Sena 3.fwdata's LastWriteTime/size did change during the
  session (from 9/18/2026 4:03:58 PM / 55,955,978 bytes to
  9/18/2026 4:50:53 PM / 55,956,965 bytes). tasklist confirmed a
  FieldWorks.exe process (PID 25040) was already running before any
  probe activity started, and a transient
  SIL.LCModel.LcmFileLockedException ("... Sena 3 ... in use by another
  program") was hit on a subsequent OpenProject() call against a brand
  new tempdir copy, consistent with that already-running FieldWorks.exe
  instance holding the real Sena 3 project open and independently
  autosaving/touching it -- not with anything this probe did (this probe
  never opened the real path; it only ever opened tempdir copies by
  absolute path). The grep check above is the operative confirmation
  that the content is clean of this probe's markers.

## Result

[PASS] -- both business rules settled with live evidence; see verdicts in
specs/318-321-nonexistent-member-mutations/reviews/cycle2-verification.md.
