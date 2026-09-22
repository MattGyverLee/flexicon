# T8 Verification -- Issue #326: Phonological Wrapper Members

Reviewer: lex-verification. Worktree `C:/Github/flexicon-326`. No production
code changed; no commit made.

## Verdict: **PASS**

## Scope

Independent live LCM verification of the final tree (T5 implement + T6
simplify), covering `PhonologicalContext.segment`,
`PhonologicalContext.natural_class`, and
`PhonologicalRule.has_metathesis_parts`/`metathesis_parts`.

## What was checked

1. Re-read T5-programmer.md, T6-simplify.md, T1's live reflection evidence,
   and `tests/operations/test_phonological_wrappers_live.py`.
2. Re-ran the offline suite (`python -m pytest -m "not requires_live_project" -q`)
   -- `2043 passed`, same 5 pre-existing failures as T5/T6, no new failures.
3. Independently re-ran T5's required live smoke test
   (`test_phonological_wrappers_live.py`, `requires_live_project`) --
   `3 passed`, `run_mode: live` confirmed in `tests/live_status.json`.
4. Wrote and ran a second, independent live test
   (`tests/operations/test_issue326_t8_verification_live.py`, evidence-only,
   not committed) that re-queries `.Name`/`class_type` off the objects the
   wrapper properties return -- not the values passed in -- via
   `best_analysis_text()`. `2 passed`, `run_mode: live` re-confirmed.
5. Confirmed the Sena 3 fixture gap reported by T1 (`.fwdata` fails to open,
   `.fwbackup`/`sena3_sandbox` both unusable in this worktree) and applied
   the task's sanctioned fallback: `target_sandbox` to prove a real
   write-enabled LCM session, plus read-only installed FLEx projects for the
   actual read-back assertions.

## Result

Both required commands pass; `run_mode: live` in both live runs (not mock).
Pre-state (T1): `SegmentRA`/`NaturalClassRA`/`LeftPartOfMetathesisOS`/
`RightPartOfMetathesisOS` confirmed absent on live LCM instances. Post-state
(T8, re-queried): `FeatureStructureRA` resolves to real `PhPhoneme` /
`PhNCSegments` objects (one with a non-empty re-queried name, `"C:A"`);
`metathesis_parts` slices `StrucDescOS` into real, correctly-typed
`PhSimpleContextSeg` parts at the switch-index boundaries reported by the
concrete `IPhMetathesisRule` object. No new offline regressions. No writes
made anywhere.

Full evidence: `specs/326-phonological-wrapper-members/evidence/live-T8.md`

## Open items handed to whoever closes out #326

- T5's open question re: Sena 3 fallback is resolved here -- fallback
  accepted as sufficient per task instructions; a follow-up to restore/copy
  a working Sena 3 `.fwdata`/`.fwbackup` for this worktree remains a
  separate, non-blocking environmental cleanup item.
- `tests/operations/test_issue326_t8_verification_live.py` is an
  evidence-only scratch file added by this verification pass, not part of
  the change under review; delete or fold into the permanent live suite at
  the implementer/lead's discretion before merge.
