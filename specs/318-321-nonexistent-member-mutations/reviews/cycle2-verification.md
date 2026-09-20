# Cycle 2 verification -- #319/#320 business rules (live)

**Evidence:** specs/318-321-nonexistent-member-mutations/evidence/live-cycle2-business-rules.md
**Project:** Sena 3 (shutil.copytree tempdir copy, never the registered project)
**Isolation:** raw SIL.LCModel objects only -- no flexicon Operations classes imported/called
**run_mode:** live (ModelVersion 7000072, 1 passed)
**Original databases:** CONFIRMED untouched -- grep for this probe's TEST_
markers against the real Sena 3.fwdata and Sena 3.bak returned 0 matches
in both files. (Sena 3.fwdata's mtime/size did shift during the session;
attributable to an independently-running FieldWorks.exe process that was
already open before this probe started, not to any write this probe made
-- see evidence file "Cleanup" section for the full account.)

## VERDICT -- Question 1 (#320 overlay element membership rule)

PERMISSIVE. Adding an ICmPossibility to overlay.PossItemsRC that is not a
member of overlay.PossListRA's possibility tree raised no exception and
persisted on a fresh HVO re-fetch (859 -> 860 items; foreign HVO 34
confirmed present after re-fetch). LCM does not enforce this membership
constraint at the data layer. Recommendation to the fix author: LIFT the
validation guard rather than adding one -- LCM itself does not require
list membership as a precondition for PossItemsRC.Add(). (Whether FLEx's
UI independently enforces this is unverified and out of scope: no UI was
exercised, only the LCM data layer.)

## VERDICT -- Question 2 (#319 roled-participant creation)

CONFIRMED, with one documented caveat on part (c):
- (a) DefaultRoledParticipants is a genuine null (not an empty object) on
  a record with no participant group. CONFIRMED.
- (b) MakeDefaultRoledParticipant() creates a new IRnRoledPartic that is
  genuinely OWNED by the record under ParticipantsOC (owner HVO matches;
  survives fresh re-fetch). CONFIRMED.
- (c) The call succeeds inside an open write task (ambient
  BeginNonUndoableTask() from undoable=False, CurrentDepth==1 throughout).
  INCONCLUSIVE for the zero-open-task case specifically (not exercised --
  would need a separate undoable=True, no-wrapper experiment) but this
  does not block the fix: wrap the call in _TransactionCM like every
  other mutating Operations method already does.
- (d) Calling MakeDefaultRoledParticipant() twice creates TWO SEPARATE
  groups (HVO 152329 and 152330, ParticipantsOC.Count goes 0 -> 1 -> 2).
  It is NOT idempotent. CONFIRMED -- this is a hard requirement for the
  fix: it must check `record.DefaultRoledParticipants is None` before
  calling MakeDefaultRoledParticipant(), reusing the existing default
  group otherwise, or every AddParticipant() call after the first will
  spawn a duplicate default group.
- (e) Removing a person from a group's ParticipantsRC (reference
  collection) unlinks the person without deleting the ICmPerson (person
  HVO still resolves via GetObject after removal, ClassName confirmed
  CmPerson). CONFIRMED. The destructive owning-collection removal path
  (PeopleOA.PossibilitiesOS.Remove) was deliberately NOT exercised, per
  instructions -- this asymmetry (RC unlinks, owning OS/OC deletes) is
  accepted as the established/reflected LCM design and needs no further
  live confirmation beyond what cycle 1's domain review already
  documented.

## Confirmation

Original Target and Sena 3 databases (the real, registered FieldWorks
projects) were left unmodified by this probe. All writes occurred only
inside a disposable tempdir copy that was deleted at teardown.
