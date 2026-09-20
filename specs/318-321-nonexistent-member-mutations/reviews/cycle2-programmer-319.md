# Cycle 2 -- programmer fix for issue #319 (Researchers/Participants hasattr no-ops)

**File changed:** `flexicon/code/Notebook/DataNotebookOperations.py`
(`GetResearchers`/`AddResearcher`/`RemoveResearcher` around former lines
1297/1351/1391, and `GetParticipants`/`AddParticipant`/`RemoveParticipant`
around former lines 1438/1488/1528).

**Tests added:**
- `tests/operations/test_issue319_participants_researchers.py` (mock-based,
  18 tests, all passing, no LCM required)
- `tests/operations/test_issue319_participants_researchers_live.py`
  (live-DB, `requires_live_project`; see "Live verification" below for why
  the six tests that call through the public API are marked `xfail`
  rather than passing outright)

**Scope:** only `DataNotebookOperations.py` and the two new test files.
No edits to `LexEntryOperations.py`, `LexSenseOperations.py`,
`OverlayOperations.py`, `exceptions.py`, or `CHANGELOG.md` (those are
owned by the concurrent programmer this cycle). No new exception types
were needed -- the six methods raise no new error classes.

## Grounding

Read first, per the task instructions:
`specs/318-321-nonexistent-member-mutations/reviews/cycle1-domain.md`

Confirmed from that review and re-verified live (see below):
- `record.Researchers` never existed on `IRnGenericRec`; the correct
  member is `record.ResearchersRC` (RC -- reference collection, target
  `ICmPerson`). Pure rename.
- `record.Participants` never existed either, and there is **no**
  equivalent rename target. The real graph is
  `IRnGenericRec --OC(ParticipantsOC)--> IRnRoledPartic --RC(ParticipantsRC)--> ICmPerson`,
  with `IRnRoledPartic.RoleRA` carrying an optional role
  (`ICmPossibility`). `IRnRoledPartic` has exactly two properties:
  `ParticipantsRC` and `RoleRA`.

## The fix

### Part A -- Researchers (safe rename)

All three `hasattr(record, "Researchers")` guards were deleted (per the
task instructions -- `ResearchersRC` always exists on `IRnGenericRec`, so
the guard was dead weight, not a fallback worth keeping) and replaced with
direct `record.ResearchersRC` usage:

```python
# GetResearchers
return list(record.ResearchersRC)

# AddResearcher
if person not in record.ResearchersRC:
    with self._TransactionCM("Add researcher to notebook record"):
        record.ResearchersRC.Add(person)

# RemoveResearcher
if person in record.ResearchersRC:
    with self._TransactionCM("Remove researcher from notebook record"):
        record.ResearchersRC.Remove(person)
```

This matches the existing `LocationsRC`/`SourcesRC` pattern already used
elsewhere in the same file. RC = reference collection: Add/Remove are
link/unlink only, never affecting the `ICmPerson`'s lifetime, consistent
with the pre-existing (accurate) docstrings ("the person object itself is
not deleted").

### Part B -- Participants (two-hop navigation, not a rename)

Implemented exactly per the team lead's decisions in the domain review,
no redesign:

**`GetParticipants`** -- kept the existing `list[ICmPerson]` signature
(no `role` parameter added, no return-type change). Iterates
`record.ParticipantsOC`, unions each group's `ParticipantsRC`, and
de-duplicates by `person.Hvo` (a person can appear in more than one role
group). Added an explicit docstring "LIMITATION" note stating that role
information (`RoleRA`) is not surfaced by this method, so the lossiness is
documented rather than silent.

**`AddParticipant`** -- targets `record.DefaultRoledParticipants` (the
read-only, no-specific-role group accessor). If it's `None` (no group
exists yet), a new one is created via `record.MakeDefaultRoledParticipant()`
before the person is linked into its `ParticipantsRC`. A duplicate-person
guard prevents re-adding. The transaction (`_TransactionCM`) wraps the
object-creation branch; a fast pre-check outside the transaction skips
opening one entirely when the person is already a member of an existing
default group, matching the file's existing style of not opening empty
transactions.

**`RemoveParticipant`** -- searches **every** `IRnRoledPartic` group in
`record.ParticipantsOC` (not just the default), collects every group that
contains the person, and unlinks the person from each group's
`ParticipantsRC`. It never calls `.Remove()` on `record.ParticipantsOC`
itself (the owning collection) -- doing so would delete the whole role
group (and everyone else's link with it), which is exactly the
destructive-vs-reference conflation the domain review flagged as the
critical risk in this part of the fix. If removing the person leaves a
group empty, that group is deliberately left in place (no opportunistic
cleanup of owned objects, per the team lead's instruction -- deleting
owned objects is out of scope for this fix).

### Docstrings

All six methods' docstrings were checked; `GetResearchers`/
`AddResearcher`/`RemoveResearcher` were already behaviorally accurate (the
old code just silently no-op'd instead of doing what the docstring
described) so only the code changed there. `GetParticipants`/
`AddParticipant`/`RemoveParticipant` docstrings were rewritten to describe
the real `ParticipantsOC`/`ParticipantsRC`/`DefaultRoledParticipants`/
`MakeDefaultRoledParticipant` graph, including the role-information
limitation on `GetParticipants` and the "never touches the owning
collection" note on `RemoveParticipant`.

## Tests

### Mock-based (`test_issue319_participants_researchers.py`) -- 18/18 passing

Deliberately effect-based, not shape-based (the task flagged that
"returns a list" assertions pass against the pre-fix broken code, which is
why #319 shipped in the first place):

- Researchers: pre/post membership assertions on `ResearchersRC` for
  add/remove/no-duplicate/remove-when-absent.
- `GetParticipants`: flattening across multiple groups, de-duplication of
  a person present in two groups, empty-record case.
- `AddParticipant` against a record with **no** existing group: asserts a
  group was actually created (`ParticipantsOC` count 0 -> 1) **and** the
  person is present on a fresh re-read -- the highest-risk path per the
  task brief.
- `AddParticipant` against a record that already has a group: asserts
  `ParticipantsOC` count is unchanged (no second group created).
- `RemoveParticipant`: asserts removal from all groups containing the
  person, asserts `ParticipantsOC` count is **unchanged** (proving a
  reference was unlinked, not a group destroyed), and asserts an
  emptied group is left in place rather than cleaned up.

Ran via `python -m pytest tests/operations/test_issue319_participants_researchers.py -v`
-> **18 passed**.

### Live-DB (`test_issue319_participants_researchers_live.py`)

Marked `pytestmark = pytest.mark.requires_live_project` throughout, per
instructions.

**What I found and how I handled the `MakeDefaultRoledParticipant`
transaction, concretely, against a real database:** this environment
does have a working live FieldWorks 9 + LCM 11 install with a real "Sena
3" project reachable via the repo's existing `flex_plugin.py` session
fixture (`initialize_flex_for_tests`, autouse). I used it to validate the
fix for real, not just against mocks. Specifically:

1. I first tried routing through the public API
   (`DataNotebook.Create()`/`Find()`/`GetAll()`) to build/locate a
   throwaway record, per the `test_locations_live.py` template. This
   uncovered **two unrelated, pre-existing bugs** independent of #319
   (details below) that make `Create()`/`GetAll()`/`Find()`
   non-functional against a real LCM 11 database today.
2. To route around that and still exercise the real fix live, the
   `temp_record` fixture builds an `IRnGenericRec` directly via
   `IRnGenericRecFactory.Create()` + `repos.Singleton.RecordsOC.Add()`
   (the correct real-LCM path, confirmed by reflecting on the live
   `IRnResearchNbkRepository` object: it exposes `.Singleton` ->
   `IRnResearchNbk`, which is what actually has `RecordsOC`, not the
   repository object itself).
3. With a real record and a real `ICmPerson` (via the already-correct
   `project.Person.Create()`) in hand, I ran the **exact same LCM
   operations the six fixed methods perform** directly against them,
   inside `writable_project.UndoableOperation(...)` blocks (mirroring
   `_TransactionCM`'s pattern), and asserted on fresh re-reads:
   - `record.ResearchersRC` starts empty, `Add()`/`Remove()` round-trip
     correctly.
   - `record.DefaultRoledParticipants` is `None` on a fresh record (not
     an empty collection -- confirming the domain review's claim that
     it's a true null-returning accessor, not a lazy-collection
     property).
   - `record.MakeDefaultRoledParticipant()` creates a group, which shows
     up in `record.ParticipantsOC` (count 0 -> 1) and becomes the new
     `DefaultRoledParticipants`.
   - A second add reuses that same group (`ParticipantsOC` count stays
     at 1).
   - Removing the person unlinks from `ParticipantsRC` without changing
     `ParticipantsOC`'s count (i.e. the group survives), confirming the
     "unlink a reference, never destroy the owning group" distinction
     the domain review flagged as the critical risk.

   All of the above passed on the first real run against Sena 3 (see
   transcript below). This is genuine live-DB evidence that the fix's
   LCM usage is correct, even though it was exercised via a throwaway
   probe script rather than the public API (for the reason in the next
   section).

   Transcript (abbreviated, `python -m pytest -s` on a throwaway probe
   that mirrors the six methods' bodies line-for-line):
   ```
   RESEARCHERS OK
   ADD PARTICIPANT (created group) OK
   REUSE GROUP OK
   REMOVE PARTICIPANT (group preserved) OK
   PASSED
   ```
   The throwaway probe script itself was not committed (scratch-only,
   deleted after use); the equivalent assertions are captured in
   `test_issue319_participants_researchers_live.py`'s docstrings and in
   the mock test suite's effect assertions, which encode the identical
   logic.

**What I could NOT verify end-to-end through the public API, and why
(two pre-existing, unrelated bugs, NOT fixed in this cycle):**

1. `DataNotebookOperations.Create()` calls `repos.RecordsOC.Add(record)`
   directly on the `IRnResearchNbkRepository` **service** object. On the
   real LCM 11 API the repository has no `RecordsOC` attribute -- that
   collection lives on `repos.Singleton.RecordsOC` (the singleton
   `IRnResearchNbk` container object). `GetAll()`/`Find()` have the
   mirror bug: they iterate `repos.AllInstances()`, which returns the
   singleton `IRnResearchNbk` container itself (`Count == 1`), not the
   `IRnGenericRec` records it owns. Confirmed live: `repos.AllInstances()`
   yielded exactly one object of type `IRnResearchNbk` (no `.Title`
   attribute), and `repos.RecordsOC` raised `AttributeError` directly
   against the real `RnResearchNbkRepository` type.
2. The private helper `__GetRecordObject` -- called by **every** public
   method in this class, including all six fixed for #319 -- does
   `self.project.project.GetObject(hvo)`. On the real LCM 11 API,
   `LcmCache` (what `self.project.project` actually is) has no
   `GetObject` method; it lives on
   `LcmCache.ServiceLocator.GetObject(hvo)` instead. Confirmed live:
   calling `AddParticipant`/`AddResearcher`/etc. through the public API
   with a real, valid, just-constructed live record raised
   `FP_ParameterError: ... 'LcmCache' object has no attribute
   'GetObject'` every time, regardless of which record or method was
   used.

   This second bug is the more serious one for #319's live-test
   ambitions: it means the six fixed methods (and literally every other
   method on `DataNotebookOperations`) cannot be exercised end-to-end
   through the public API against a real database today, independent of
   whether the #319 fix itself is correct. I chose **not** to fix this
   helper: it's outside the six methods this cycle assigned to me, a
   one-line change there would touch shared infrastructure used by
   dozens of unrelated methods (high collision risk with the concurrent
   programmer's files this cycle and with whatever issue eventually
   claims it), and the task instructions were explicit about staying
   within Part A / Part B's scope.

   Because of this, the six `xfail`-marked tests in
   `test_issue319_participants_researchers_live.py` that call through
   the public API (`GetResearchers`/`AddResearcher`/`RemoveResearcher`/
   `GetParticipants`/`AddParticipant`/`RemoveParticipant`) currently fail
   for that unrelated reason and are marked
   `@pytest.mark.xfail(reason="...", strict=False)` rather than left as
   red failures or silently skipped -- so CI keeps tracking them (they
   should flip to passing, and the xfail marker should then be removed,
   the moment `__GetRecordObject` is fixed by whoever picks that up).
   **Recommend filing this as its own follow-up issue** --
   `__GetRecordObject`'s `GetObject`/`ServiceLocator.GetObject` mismatch
   blocks all live use of `DataNotebookOperations`, and the
   `Create()`/`GetAll()`/`Find()` `RecordsOC`/`AllInstances()` mismatch
   is a second, independent blocker on top of it. Neither is mentioned
   in the #318-321 cycle-1 domain review, so they appear to be newly
   discovered here.

## Test run summary

```
python -m pytest tests/operations/test_issue319_participants_researchers.py -v
  -> 18 passed

python -m pytest tests/operations/test_issue319_participants_researchers_live.py -v
  -> 6 xfailed (documented, see above -- blocked by the unrelated
     __GetRecordObject bug, not by the #319 fix)

python -m pytest tests/operations/test_datanotebook_duplicate.py -v
  -> 8 passed (pre-existing regression suite for the same file,
     confirmed unaffected by this change)
```

No git commit or push was made, per instructions.
