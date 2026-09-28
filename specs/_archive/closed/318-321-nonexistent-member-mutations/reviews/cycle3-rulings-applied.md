# Cycle 3 -- team-lead rulings applied

## Ruling 1: overlay membership guard downgraded (#320)

`flexicon/code/Lists/OverlayOperations.py::AddElement` no longer raises
`FP_ParameterError` when the element is not a member of
`overlay.PossListRA`'s list. The check remains; on failure it now emits
`logger.warning(...)` naming the HVO and stating the add proceeds anyway,
then proceeds to add. A comment at the guard cites the live evidence
(`evidence/live-cycle2-business-rules.md`: LCM raised nothing and
persisted HVO 34, 859->860), states that "LCM allows it" and "FLEx
accepts it" are untested-separately claims, and explains this does not
conflict with the Original Author's Q4 ruling (that ruling covers
no-ops; here the add genuinely succeeds).

`tests/operations/test_issue320_overlay_elements.py::test_add_element_not_member_of_bound_list_raises`
renamed to `..._warns_and_proceeds`; it now asserts the element persists
in `PossItemsRC` and that a "not a member" warning was logged via
`caplog`, instead of `pytest.raises`. Module docstring updated to match.
11/11 tests in that file pass.

## Ruling 2: #319 xfails made strict (`tests/operations/test_issue319_participants_researchers_live.py`)

All six public-API xfails (`TestResearchersLive` x2,
`TestParticipantsLive` x4) changed from `strict=False` to `strict=True`,
with reason strings naming both root causes: `__GetRecordObject` calling
`LcmCache.GetObject()` (needs `.ServiceLocator.GetObject`), and
`Create()`/`GetAll()`/`Find()`'s repository-vs-`Singleton` /
`AllInstances()`-returns-container mismatch. Reasons state both are out
of scope for #318-321, awaiting a separate issue. Neither bug was fixed.
6/6 xfailed (unchanged pass/fail shape, now strict).

## Full suite run

`python -m pytest -q`: **31 failed, 2629 passed, 56 skipped, 8 xfailed**
(126s).

Of the 31 failures, 2 are the documented pre-existing, unrelated
failures: `test_issue266_phoneme_ws_resolution.py::...test_fresh_index_cache_per_apply_call`
and `test_issue267_translations_ws_resolution.py::...test_fresh_index_cache_per_apply_call`.
Not fixed, not caused by this work, and deterministic (not flaky), per
instructions.

The remaining 29 failures (`test_duplicate_operations.py` x7,
`test_natural_classes.py` x8, `test_phon_features.py` x8,
`test_phon_rules.py` x4, `test_phonemes.py` x2) are **not** in either
file this ruling touched (`OverlayOperations.py`,
`test_issue320_overlay_elements.py`,
`test_issue319_participants_researchers_live.py`) and none of those
failing test modules reference `OverlayOperations` or
`DataNotebookOperations` (grep-confirmed). `git status`/`git diff`
at the time of this run show other files concurrently modified by the
main session (`LexEntryOperations.py`, `LexSenseOperations.py`,
`exceptions.py`, `lcm_casting.py`) that this ruling never touched --
these 29 failures track that in-flight, concurrently-edited state, not
the two rulings applied here.
