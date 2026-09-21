# HANDOFF -- CopyAlternatives misuse audit (#352) / OcmCodes.None (#348, #262)

**Date:** 2026-09-21
**Session's chosen route:** (b) -- clear the SemanticDomainOperations blocker *and* live-verify it.
**Authored by:** flextools session; see `flextools_get_session_history` for the exact operations.

## TL;DR for the next session

Status: **FIX APPLIED IN SOURCE, EDITABLE-INSTALLED, READ-PATH LIVE-PROVEN.**
The one unfinished piece is a **write** live-proof, and it is blocked **only** by a
runtime-restart dependency, not by any remaining code defect.

---

## 1. What the bug was (verified live, not assumed)

Read-back and export reflection on `ICmSemanticDomain` was treating two fields as
MultiUnicode multistrings when they are not:

| Field | Real LCM type | Old (wrong) site | Live symptom |
|-------|---------------|------------------|--------------|
| `OcmCodes` | **scalar `String`** | `SemanticDomainOperations.GetOcmCodes` (`domain.OcmCodes.get_String(wsHandle)`) | `AttributeError: 'str' object has no attribute 'get_String'` |
| `Questions` | **owning sequence** `QuestionsOS` of `ICmDomainQ` (each a MultiUnicode `Question`) | `GetQuestions` + `Duplicate` deep-copy (`CopyAlternatives` on the owning seq as if scalar multistring) | structural/`CopyAlternatives` `AttributeError` |

The `CopyAlternatives` misuse family in `SemanticDomainOperations.py` is the
"pattern audit" item #352 flagged; the `OcmCodes is None` face is #348/#262.

## 2. The fix (in repo source, on `main` working tree)

`flexicon/code/Lexicon/SemanticDomainOperations.py`:
- `OcmCodes` is a **scalar String** on `ICmSemanticDomain` (cast target
  `ICmSemanticDomain`, no writing-system loop). Read `domain.OcmCodes or ""`;
  duplicate assign `duplicate.OcmCodes = source.OcmCodes or ""`.
- `Questions`/`QuestionsOS` is an **owning sequence of `ICmDomainQ`**, reached via
  `ICmDomainQFactory` (verified: `ICmDomainQ` / `ICmDomainQFactory` resolve from
  `SIL.LCModel`, factory category). Deep-dup copies each `domain_q` via the
  factory's owning seq `QuestionsOS`, then `new_q.Question.CopyAlternatives(domain_q.Question)`.
- Removed the writing-system loops over these two scalar/owning-seq fields in
  `GetOcmCodes`/`GetQuestions`/`GetOcmCodes`-in-`_Copy`/`_Copy alternatives` sections.

## 3. What was installed (so the runtime picks up the fix)

The flextools-mcp runner imports flexicon from **its own venv**, not this checkout.
That venv had the stale prebuilt **pyflexicon 4.8.0**. It was switched to an
**editable local install of this repo**:

```
uv pip install --python <flextools-mcp venv python> -e C:\Github\flexicon
```

Now `pyflexicon==4.9.0 (from file:///C:/Github/flexicon)` and `flexicon.__file__`
resolves into the repo. **A fresh interpreter imports the fixed source.**
See `evidence/live-proof.md` for the machine-checkable output.

## 4. LIVE-PROVEN (read path) -- Target project, real LCM

A read-only probe over real semantic domains on the `Target` project succeeded:
scalar `OcmCodes` readback plus `QuestionsOS` owning-seq iteration, no
`AttributeError`. Exact command + run_mode + probe output: see
`evidence/live-proof.md`.

## 5. THE ONE REMAINING STEP (write proof) -- needs a server restart

The deep-duplicate **write** round-trip (duplicate a domain, read
`QuestionsOS.size`/`OcmCodes` back, remove the `TEST_` duplicate) is NOT yet
flowing live, for one reason only:

> The running flextools-mcp **server process** cached flexicon **4.8.0 in memory
> at startup** (before the editable swap). Each `flextools_flextools_run_module`
> child re-imports but inherits the server's already-loaded 4.8.0, so the write
> probe still hits the OLD `get_String(wsHandle)` line and raises.

This is a **process-restart dependency, not a code defect.** The fix is in source
and editable-installed; a fresh interpreter resolves it correctly (proven in
`evidence/live-proof.md`).

**To finish the write proof:**
1. Restart the flextools-mcp MCP server (so it re-imports flexicon 4.9.0 editable
   from this repo).
2. Re-run the guarded deep-dup write probe against `Target` with
   `write_enabled=True, confirmed=True` and a pre-write backup:
   - `op.Duplicate(source, deep=True)` under `if modifyAllowed:`
   - read back `QuestionsOS.size` + scalar `OcmCodes` via the facade
   - assert conservation vs source
   - delete the `TEST_` duplicate (cleanup)
3. Land `specs/352-copyalternatives-audit/evidence/live-write.md` with the
   pass line.

## 6. Branching

Work is on **`main`** working tree (uncommitted `SemanticDomainOperations.py` +
`.claude/bugfix-loop.md`). The `fix/348-ocmcodes-none` branch holds the older
#348-specific form of the same fix. Under CLAUDE.md the autonomous
bug-fix loop is **PAUSED** (see `.claude/bugfix-loop.md`) and must not be
re-armed without explicit request.
