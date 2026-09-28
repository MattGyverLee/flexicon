# Domain Expert RULING — name-field whitespace identity (cycle 1)

**Date:** 2026-09-07
**Status:** DECIDING VERDICT, not advisory.
**Authority:** The project owner directed *"Let's do what is best for the user, /lex-domain can decide"*, placing lex-lead's C3 ruling under this agent's authority. Persisted verbatim by the main session (lex-domain has no Write tool).

## Domain Expert Ruling

**Grounding checked in source:** `TextOperations.py:118,134-135` documents `Create`'s uniqueness ("Must be unique and non-empty" / raises `FP_ParameterError` "if a text with this name already exists") as a **library-invented policy** — `IText.Name` carries no such constraint in the LCM model itself, and FLEx's own Texts & Words organizer enforces zero title uniqueness (duplicate "Untitled Text," re-imported duplicates from revision workflows, and repeated Scripture-portion titles across drafts are all routine, unremarked-on FLEx states). `AnthropologyOperations.py:252,265,269` documents the same invented-uniqueness shape for OCM/CmAnthroItem names. `CheckOperations.py`'s "check type" is this library's own concept layered on `ICmPossibilityList`, not a native FLEx-UI list a user browses.

**Q1.** FLEx name-entry boxes for these fields are plain single-line `ITsString` editors; nothing in the LCM model or in FLEx's UI code trims on commit, and C5's own finding (`AppendSentence` manufacturing `". "` and storing it verbatim) confirms FLEx's general philosophy is "store what was typed," not silent reformatting. For text titles specifically, FLEx enforces **no** uniqueness at all, whitespace-differing or otherwise — two items differing only by a trailing space absolutely can, and functionally already do, coexist in real FLEx projects. That argues (ii) is *more FLEx-faithful* in the narrow sense of "reproduces the FLEx model's total permissiveness" — but it also means the uniqueness guard being debated isn't a FLEx invariant to preserve either way; it's flexicon's own value-add.

**Q2.** Text titles: yes — sort-order padding hacks and import artifacts (Paratext `\h`, Word/PDF copy-paste, Toolbox migration) genuinely introduce meaningful-to-the-user padding. OCM/Anthropology names: rare — the standard catalog carries no such convention, though user-added subitems could inherit copy-paste whitespace. Check-type names: essentially never — these are ad hoc user labels for a library feature with no whitespace convention at all. So the "meaningful whitespace" argument is real but strictly weaker and rarer for names than for paragraph content.

**Q3.** C10's distinction is sound at the level it was making it: nothing in the LCM name-field type or in any name-writer *manufactures* whitespace as structure the way `AppendSentence` manufactures `". "`. The closest analog — user sort-order hacks — is user-imposed convention, not FLEx/LCM-generated structure, so it doesn't rise to C5's level and doesn't overturn C10. It does mean C10 slightly understates *why* raw-byte persistence still matters for names (sort hacks, import fidelity), but that's an argument for persisting raw bytes, not for weakening the separate dedup question — persist-vs-strip and identity-for-comparison are properly separable, which is exactly what C10/lex-lead's ruling does.

**Q4.** (i) serves the user better. A guard the user relies on ("`Exists` returned False, so `Create` is safe") that can be silently defeated by one invisible character is a false-confidence footgun, worse than no guard at all — precisely the population most exposed to it (import/round-trip users) is the population most likely to already have stray whitespace. (i) surfaces the collision as an actionable `FP_ParameterError` naming the existing record; (ii) produces two rows in a FLEx list/tree that render pixel-identical, with no FLEx affordance to distinguish them.

**Q5. ACCEPTED.** Persist the caller's raw bytes; strip both sides at every uniqueness comparison. This does not redefine what a name *is* — the model still stores exactly what the caller typed. It defines what flexicon's own, library-invented uniqueness guard treats as a collision, and it should treat whitespace as insignificant for that purpose because the guard exists to protect users from accidental duplication, and an invisible-character bypass defeats that entire purpose while serving no compensating value — FLEx itself enforces nothing here, so there is no native semantic being overridden.

**Q6.** Raise `FP_ParameterError`, matching the four #242 content writers (`spec.md` C8's binding shape), for both `str` and non-`str`-coerced branches. A name is a display label with no legitimate all-whitespace state in any FLEx list/tree rendering — unlike paragraph content, there is no structural or transient-editing argument for an invisible name, only the confusing `<blank row>` UI state this campaign exists to eliminate. No FLEx-specific reason favors leniency here.

---

## Consequences for the contract (recorded by the main session)

- **lex-lead's C3 STANDS**, now carrying the owner's own "best for the user" standard and an independent FLEx-domain basis.
- **New supporting fact for the record:** the uniqueness guard at all three families is a **flexicon invention**, not a FLEx/LCM invariant. This strengthens C3 rather than weakening it — the ruling decides what *our* guard means, and overrides no native FLEx semantic.
- **C10's content-vs-name distinction survives**, with one correction: it understates why raw-byte persistence matters for names (sort-order hacks, Paratext `\h` / Toolbox / copy-paste import fidelity). That is an argument for the persist half, not against the dedup half.
- **Q6 answers the whitespace-only-name question**, which lex-lead's C7 had left implied: `FP_ParameterError`, on both the `str` and non-`str` branches, matching #242's four content writers.
