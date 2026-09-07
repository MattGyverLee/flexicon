# Live LCM evidence — B2 batch 11/11 (Lexicon)

**Task:** B2 batch 11 of 11 — bracket the final 84 unbracketed LCM mutation
sites, all in `flexicon/code/Lexicon/`, per decision D5.
**Project:** Target (scratch), via the `target_sandbox` fixture.
**Date:** 2026-08-16

---

## 1. Exact command

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_lexicon_brackets_live.py -m requires_live_project -q
```

**Result:** `20 passed, 3 xfailed in 12.88s`

## 2. run_mode

`tests/live_status.json`:

```
run_mode      : live
run_timestamp : 2026-08-15T22:37:40Z
lexicon tests recorded: 23  (20 pass, 3 xfail)
```

Classes exercised live: `AllomorphOperations`, `EtymologyOperations`,
`ExampleOperations`, `FLExProject`, `LexEntryOperations`,
`LexSenseOperations`, `PronunciationOperations`, `SemanticDomainOperations`.

`FLEXLIBS_REQUIRE_LIVE=1` was set, so a mock fallback, a locked Target or a
missing fixture would have been a hard failure rather than a silent
degradation. The run reached a real LCM cache — asserted directly by
`TestLexiconFixtureReachesLiveLCM::test_sandbox_opens_write_enabled`
(`writeEnabled is True` and a non-None underlying cache).

The imported package is this checkout, not the released one (the batch-9
load-path caveat):

```
flexicon pkg  : D:\Github\_Projects\_LEX\flexicon\flexicon\__init__.py
BaseOperations: D:\Github\_Projects\_LEX\flexicon\flexicon\code\BaseOperations.py
```

## 3. Pre-state / post-state, re-read from the LCM

Every assertion below re-queries through the Operations **getter** after the
write. Asserting on the value passed in would prove nothing.

### Round-trip (bracketed write reaches the LCM)

| Operation | pre-state | wrote | post-state (re-read) |
|---|---|---|---|
| `LexEntry.SetLexemeForm` | `TEST_lexform` | `TEST_changed` | `TEST_changed` |
| `LexEntry.SetCitationForm` | *(empty)* | `TEST_cit` | `TEST_cit` |
| `LexEntry.SetBibliography` | *(empty)* | `TEST_biblio` | `TEST_biblio` |
| `LexEntry.SetComment` | *(empty)* | `TEST_comment` | `TEST_comment` |
| `LexEntry.SetLiteralMeaning` | *(empty)* | `TEST_literal` | `TEST_literal` |
| `LexEntry.SetRestrictions` | *(empty)* | `TEST_restrict` | `TEST_restrict` |
| `LexEntry.SetSummaryDefinition` | *(empty)* | `TEST_summary` | `TEST_summary` |
| `Senses.SetGloss` | `TEST_gloss` | `TEST_regloss` | `TEST_regloss` |
| `Senses.SetDefinition` | *(empty)* | `TEST_definition` | `TEST_definition` |
| `Senses.SetBibliography` | *(empty)* | `TEST_sbiblio` | `TEST_sbiblio` |
| `Senses.SetGeneralNote` | *(empty)* | `TEST_sgeneral` | `TEST_sgeneral` |
| `Senses.SetRestrictions` | *(empty)* | `TEST_srestrict` | `TEST_srestrict` |
| `Examples.SetExample` | `TEST_sentence` | `TEST_revised` | `TEST_revised` |
| `Pronunciations.SetForm` | `TEST_form` | `TEST_revised` | `TEST_revised` |
| `Etymology.SetForm` | *(empty)* | `TEST_form` | `TEST_form` |
| `Etymology.SetGloss` | *(empty)* | `TEST_gloss` | `TEST_gloss` |
| `Etymology.SetComment` | *(empty)* | `TEST_comment` | `TEST_comment` |
| `Allomorphs.SetForm` | `TEST_form` | `TEST_revised` | `TEST_revised` |
| `SemanticDomains.SetName` | *(captured)* | `TEST_domain_name` | `TEST_domain_name`, then restored and re-read as the captured original |

### Validation-outside-the-bracket (D5's core property)

A rejected input must raise **without** opening an empty named undo entry,
leaving the stored value untouched.

| Operation | pre-state | rejected input | raised | post-state (re-read) |
|---|---|---|---|---|
| `LexEntry.SetLexemeForm` | `TEST_keepme` | `"   "` | `FP_ParameterError` | `TEST_keepme` (unchanged) |
| `Allomorphs.SetForm` | `TEST_keepme` | `"   "` | `FP_ParameterError` | `TEST_keepme` (unchanged) |

### No-op-guard-outside-the-bracket

A redundant Add/Remove against a reference collection must be a true no-op,
not an empty named undo entry.

`Senses.AddSemanticDomain` / `RemoveSemanticDomain`, counts re-read via
`GetSemanticDomains` after each call:

```
0  ->  Add        -> 1
1  ->  Add (dup)  -> 1   (redundant add did not change the collection)
1  ->  Remove     -> 0
0  ->  Remove (dup) -> 0 (redundant remove did not change the collection)
```

### Delete round-trip (bracketed Remove really detaches)

| Operation | pre-count | after Create | after Delete |
|---|---|---|---|
| `LexEntry.Delete` | N | N+1 | N |
| `Senses.Delete` | N | N+1 | N |
| `Examples.Delete` | N | N+1 | N |
| `Pronunciations.Delete` | N | N+1 | N |
| `Etymology.Delete` | N | N+1 | N |

All test objects are `TEST_`-prefixed and removed in `finally:` blocks;
`SemanticDomains.SetName` is the one test touching pre-existing data and uses
capture-and-restore. Target is left clean.

## 4. Pre-existing bugs surfaced (NOT caused by batch 11)

Three methods are unreachable or broken on a live project. All three fail
**before** the bracket is entered (or write to a field that does not exist),
so they are unrelated to B2; all are recorded as `xfail(strict=True)` in
`tests/operations/test_lexicon_brackets_live.py` so they cannot silently
disappear, and all were deliberately left unfixed to keep batch 11
mechanical — the same call made for batch 9's four Notebook bugs.

1. **`ExampleOperations.SetLiteralTranslation` / `GetLiteralTranslation`** —
   both call `self.__WSHandleAnalysis(...)`, which does not exist on
   `ExampleOperations` (it defines only `__WSHandle` and `__WSHandleVern`).
   Raises `AttributeError` on any live project. Present at HEAD lines
   1491/1520, i.e. before this batch.

2. **`EtymologyOperations.SetSource` / `GetSource`** — `ILexEtymology` has no
   `Source` attribute at all; raises `AttributeError`. This is CLAUDE.md
   "Category 8" territory (same-name fields with different LCM types across
   interfaces — `Source` is `ITsString` on `ILexSense`).

3. **`EtymologyOperations.SetLanguage`** — the worst of the three, because it
   does **not** raise. `ILexEtymology` has no `LanguageRA` field (the
   interface exposes `LanguageNotes`), but pythonnet accepts
   `etymology.LanguageRA = language` as a plain Python attribute on the
   wrapper. Probed directly:

   ```
   hasattr LanguageRA before      : False
   SetLanguage(None) did not raise
   hasattr LanguageRA after       : True     <- Python-side attribute only
   fresh LCM handle for same Hvo  : False    <- the write never landed
   SetLanguage(<obj>) did not raise either
   ```

   Silent data loss. The bracket around it opens and commits correctly; the
   write inside it simply goes nowhere.

Consequence for this batch: the brackets on these three sites are correct and
`grep`-auditable, but could only be verified statically and by the scanner,
not live.

## 5. Pass/fail

**PASS** — batch 11's brackets are verified live on the Target project.
`run_mode` is `live`, 20 tests passed with every assertion re-read from the
LCM, and the three xfails are documented pre-existing defects unrelated to
the bracketing.

Scanner: **84 -> 0**. Ratchet baseline: **84 -> 0**. The B2 sweep is complete
(295 -> 0 across 11 batches).
