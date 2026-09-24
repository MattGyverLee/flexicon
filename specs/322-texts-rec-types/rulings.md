# Issue #322 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/322-texts-rec-types from origin/main

## RULING (binding)

Live reflection and `liblcm_baseline.json` confirm:

- **`IRnGenericRec`** has **`TextRA`** (single atomic reference), not `TextsRC`.
- **`IRnResearchNbk`** (project `ResearchNotebookOA`) owns **`RecTypesOA`**;
  **`ILangProject`** has no `RecTypesOA`.
- **`ICmAnthroItem`** has no `TextsRC` or other text-link collection.

**Correct behaviour (issue #322 scope):**

1. **`DataNotebookOperations.GetAllRecordTypes`** -- Read
   `self.project.lp.ResearchNotebookOA.RecTypesOA.PossibilitiesOS`
   (same cast pattern as today). Do not guard on `lp.RecTypesOA`.
2. **`DataNotebookOperations` text link/read** -- Use `TextRA` for
   `GetTexts`, `LinkToText`, and `UnlinkFromText`. One linked text per
   record; replacing an existing link is allowed.
3. **`AnthropologyOperations` text link API** -- `AddText` / `RemoveText`
   must **not** silently no-op. Raise `FP_ParameterError` with an explicit
   message that LCM provides no text-link surface on `ICmAnthroItem`.
   Read paths (`GetTexts`, `GetTextCount`, `GetItemsForText`) may return
   empty results without pretending a link exists.

**Out of scope:** Multi-text collections on notebook records (no LCM member),
anthropology text linking via another type, or re-basing `AgentOperations` /
possibility inheritance (#54).

## Verification plan

- Offline: source ratchets on the three areas above; extend member-truth
  sweep expectations where needed.
- Live: optional read/write on `target_sandbox` for record type enumeration
  and `TextRA` round-trip when LCM is available.
