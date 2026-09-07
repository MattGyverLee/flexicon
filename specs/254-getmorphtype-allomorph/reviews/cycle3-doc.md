# Doc Agent Report -- cycle3-doc

**Date:** 2026-09-07
**Trigger:** issue #254 (dispatched task, two entries)

## What was added

Both entries added to `docs/API_ISSUES_CATEGORIZED.md`, inside **Category 8:
Same-name fields with different LCM types**, immediately before its
"Recommended pattern" closing subsection:

1. **New subsection "The `MorphRA` field (issue #254, RESOLVED)"** -- table
   of `MorphRA`/`MorphTypeRA` across `IWfiMorphBundle`, `IMoForm`,
   `ILexSense`; root-cause note (crash message, why the copy-paste looked
   safe); fix summary (`GetMorphType` now returns `IMoMorphType`,
   `SetMorphType` retired, `GetMorph`/`SetMorph` added).
2. **New subsection "Test-authoring trap: `MoStemAllomorph.MorphTypeRA` is
   not `None` after `Add`"** -- states the LCM auto-infer-`"root"` quirk,
   the required follow-up-transaction clear, cites
   `specs/254-getmorphtype-allomorph/evidence/live-cycle2-fix.md` item 4.

Also added one bullet to the existing "Why this matters" list crediting
issue #254 alongside #36/#39/#40, distinguishing its shape.

## Placement decision (entry 1)

Placed in Category 8, not a new category. CLAUDE.md points there, and while
CLAUDE.md's own framing calls it "wrong field entirely, under a name that is
correctly typed on neighbouring interfaces" (not classic same-name/
different-type), I judged it a close enough variant of the category's core
concern -- copying a working accessor pattern to the wrong field/type
without checking the target interface -- to keep the manifest's "one trap,
one place" discipline rather than fork a Category 12 for a single instance.
Labeled it explicitly as a variant in the entry text so a future reader
isn't confused by the shape difference.

## No manifest found

`docs/MANIFEST.md` does not exist in this repo. Per protocol this should be
bootstrapped, but the dispatched task was narrowly scoped ("Do NOT touch
CLAUDE.md, CHANGELOG.md, or any source file") and did not request manifest
work, so I proceeded without it. Flagging as an open follow-up for
`/lex-lead` or the user.

## Files touched

- `D:\Github\_Projects\_LEX\flexicon\docs\API_ISSUES_CATEGORIZED.md`

## Open follow-ups

- `docs/MANIFEST.md` does not exist -- bootstrap needed (separate task).
