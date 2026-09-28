# Issue #363 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/363-confidence-phantom from origin/main

## RULING (binding)

`liblcm_baseline.json` confirms **`ConfidenceRA` is absent** from
`IWfiAnalysis` and `IWfiGloss`. Research notebook records (`IRnGenericRec`)
**do** expose `ConfidenceRA` (typed `ICmPossibility`).

The repository scans in `GetAnalysesWithConfidence` /
`GetGlossesWithConfidence` used phantom `hasattr(..., "ConfidenceRA")` on
wordform types, so both queries were always empty (silent failure).

**Correct behaviour (issue #363 scope):**

1. **GetAnalysesWithConfidence** -- Stop scanning `IWfiAnalysisRepository`.
   Enumerate research notebook records via `DataNotebook.GetAll()` and
   match `record.ConfidenceRA.Hvo` to the requested level. Return
   `IRnGenericRec` instances (update docstrings: these are notebook
   records, not interlinear `IWfiAnalysis` objects). The public method
   name is retained to avoid a breaking rename in this PR.
2. **GetGlossesWithConfidence** -- `IWfiGloss` has no confidence field.
   Raise `FP_ParameterError` with an explicit message instead of returning
   an empty list.

**Out of scope:** Renaming `GetAnalysesWithConfidence`, fixing
`DataNotebookOperations.GetConfidence` (`Confidence` vs `ConfidenceRA`),
or confidence on interlinear approval (`EvaluationsRC`).

## Verification plan

- Offline: source ratchets on both methods; drop #272 seam inventory rows
  that required a repository `GetService` call in the old implementation.
- Live: read-only call to `GetAnalysesWithConfidence` on Sena 3 when LCM is
  available (`requires_live_project`).
