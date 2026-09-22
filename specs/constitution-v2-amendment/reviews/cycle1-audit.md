# Propagation Audit — Principle II reversal (constitution v2.0.0)

Cycle 1. Auditor: Explore (read-only). Date: 2026-09-22.

Note: produced read-only; persisted to this path by the main session because the
auditing agent has no Write tool. Classification reflects the mid-flight correction
that Sena 3 is safe for reads and edits in place at any time.

**Counts:** Bucket A (CONTRADICTS v2.0.0, must edit) **26** hits across **11** files.
Bucket B (stale but compatible) ~24 hits, 12 files. Bucket C (still correct, do not
sweep up) ~15 hits, 7 files.

## Bucket A — CONTRADICTS v2.0.0

| file | line | bucket | quoted text | proposed fix |
|---|---|---|---|---|
| C:\Users\thoua\.claude\agents\lex-lead.md | 167 | A | "needs_human — the next step needs a human decision OR a DESTRUCTIVE live-LCM write" | Drop the "OR a DESTRUCTIVE live-LCM write" arm; keep decision-only |
| C:\Users\thoua\.claude\agents\lex-lead.md | 169 | A | "Never perform a destructive live write unattended — this mirrors the log-triage rule" | Replace: writes to Target/Sena 3/sandbox are performed unattended |
| C:\Users\thoua\.claude\agents\lex-lead.md | 211 | A | "the fix needs a human decision / destructive live write, hand off with status: needs_human" | Strike "/ destructive live write" |
| C:\Users\thoua\.claude\CLAUDE.md | 96 | A | "needs_human → STOP. Surface the blocker to the user." (paired with 97) | Keep STOP; retarget to decisions only |
| C:\Users\thoua\.claude\CLAUDE.md | 97 | A | "Never let the loop perform a destructive live-LCM write ... unattended" | Replace: loop writes freely to Target/Sena 3/sandbox; never other projects |
| C:\Users\thoua\.claude\agents\lex-verification.md | 197 | A | "The change requires a destructive write a human must authorize" | Delete this blocker bullet; destructive -> use sandbox |
| C:\Users\thoua\.claude\agents\lex-verification.md | 199 | A | "Per the LEX crew protocol this is a needs_human handoff." | Scope to locked-project / FieldWorks-absent only |
| C:\Users\thoua\.claude\agents\lex-qc.md | 161 | A | "destructive write needing authorization) is not a PASS. It is a BLOCK" | Remove the "destructive write needing authorization" clause |
| D:\...\flexicon\CLAUDE.md | 146 | A | "### The required invocation" — then quotes only the live command | Retitle "The two required invocations"; add the offline one |
| D:\...\flexicon\CLAUDE.md | 124 | A | "### The two live projects" / "Default to Target for anything that writes" | State Sena 3 is write-safe in place; Target is default, not mandate |
| D:\...\specs\write-path-transactions\plan.md | 37 | A | "Required invocation, per constitution Principle II: pytest -m \"not requires_live_project\"" | Quote both invocations |
| ...\specs\write-path-transactions\plan.md | 50 | A | "No agent may execute a live LCM write (constitution II)." | Delete constraint; live writes now mandatory |
| ...\specs\write-path-transactions\plan.md | 51 | A | "structurally unavailable to every task except the needs_human B2t gate" | Delete; persistence verification is now available |
| ...\specs\write-path-transactions\plan.md | 62 | A | "evaluated against .specify/memory/constitution.md v1.0.0" | Re-evaluate against v2.0.0 |
| ...\specs\write-path-transactions\plan.md | 67 | A | "**II. No live write without human gate** \| PASS, with two recorded breaches" | Retitle row to v2.0.0 principle; re-assess |
| ...\specs\write-path-transactions\plan.md | 189 | A | "**B2t** ... **`needs_human`.** Requires a live LCM write" | Remove gate (already discharged per tasks.md:144) |
| ...\specs\write-path-transactions\plan.md | 190 | A | "to a scratch project. No agent may execute it." | Delete sentence |
| ...\specs\write-path-transactions\spec.md | 404 | A | "Phases A-D of those run **in-place against the real Sena 3 project**" | Keep prohibition; reword reason to "unscoped, no -m filter" |
| ...\specs\write-path-transactions\spec.md | 406 | A | "That command therefore performs live LCM writes against a real FLEx project." | Reword: hazard is unscoped collection, not writing |
| D:\...\docs\FLEXTOOLSMCP_WRITE_CONTRACT.md | 37 | A | "The required invocation is: python -m pytest -m \"not requires_live_project\" -q" | Say "offline half of two required invocations"; add live one |
| ...\docs\FLEXTOOLSMCP_WRITE_CONTRACT.md | 56 | A | "Phases A-D of those run **in-place against the real Sena 3 project**" | Keep prohibition; reason = unscoped |
| ...\docs\FLEXTOOLSMCP_WRITE_CONTRACT.md | 67 | A | "the only one that does not touch a real project" | Rewrite: correct because it is scope-filtered |
| D:\...\specs\lcm-member-truth-sweep\STATUS.md | 18 | A | "needs_human on a genuine blocker, and never a destructive live-LCM write unattended" | Strike the second clause |
| D:\...\specs\lcm-member-truth-sweep\spec.md | 306 | A | "Never run scripts/restore_*.py unattended -- ... stop with status: needs_human" | restore_target.py is now the sanctioned unattended path |
| D:\...\specs\242-paragraph-whitespace\tasks.md | 36 | A | "target_sandbox ONLY. Never the real Target, never any scripts/restore_*.py run" | Permit real Target + restore; sandbox for destructive/locked |
| D:\...\specs\243-closeproject-save-guard\tasks.md | 126 | A | "python -m pytest tests -m \"not requires_live_project\" -q" as sole gate | Add the live invocation |
| D:\...\docs\RELEASING.md | 232 | A | "python -m pytest -m \"not requires_live_project\" -q" as release gate | Add FLEXLIBS_REQUIRE_LIVE=1 live run to the checklist |

## Bucket B — STALE BUT COMPATIBLE (~24; leave)

Genuine-decision `needs_human`, which v2.0.0 preserves: `lex-lead.md:160`;
`flexicon\CLAUDE.md:179-180`; `lex-qc.md:160` (Target locked / FieldWorks absent
portion); `specs\250-writingsystem-activation\spec.md:261`;
`specs\276-gramcat-collection\spec.md:179`; `specs\lcm-member-truth-sweep\tasks.md:93,269`
(issue-filing needs user approval); `specs\name-field-whitespace-identity\spec.md:268,375,612`;
`specs\242-paragraph-whitespace\tasks.md:320,343` + `spec.md:823` (broken environment);
`specs\feature-structure-sync-gap\STATUS.md:625,826,1106` (cross-crew concurrency);
`lex-doc.md:215` (manifest arbitration).

Historical incident/closure records that should stay legible, not be rewritten:
`specs\write-path-transactions\tasks.md:144,175,202`; `reviews\cycle3-verification.md:63-64`;
`docs\FLEXTOOLSMCP_WRITE_CONTRACT.md:556,646,650`.

Stale-but-harmless path drift: `lex-qc.md:132` and `lex-verification.md:89` still say
`tests/conftest.py` where the constitution says `tests/flex_plugin.py`.

## Bucket C — STILL CORRECT (~15; confirm these survive)

Bare-`pytest` / `--ignore=tests/contract` prohibition: `constitution.md:76`,
`flexicon\CLAUDE.md:159-161`, `lex-verification.md:91-93`, `.claude\bugfix-loop.md:124-127`.

`TEST_` prefix + finally-restore: `constitution.md:55`, `flexicon\CLAUDE.md:137`,
`lex-verification.md:75-78`.

Sandbox for destructive or locked-project cases: `flexicon\CLAUDE.md:138-141`,
`lex-verification.md:66,78`.

**Sena 3 in-place writing already correct** and must NOT be swept:
`tests\LIVE_TESTING.md:176-201` (Phases C/D in place on real Sena 3; `sena3_sandbox`
"the exception, not the rule"), `lex-verification.md:44`, `.claude\bugfix-loop.md:144`,
`flexicon\CLAUDE.md:129`.

Both-invocations-quoted exemplar: `specs\write-path-transactions\spec.md:374-387`.

`.specify\templates\*` encode nothing of the old rule — no edit needed.

## Edit order

1. `C:\Users\thoua\.claude\agents\lex-lead.md` — **the orchestrator's own definition**;
   it gates every dispatch, so its stale `needs_human`-on-write arm will re-inject the
   void rule into any brief written before it is fixed. Edit first.
2. `C:\Users\thoua\.claude\CLAUDE.md` — the ralph-loop handler that enforces lex-lead's
   status; must move in the same pass or the loop still halts on writes.
3. `C:\Users\thoua\.claude\agents\lex-verification.md`, then `lex-qc.md` — producer and
   gatekeeper of live evidence.
4. `D:\Github\_Projects\_LEX\flexicon\CLAUDE.md` — project runtime guidance; add the
   second invocation and the Sena 3 write permission.
5. `docs\FLEXTOOLSMCP_WRITE_CONTRACT.md`, then `docs\RELEASING.md` — published docs
   quoting the single offline invocation.
6. `specs\write-path-transactions\plan.md` + `spec.md` — the largest concentration of
   the void rule.
7. `specs\lcm-member-truth-sweep\{STATUS,spec}.md`, `specs\242-paragraph-whitespace\tasks.md`,
   `specs\243-closeproject-save-guard\tasks.md` — standing-gate blocks inherited by
   future tasks.

Note on 6-7: those features are closed. If the crew treats `specs/**` as an
append-only record, prefer a dated superseding note citing constitution v2.0.0 over an
in-place rewrite, per the constitution's "superseded reasoning stays legible" rule.
