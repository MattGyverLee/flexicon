# Issue #377 (item 2) -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/377-scrdraft-type from origin/main

## Context

Issue #377 tracks three follow-ups from #352. PR #431 addresses item 3
(`sena3_sandbox` fail-loud under `FLEXLIBS_REQUIRE_LIVE=1`). Item 2 is
`ScrDraftOperations.Create(description, type=...)`: the `type` label was
accepted but never applied, so callers believe they selected
`consultant_check` or `back_translation` while LCM kept the default draft
type.

Live evidence in `specs/352-copyalternatives-audit/evidence/live-scrdraft.md`
already fixed Description handling; the unused `type` param was documented as
out of scope pending ScrDraftType exposure.

Contract baseline (`tests/contract/snapshots/liblcm_baseline.json`) shows
`IScrDraft.Type` is read/write `ScrDraftType` and `IScrDraftFactory.Create`
has a `(String, ScrDraftType)` overload.

## RULING (binding)

1. **Apply the `type` parameter** on every successful Create. Do not keep a
   silent no-op.
2. Map the three documented string labels to LCM enum members:
   `saved_version` -> `ScrDraftType.SavedVersion`,
   `consultant_check` -> `ScrDraftType.ConsultantCheck`,
   `back_translation` -> `ScrDraftType.BackTranslation`.
3. Unknown labels -> `FP_ParameterError` listing the allowed set.
4. Prefer `factory.Create(description, draft_type)` when the overload accepts
   two arguments; if pythonnet exposes only the one-arg overload, call
   `factory.Create(description)` then assign `new_draft.Type = draft_type`.
5. **Out of scope for this PR:** item 1 (Sena 3 `stem_name` set round-trip),
   item 3 (already in #431), new public type aliases beyond the three labels,
   live verification on this cloud host (no FieldWorks runtime).

## Verification plan

- Offline: source ratchet + unit test for unknown `type` label.
- Live (when LCM available): extend `test_352_scrdraft_live.py` with a
  consultant-check create/read-back of `Type` (optional follow-up).
