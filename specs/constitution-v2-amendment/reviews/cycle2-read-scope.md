# Read-Scope Sweep — the gap cycle 1 could not see

Cycle 2. Auditor: Explore (read-only). Date: 2026-09-22.

Note: produced read-only; persisted to this path by the main session because the
auditing agent has no Write tool.

Scope: text that confines READS to Target and Sena 3, or treats opening another
project read-only as needing permission. Constitution v2.0.0+ Principle II makes
reads unrestricted; only writes are bounded.

| file | line | class | quoted text | proposed fix |
|---|---|---|---|---|
| D:\...\flexicon\CLAUDE.md | 124-132 | **CONTRADICTS** | "### The two live projects" ... table "Use for \| Sena 3 \| Read-path coverage" ... "Reach for **Sena 3** only when the test genuinely needs pre-existing data to read or modify." | Section names exactly two projects and allocates *reads* to one, with nothing saying any project may be opened read-only. Cycle 1 flags :124 for the **write** default only. Add under the table: "Reads are unrestricted -- any project on the machine may be opened read-only at any time, no gate (constitution II). The table allocates the two *write*-safe projects." Retitle "The two live **write** projects". |
| D:\...\flexicon\tests\LIVE_TESTING.md | 13-27 | **CONTRADICTS** | "## The two live projects" ... "Reach for Sena 3 only when the test needs pre-existing data to read or modify." ... "`Test`, `SampleLexicon`, and `SampleLexicon3` remain as fallback candidates ... but **new live tests should use the Target or Sena 3 fixtures below**." | Closest thing to an exhaustive openable-project list; :26-27 reads as a prohibition on new tests opening anything else, including read-only. Not in cycle-1 Bucket A (only :176-201 appears, in Bucket C -- do not disturb those). Scope :26-27 to write-enabled fixtures; add the reads-unrestricted sentence and cite `.claude\bugfix-loop.md:144-149` and `tests\operations\test_parser_live.py:59-64` as sanctioned read-only opens outside the two. |
| C:\Users\thoua\.claude\agents\lex-verification.md | 39-44 | **CONTRADICTS** (weak) | "## The two live projects" ... "\| **Sena 3** \| Fully populated \| Read-path, modify-pre-existing-data \|" | Same heading+table in the agent that *produces* live evidence, so it re-injects the framing into every brief. Cycle-1 Bucket C protects :44's write content -- keep that, add one line: reads may target any project; the table bounds writes. |
| D:\...\flexicon\tests\test_CustomFields.py | 44-46 | COMPATIBLE | "is not one of the two projects CLAUDE.md designates (Target, Sena 3)" | Docstring is `_openProject` "with **write** access"; the skip is environmental, not permission. Leave. |
| D:\...\tests\flex_plugin.py | 1362-1369 | COMPATIBLE | "Division of labour: Target -- write-path verification. Sena 3 -- read-path coverage" | Convenience allocation + write-evidence rule. Leave. |
| D:\...\scripts\restore_sena3.py | 8-9 | COMPATIBLE | "used for read-path coverage and for modifying pre-existing data" | Describes the fixture's purpose. Leave. |
| D:\...\specs\277-nonexistent-property-reads\evidence\live-277-overlays.md | 122-125 | COMPATIBLE | "per CLAUDE.md, Sena 3 -- not Target -- is the populated project for read-path coverage" | Dated evidence; advice, not gate. Leave. |
| D:\...\flexicon\.claude\bugfix-loop.md | 144-149 | COMPATIBLE (model text) | "`Ejagham Full` ... is available as an additional read-path corpus when Sena 3 lacks the data ... do not use it as a Target substitute" | Already read-anywhere / write-bounded. Reuse this wording in the three fixes above. |
| D:\...\tests\operations\test_parser_live.py | 30-32, 59-64 | COMPATIBLE | "INSTALLED PROJECTS ONLY, NEVER A .fwbackup SANDBOX" (IndonesianHC-Complete, Malay Parsing) | Technical (modal dialog), not permission -- and live proof reads already range past the two. Leave. |
| D:\...\specs\write-path-transactions\reviews\cycle3-verification.md | 63 | COMPATIBLE | "you may NOT open any FLEx project **for writing**" | Write-scoped, historical incident record. Leave. |
| C:\Users\thoua\.claude\backups\perf-trim-20260918\project-CLAUDE.md | 233-238 | COMPATIBLE | duplicate "### The two live projects" table | Dated backup artifact, not live guidance. Do not edit. |

## Bottom line

Only 3 true read-confinement defects exist, all the same shape -- a "The two live
projects" heading whose "Use for" column assigns *read-path coverage* to Sena 3 while
nothing states reads are unrestricted, so the table reads as the complete set of
openable projects: `flexicon\CLAUDE.md:124-132`, `tests\LIVE_TESTING.md:13-27` (the
strongest, via "new live tests should use the Target or Sena 3 fixtures"), and
`lex-verification.md:39-44`.

Nothing anywhere treats a read-only open as needing permission or a gate; the fix is
additive (one reads-unrestricted sentence per site, plus retitling the heading to name
writes), and `.claude\bugfix-loop.md:144-149` already carries the correct wording to
copy. No hits overlap cycle-1's 26 Bucket A entries on their read dimension.
