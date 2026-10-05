# QC Cycle 2 - commits 323009b (#631), 21eba10 (#630)

(Reviewer had no Write tool; saved verbatim by the main session.)

Score: 88/100. Recommend FIX ISSUES (minor). No P0/P1.

## P2
- InflectionFeatureOperations.py:277-278: duplicate `logger.debug("Created inflection class '%s'", name)`; remove one.
- MSAOperations.py:1757-1764: lost-field check for infl->deriv/unclassified lists FromProdRestrictRC. Lost for unclassified (no such field), but deriv HAS FromProdRestrictRC, so infl->deriv may preserve it -- check what ChangeAffixVariant actually copies; if it copies, warning is a false positive. Same for deriv->infl at 1784-1786 (infl has FromProdRestrictRC; only "To" is lost). Make warnings match actual transfer behaviour.

## P3
- InflectionFeatureOperations.py:258-261: when both `parent` and `pos` given, `pos` silently ignored (documented 214-216); mismatch could raise/warn per rule 6.
- InflectionFeatureOperations.py:2012-2062: missing ProdRestrictOA list created without name setup; verify live it reads back.
- InflectionFeatureOperations.py:2055: list-creation branch (ProdRestrictOA None) not exercised by a live test.
- MSAOperations.py:1041-1046: `__RCHasItems` swallows non-int `Count` (mock-tolerant production code).
- docs/API_ISSUES_CATEGORIZED.md:1449-1493: accurate; add the `parent`-wins note.

## Verified OK
- (a) Create requires pos/parent, sibling-scoped casefold duplicate check, ownership before Name set, `_EnsureWriteEnabled`. Delete resolves owner via cast_to_concrete and removes from correct collection. ExceptionFeatureCreate creates list when None inside the transaction.
- (b) `__ExceptionFeatureRC` per-ClassName casts correct; side validation correct; error messages name the real fields; docstrings match behaviour; writes call `_EnsureWriteEnabled`.
- (c) No leftover `__ProdRestrictRC` / `_PROD_RESTRICT_MSA_CLASSES` references; only no-pos `InflectionClassCreate(name)` callers are tests expecting the raise.
- (d) Commit subjects use "(issue 630)"/"(issue 631)"; bodies not inspected by reviewer.
