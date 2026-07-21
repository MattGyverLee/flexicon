# QC Report — cycle4-lex-qc

> Written by main session on behalf of lex-qc (read-only, no Write tool). Verbatim.

**QC Score: 91/100 — PASS. Recommendation: APPROVE.**

## Pattern-Audit Gate
N/A — docstring/doc-only (T7-T9) plus three pre-existing style/complexity fixes (T1-T3), not a bugfix closing a labelled `bug` issue.

## Findings — T1-T3 verified correct
- `MediaOperations.py` (imports 14-36): stdlib → third-party (`SIL.LCModel`) → local, clean order.
- `AgentOperations.py:84,114`: `@OperationsMethod` correctly applied (no `@wrap_enumerable` — returns plain `list`, correctly undecorated).
- `TranslationTypeOperations.py:318-357` (`GetSegmentsWithType`): fail-loud confirmed — raises `NotImplementedError` with clear rationale, documented in docstring + `Notes:`.

## Docstring spot-check (8 methods, 3 container types) — all accurate
`MediaOperations.GetAll` (EnumerableWrapper), `AnthropologyOperations.GetAll:175`, `ConstChartRowOperations.GetAll:225` (`return list(chart.RowsOS)`), `AgentOperations.GetAll:112` (list), `PhonologicalRuleOperations.GetAll:105`, `MorphRuleOperations.GetAllCompoundRules/GetAllAffixTemplates/GetAllAffixTemplatesForPOS` (SmartCollection) — every declared `Returns:` matches the actual return body.

## Docs
`docs/getall-contract.md`, README.rst pointer, `BaseOperations.py` "Behavioral collection contract" paragraph — accurate, cross-referenced correctly.

## Pyright Triage
1. `BaseOperations.pyi:20` `Iterator[Any]` vs list-returning overrides — PRE-EXISTING stub/impl mismatch, untouched (docstring-only edits). Defer to dedicated `.pyi` cycle. Not a regression.
2. `reportOptionalCall` at BaseOperations.py:~308 (`OperationsMethod.__get__`) — pre-existing, unrelated, defer.
3. all()/any() misuse ~1838-2116 — real defect: bare builtin `any` used as type annotation (`param: any`), no `typing.Any` import. Pre-existing, NOT introduced here. P2 — separate follow-up (4 occurrences, trivial + add `from typing import Any`).

## Issues
- P2: `BaseOperations.py:1838,2116` — `any`/`typing.Any` annotation misuse (pre-existing, not in scope).
- P2: 7 un-bracketed `list:` docstrings intentionally deferred by programmer — cosmetic, not misleading.

**Summary:** All T1-T3 fixes and 8 spot-checked docstrings correct; docs solid. Pyright base-annotation and reportOptionalCall are pre-existing noise (defer to .pyi follow-up); one real pre-existing `any`/`Any` bug worth a separate ticket. 91/100, APPROVE.
