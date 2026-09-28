# QC Report — Issue #232 `GetPartOfSpeechObject`

**Cycle:** 3
**Agent:** lex-qc
**Date:** 2026-08-13

> Persisted by the orchestrator: `lex-qc` has only Read/Grep/Glob and no Write tool,
> so it returned this body inline. Content is verbatim from the agent apart from this note.

**Summary:** No P0s. Source diff is clean and follows CLAUDE.md logging conventions. The new
AST-exec test harness is sound (fails loudly on rename/move/delete, exercises the real current
source each run) but its "matches test_agent_version_unicode.py" claim overstates the precedent,
and the new `_POS_BEARING_MSA_CLASSES` frozenset duplicates a hardcoded list that already lives
in `lcm_casting.py` with no coupling test.

## P1 Issues

1. **DRY / drift risk between two hardcoded MSA-type lists** —
   `flexicon/code/Lexicon/LexSenseOperations.py:59-61` (`_POS_BEARING_MSA_CLASSES`) duplicates,
   string-for-string, the four `ClassName` branches already hardcoded in `get_pos_from_msa`'s
   if/elif chain at `flexicon/code/lcm_casting.py:411-434`. Nothing enforces the two stay in
   sync. If `lcm_casting.py` ever gains a 5th supported MSA subtype, `GetPartOfSpeechObject`
   will incorrectly log a warning and return `None` even though `get_pos_from_msa` could have
   resolved it correctly. `test_lexsense_getpos_object.py:134-150` only pins the frozenset's
   *own* value — it doesn't cross-check against `lcm_casting.py`. Recommend exporting the class
   list from `lcm_casting.py` as the single source of truth (or adding a cross-file coupling
   test) rather than re-literalizing it.

2. **Misleading precedent citation for the test harness** —
   `tests/test_lexsense_getpos_object.py:13-20` says the strategy is "static (AST based)...
   matching test_agent_version_unicode.py." Verified: `test_agent_version_unicode.py` (and
   `test_wfianalysis_agent_import.py`) do *only* static AST assertions — no `exec()`/`compile()`
   of a reconstructed module. Grepping all of `tests/` confirms the exec-based synthetic-module
   technique here is unprecedented elsewhere in the suite. It is well-built (loud `pytest.fail`
   on missing class/method/constant, re-reads source per test, correct `self.__X` name-mangling),
   and it plausibly exists to dodge the `sys.modules["SIL"]=MagicMock()` poisoning problem
   `conftest.py:41-52` explicitly documents as the reason three other wrapper test files were
   disabled — but that rationale isn't stated in the file. Add a comment naming that real
   constraint so the next engineer doesn't mistake this for boilerplate to copy-paste, or
   distrust it as gratuitously complex.

## P2 Issues

- None beyond the above; no magic numbers, no bare excepts, logging uses lazy `%s`/`%r`
  formatting correctly.

## Source Diff (`LexSenseOperations.py:1192-1209`)

Clean: `getattr(msa, "ClassName", None)` guards missing attribute; `getattr(sense, "Hvo", None)`
guards the log call too; early-return structure is readable; no exception swallowing beyond the
documented "None means no MSA" contract.

**Score: 88/100** — no blocking defects, code ships as-is; the two P1s are
pre-existing-debt-shaped (not caused by this diff, but this diff is the moment to fix the first
one before it compounds).

**Recommendation: FIX ISSUES** (P1 #1 is cheap to address now; P1 #2 is a one-line comment).

---

## Orchestrator verification note

P1 #1 independently confirmed against source. `lcm_casting.py:411-434` is a literal
`if class_name == "MoStemMsa": ... elif class_name == "MoDerivAffMsa": ...` chain over exactly
the four names now re-literalized in the frozenset. The drift risk is real, and it is the same
defect shape as #232 itself: LCM type knowledge encoded in two places that can diverge silently.
