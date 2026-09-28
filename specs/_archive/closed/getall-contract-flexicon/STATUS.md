# STATUS — getall-contract-flexicon

Repo: flexicon (main). Cross-repo issue: FlexToolsMCP#37.

## Where things stand (as of 2026-07-20, cycle 3/spurt end)

All quality gates are GREEN for the flexicon changeset:

- **Verification:** PASS. The 3 code fixes (T1-T3) are correct, and the full
  changeset is regression-clean — clean-main worktree (HEAD `ff1c008`) vs the
  working tree produce byte-for-byte identical 172-node FAILED/ERROR sets
  (139 failed / 33 errors both sides), delta 0 in both directions. The 6-count
  passed/skipped difference is a worktree-fixture artifact (untracked
  `.fwbackup` fixtures not materialized by `git worktree add`), not a code
  regression. See `reviews/cycle4-lex-verification.md` +
  `reviews/cycle5-lex-verification-baseline.md`.
- **QC:** 91/100 APPROVE. See `reviews/cycle4-lex-qc.md`.
- **Domain:** PASS. See `reviews/cycle4-lex-domain.md`.

## What landed this feature

- T1-T3: the D1/D2/D3 code fixes — `MediaOperations.GetAll` uses
  `ICmFileRepository`; `AgentOperations.GetAll` gets `@OperationsMethod`;
  `TranslationTypeOperations.GetSegmentsWithType` is now fail-loud.
- T7-T9: standardized ~51 bare `GetAll`/`GetAll*` docstrings to the
  `Returns: <ContainerType>[<Element>]` contract form (dropping misleading
  `Yields:` wording), added `docs/getall-contract.md` (canonical
  loop/len/index/re-iterate guarantee) + `README.rst` pointer + a
  cross-referencing paragraph in the `wrap_enumerable` docstring.

## Next pickup

1. **T6 (this spurt's last action): archivist commit** — single flexicon commit
   covering T1-T3 + T7-T9, `closes MattGyverLee/FlexToolsMCP#37` (cross-repo),
   update CHANGELOG `[Unreleased]` + `history.md`, and file/note the two
   deferred out-of-scope tickets.
2. **Deferred (out-of-scope, ticketed):**
   - Pre-existing bare `any`/`typing.Any` bug at `BaseOperations.py:1838,2116`.
   - `.pyi` `Iterator[Any]` return-annotation reconciliation (T10 — needs
     generics modeling + `*args/**kwargs` signature-drift fix; dedicated cycle).
3. **Next spurt (MCP revision, in FlexToolsMCP repo):** drop the Level-2 override
   -> regen via `refresh.py` against the now-standardized flexicon docstrings;
   rescope the validator to stable-flexlibs mode only; reframe the Level-1 docs;
   un-flip the flexicon-mode corpus cases.
