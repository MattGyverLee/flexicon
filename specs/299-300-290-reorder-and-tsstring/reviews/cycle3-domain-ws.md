# Domain Expert Ruling -- issue #290, `ws=` parameter (cycle 3)

**Date:** 2026-09-10
**Reviewer:** Domain Expert Agent
**Score:** N/A (ruling, not a scored review)
**Status:** RULING ISSUED

## House precedent: LexSenseOperations

`GetSource`/`GetScientificName`/`GetImportResidue`
(`flexicon/code/Lexicon/LexSenseOperations.py:3163,3190,3227`) take **no
`ws`/`wsHandle` parameter at all** -- signature is `(self, sense_or_hvo)`.
Only the paired setters (`SetSource`/`SetScientificName`/
`SetImportResidue`, same file :3170/3197/3234) take `wsHandle=None`, each
documented identically: it "tags the WS metadata on the single TsString
run -- it does **not** pick a per-WS slot." That is the house convention
for bare-`ITsString` fields, and `docs/API_ISSUES_CATEGORIZED.md`
Category 8 names this exact class of bug (same field name, different LCM
type) without prescribing a getter-signature rule -- the actual rule
lives in the Lexicon code, and #290 should read it from there.

## Rulings

**1. Inert getter `ws=`:** Remove it, not deprecate-then-remove. The
precedent has no such parameter, and live evidence
(`evidence/live-290-reflection.md` Q3) shows `GetLabel`/`GetNotes`
crashed with `AttributeError` **unconditionally** before this fix --
default `ws` included. No caller ever ran a working invocation with any
`ws` value, so there is no live behavior to preserve across a
deprecation window. Match `GetSource`'s signature: `GetLabel(self,
row_or_hvo)` / `GetNotes(self, row_or_hvo)`.

**2. Setter `ws=`:** Keep, unchanged. It matches `SetSource`'s
`wsHandle=None` exactly -- same real-but-narrower meaning (tags the run,
doesn't select a slot), already documented that way in the current
docstrings. No change needed.

**3. CLAUDE.md violation:** Yes, on the getters -- but the sharper hit is
Rule 1 (hide LCM complexity), not Rule 5. A `ws=` a caller can pass on
`GetLabel` implies a per-WS slot that doesn't exist on
`IConstChartRow.Label`; that's a phantom multistring capability leaking
into the domain user's mental model, not a caller-managed correctness
flag. Rule 5 applies more cleanly to the setters, and there it's already
satisfied: setter `ws` is call-site-dependent (which WS tags the run)
exactly like the sanctioned `normalize_match_key(casefold=...)` example.

**4. Blocking or follow-up:** Follow-up, not a blocker. The core #290 fix
(routing all six sites through `_MakeTsString`/`_ReadTsString`) resolves
a live crash and should ship now. The getter-signature cleanup is API
polish with zero live-behavior risk either way; cycle 2 already deferred
it correctly. Open a follow-up issue: "Remove inert `ws=` from
`GetLabel`/`GetNotes`, matching `LexSenseOperations.GetSource` et al."

---
**Reviewed By:** Domain Expert Agent
