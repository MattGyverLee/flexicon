# APPROVED FOR POSTING -- lead ruling, cycle 8

**Status:** **POST.** The user delegated this decision to `/lex-lead`
("let the /lex-lead team decide"), so it is no longer held for their
approval. The draft's own stated precondition -- the cycle-8 Defect-4 gate
returning PASS -- is **satisfied**: PASS on every leg, no mutation left
NOT-KILLED (`cycle8-verification-D4-gate.md`), and the archivist audit of
`269b6a7` returned PASS on all seven clauses with 0 FAIL / 0 CONCERN
(`cycle8-archivist-269b6a7-audit.md`), both in this directory.

**Scope of the authorisation, exactly:** post the body below -- everything
under "Proposed comment body for issue #250" -- **verbatim**, as a comment
on flexicon#250, via `gh issue comment 250`. **Do NOT close #250. Do NOT
edit the issue body, title, or labels.** Nothing else on GitHub is
authorised by this ruling.

**Facts re-verified by the lead before authorising** (a public comment is
hard to retract, so none of this was taken on trust):

- `#250`, `#266` and `#267` all exist and are all OPEN, with titles
  matching how this comment describes them.
- The three-site frozen set is confirmed correct by cycle 8's tracked,
  hash-verified ratchet probe, whose failure message named the fourth site
  exactly as predicted. `PhonemeOperations.py:1336` was separately checked
  and is correctly EXCLUDED as a read path, not a resolution site.
- The Name/Description-vs-`BasicIPASymbol` asymmetry is confirmed **from
  the shipped source**, not inferred: `PhonemeOperations`'
  `ApplySyncableProperties` carries the comment "BasicIPASymbol and
  Features need dedicated handling; everything else (Name, Description, and
  any future plain scalars) goes through the base loop", and
  `__ApplyBasicIPASymbol` then builds its own `{ws.Id: ws.Handle}` map and
  runs its own resolution loop.
- No artifact anywhere claims D4-c is live-verified (gate leg 6, zero
  hits), and this comment does not either.

**Why post now rather than after T6-T9** (the hold argument, answered):
T6-T9 are feature-structure sync work on MSA/POS/Allomorph/Phoneme. They do
not touch either WS-resolution site, and they do not touch Defects 1-3. So
nothing in this comment is at risk of being invalidated by them, and the
"one comment now plus a correction later" scenario does not arise -- a
follow-up when `#266`/`#267` close is a normal additive comment, not a
correction. Against that, the asymmetry is in `main` **today**, undisclosed,
and anyone syncing phonemes right now is exposed to it with no way to learn
it from the issue. A campaign whose whole purpose is eliminating silent
partial coverage does not get to sit on a silent partial-coverage
disclosure for tidiness.

---

## Proposed comment body for issue #250

Defect 4 (case/separator normalization divergence between the
writing-system lookup helpers and the sync write path's
`{ws.Id: ws.Handle}` maps) is now fixed, independently of Defects 1-3.

**Defects 1-3 remain open. This issue must NOT be closed.** The fix lands
only the Defect-4 slice; the missing-Activate-API question, the
`Exists`/`Create` semantics, and the silent-vs-loud drop question are all
still unresolved and tracked here.

### Coverage boundary -- read before assuming this closes the whole symptom

The fix reaches `BaseOperations._apply_props_loop` only -- **1 of 3**
self-resolving writing-system resolution sites in the codebase. It does
**not** reach:

- `Grammar/PhonemeOperations.__ApplyBasicIPASymbol` -- tracked as **#266**
- `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC`
  loop -- tracked as **#267**

Both build their own exact-case map and run their own resolution loop
rather than delegating to the now-fixed helper.

This produces a surprising, worth-stating-plainly asymmetry: syncing a
phoneme whose writing-system id differs from the target only by case or
separator will now correctly save that phoneme's `Name` and `Description`
alts -- but will **still silently drop that same phoneme's `BasicIPASymbol`
alt**, with no warning either way. One object, one sync operation, two
different outcomes depending on which property is being written.

These are deliberately **two** issues rather than one, because they are
differently-sized efforts. **#266** is the genuine one-line substitution
against the new module-level `_resolve_ws_handle` helper. **#267** is a
correctness change, not a substitution: its loop creates and attaches the
`ICmTranslation` *before* any writing system resolves, so a naive one-line
fix would leave an orphaned translation with zero alts whenever the
ambiguity `FP_ParameterError` fires mid-loop. #267 therefore carries an
explicit regression-test requirement for that orphan -- the exact bug the
obvious fix would introduce.

Note for whoever picks either up: closing a site turns the three-site
resolution-ratchet test red **by design**. Update the frozen set in the
same commit; do not disable the test.

### Live vs. offline verification

Of the three ways this defect fires:

- **D4-a** (caller-supplied `ws_map` value is case/separator divergent) and
  **D4-b** (no `ws_map` at all, source and target writing systems
  legitimately disagree on subtag case) are both **proven live**: the drop
  measured on unfixed code, the save measured on fixed code, each re-read
  from the LCM after re-fetching the object.
- **D4-c** (separator divergence, e.g. `en_US` vs `en-US`) is covered
  **offline only**, against the real resolution function with fabricated
  dicts. It is not verified live because the sandbox project's only two
  active writing systems (`en`, `etu`) contain neither a `-` nor a `_` to
  flip, so the trigger cannot be constructed from real project state
  without fabricating a differently-shaped project, which is out of scope
  here. D4-c is **not** described as live-verified anywhere in this comment.

### Summary

- Fixed: writing-system id resolution in `_apply_props_loop` (the shared
  sync write path).
- Not fixed, tracked separately: the same resolution gap in
  `PhonemeOperations.__ApplyBasicIPASymbol` (**#266**) and
  `ExampleOperations.ApplySyncableProperties`'s `TranslationsOC` loop
  (**#267**).
- Not fixed, this issue's original scope: Defects 1-3 (activation,
  `Create` semantics, silent-drop diagnostics).

**#250 stays open.**
