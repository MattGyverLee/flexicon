# Cycle 3 programmer report (issues 630 / 631)

## Changes
1. InflectionFeatureOperations.py: removed duplicate logger.debug in InflectionClassCreate.
2. MSAOperations.py ChangeAffixVariant: now snapshots FromProdRestrictRC before creation and copies it
   infl<->deriv (new MSA). Lost warnings match reality: infl->unclassified: From; deriv->infl: To only;
   deriv->unclassified: From+To; infl->deriv: none. Docstring Notes updated.
3. MSAOperations.GetExceptionFeatures: unclassified, and infl with side="to", log warning and return [];
   Add/Remove still raise. Docstring updated (incl. stem MSAs ignore side). Invalid side still raises.
4. InflectionClassCreate: warns (naming pos= and parent= Hvos) when parent's owning POS is not pos; parent wins.
   Neither-given error names pos= and parent=.
5. Docs: CHANGELOG.md [Unreleased]; docs/MIGRATION_GUIDE.md (new section at end, before/after code);
   docs/API_ISSUES_CATEGORIZED.md (parent wins, lenient read, ChangeAffixVariant behaviour).
6. Tests: offline test_574_msa_exception_features.py (lenient reads, 6 ChangeAffixVariant tests),
   test_issue631_inflection_class_store.py (3 new); live 630 (unclassified/side=to read, ProdRestrictOA=None create,
   3 ChangeAffixVariant cases), live 631 (mismatch warning, neither-given message).
   Evidence: evidence/live-630.md, live-631.md.

Line numbers: see `git show` on the commits (file edits are localized to the functions named above).

## Results
- Offline: `python -m pytest -m "not requires_live_project" -q` -> 3719 passed, 1174 deselected.
- Live: both live files, FLEXLIBS_REQUIRE_LIVE=1 -> 15 passed. tests/live_status.json run_mode: "live".
