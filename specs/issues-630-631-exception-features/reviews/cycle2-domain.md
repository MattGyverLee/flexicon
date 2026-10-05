# Cycle 2 Domain Review

(Reviewer had no Write tool; saved by the main session. Basis: MSAOperations.py code read; LCM mapping from model knowledge, no live read.)

## #630 MSA exception features: PASS (P2/P3 notes)
- Mapping correct: MoStemMsa.ProdRestrictRC; MoInflAffMsa.FromProdRestrictRC only; MoDerivAffMsa.From/ToProdRestrictRC; MoUnclassifiedAffixMsa has none.
- From/to matches the FLEx derivational-affix MSA editor ("From" = source category, "To" = derived category).
- Raising on write for unclassified / infl side="to" is correct: no storage field exists, so rule 6 does not apply.
- P2: make the READ path lenient -- GetExceptionFeatures on unclassified affix MSAs and on MoInflAffMsa side="to" should log a warning and return []. Keep Add/Remove raising.
- P3: document that the stem branch ignores `side`; optionally warn if side="to" is passed explicitly for a stem MSA.

## #631 inflection-class ownership: PASS (P2/P3 notes)
- Ownership correct: IPartOfSpeech.InflectionClassesOC, nested IMoInflClass.SubclassesOC; exception features are ICmPossibility under MorphologicalDataOA.ProdRestrictOA.
- Requiring pos= or parent= is right; a class cannot exist without an owner.
- P2: breaking change needs a migration-guide entry; error message should name both options; reject (or warn on) pos= + parent= where parent's POS conflicts with pos.
- P3: ExceptionFeature* on InflectionFeatures is discoverable enough; add "See also" cross-links; consider thin alias on project.MSA. Do not move.
- P3: use the FLEx UI term "exception features" consistently in docs (LCM: ProdRestrict).

Overall: both PASS; P2 items are not blockers.
