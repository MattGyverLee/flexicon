# Issue #276 -- domain ruling (lex-domain, 2026-09-09)

Requested because #276 is blocked on a data-model decision, not on code.
Ruling reproduced in substance; full reasoning in the crew transcript.

## VERDICT

The owner's list-vs-entry intuition is directionally right, with the
terms tightened:

- **List level** -- "grammatical category" = **Part of Speech**,
  `IPartOfSpeech` in `LangProject.PartsOfSpeechOA.PossibilitiesOS`.
  A genuine `ICmPossibility` hierarchy; `SubPossibilitiesOS` works
  because `IPartOfSpeech` *is* a possibility subtype. Already owned by
  `POSOperations`.
- **Entry level** -- the FLEx sense field **"Grammatical Info."** is the
  **MSA**, `ILexSense.MorphoSyntaxAnalysisRA`, which *references* a POS
  (`IMoStemMsa.PartOfSpeechRA`) and *owns* a feature structure
  (`IMoStemMsa.MsFeaturesOA -> IFsFeatStruc`). "Verb: past" is that
  composite. Already owned by `MSAOperations` +
  `InflectionFeatureOperations`.

Correction to the owner's phrasing: the entry-level object is not "a
GramCat expanded with features." There is no LCM class for an expanded
category. The LCM noun is `IMoMorphSynAnalysis` -- it references a POS,
it is not a variant of one.

## Q1 -- list-vs-entry distinction correct? YES, as corrected above.

FLEx UI labels: Grammar area tool "Categories" for the POS list;
Lexicon sense field "Grammatical Info." for the MSA. **Flagged by
lex-domain as domain knowledge, not re-verified against a running
FieldWorks instance this session.** The LCM paths are code-verified.

## Q2 -- what should `project.GramCat` denote?

**Ruling: option (a)** -- a discoverability alias/delegate onto
`POSOperations`, mirroring the existing `Features -> InflectionFeatures`
precedent at `FLExProject.py:1682-1710`.

Reasoning:
- The already-committed docstrings `project.GramCat.Find("Verb")`
  (`FLExProject.py:1876,1880-1881`; `MSAOperations.py:141,145-146`) are
  unambiguously POS lookups feeding `MSA.CreateStem`/`CreateDerivAff`,
  which take `IPartOfSpeech`. Those examples only become true under
  reading (a). Strongest single piece of evidence.
- Working linguists' loose use of "grammatical category" means "what
  part of speech is this."
- The MSA composite is a sense-level fact *about* a category, not an
  inventory a user browses. There is no FLEx tool for CRUDing "the list
  of MSAs" -- MSAs are always per-sense. That asymmetry is why the list
  reading deserves a Grammar-area operations class and the entry reading
  belongs on the sense.

Rejected:
- **(b) GramCat = the MSA composite** -- would duplicate `MSAOperations`
  under a second name, or force GramCat into `Lexicon/`, contradicting
  its module placement and its own inventory-flavoured docstring.
- **(c) split/retire as irreducibly ambiguous** -- unnecessary once (a)
  is adopted; the ambiguity dissolves because POS owns the list, MSA
  owns the entry composite, and GramCat is only a spelling for the
  former.

Hierarchy surface (`recursive=`, `parent=`, `GetSubcategories`,
`GetParent`): retain the *capability*, delete GramCat's parallel broken
reimplementation, and serve it from `POSOperations`, which already gets
the hierarchy right.

> **Correction to the ruling, verified in code.** lex-domain wrote that
> `POSOperations` "presumably has its own `GetSubcategories`/`GetParent`/
> `parent=`." Verified: it has `GetSubcategories(recursive=)`,
> `AddSubcategory`, and `RemoveSubcategory`, but it has **no `GetParent`**,
> and its `Create(name, abbreviation, catalogSourceId=None)` has **no
> `parent=`**. So delegation is not purely subtractive: `GetParent` is a
> genuine capability that must be backfilled onto `POSOperations`, and
> `Create`'s signature genuinely differs. See spec.md section 4.

## Q3 -- is `IFsFeatStrucType` ever a "grammatical category"?

**No. The current collection is simply wrong, not under-documented.**

`IFsFeatStrucType` is a *structural template for feature structures* --
it classifies which features may co-occur inside an `IFsFeatStruc`
(canonical example in this repo's own docstrings: Bantu "tCommonAgr").
It sits one further abstraction removed from any category: an
`IFsFeatStruc` optionally points at a type via `TypeRA` to declare
conformance. The type carries no part-of-speech and no morphosyntactic
category semantics, and never appears in the sense's Grammatical Info.
field.

This is a wrong-collection bug, not the "Category 8" same-name-field
collision `CLAUDE.md` documents -- the correct collection sits one field
away on `LangProject` and was never consulted.

## Q4 -- hazard of the stray `IFsFeatStrucType`s already written

lex-domain's assessment, **flagged as domain knowledge; no orphan scan
was run**:

- FLEx will not crash or refuse to open such a project. LCM does not
  enforce back-references for this class.
- The stray type **does surface to the user**, as an unexplained entry
  in the Grammar > Features type list bearing whatever name was passed
  to `GramCat.Create` -- e.g. "1st person" sitting alongside
  "tCommonAgr", a domain-nonsensical juxtaposition.
- Harmless to analysis output (nothing reads it absent a `TypeRA`
  reference) but it corrupts the Features inventory *as presented*.
  Worse than untidy: it plants incoherent entries in a list a linguist
  will try to make sense of.

**Ruling: document, do not auto-migrate.** Stray types are
indistinguishable from ones legitimately created by
`InflectionFeatures.TypeCreate`, and one may since have been wired up
via `TypeRA`. Deciding needs a human looking at the specific project --
a `needs_human` call, not a blind script.

## Q5 -- should a caller reach features FROM a category?

**No -- only the reverse, and it already exists.** A single POS is used
across countless senses with countless feature combinations; there is no
canonical expansion belonging to the category. The expansion belongs to
the MSA instance.

Already covered: sense -> MSA -> POS (`MSAOperations`), sense -> MSA ->
features (`InflectionFeatureOperations` + `MSAOperations` sync).

Noted gap, **out of scope for #276**: `IPartOfSpeech` does own
`DefaultFeaturesOA` / `InherFeatValOA` (POS-level default/inherited
feature values used to pre-populate new MSAs of that category, per
`Shared/lcm_constants.py:126-129`). If `POSOperations` does not expose
these, that is a separate narrower gap -> follow-up issue.

**No new navigation helper is required by this ruling.**

## Explicitly unverified by lex-domain

- Exact FLEx 9.x UI tool label for the POS list ("Categories" vs a
  renamed variant) and the Grammatical Info. popup layout -- asserted
  from domain knowledge, not confirmed against a running FieldWorks
  instance or its help file.
- No orphan scan was run for Q4's severity claim.
