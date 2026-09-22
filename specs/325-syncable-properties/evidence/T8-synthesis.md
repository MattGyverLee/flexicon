# T8 -- Campaign synthesis (issue #325 syncable properties)

**Task:** T8 (lex-synthesis)  
**Campaign:** 325-syncable-properties  
**Working directory:** `C:/Github/flexicon-325`  
**Date:** 2026-09-22  
**Commit:** none (per binding)

## Inputs aggregated

| Source | Outcome |
|--------|---------|
| `rulings.md` (R1-R8) | Binding implementer authority; R4 flagged `needs_human` at T1 |
| `live-T3-syncable-properties.md` | `run_mode`: **live**; 7 pass / 1 skip (media) |
| `tests/live_status.json` | `run_mode`: **live**, timestamp 2026-09-22T21:59:00Z |
| `T4-qc.md` | **APPROVE** (pattern-audit gate cleared) |
| `T6-domain.md` | **CONFORM** (R4 live verification **DIVERGE** from verified bar) |
| `T7-doc.md` | **PASS** |
| `pattern-audit.md` | Wave-1 sites fixed; **15** sibling lines for T9 filing |

---

## Unified assessment

Wave-1 code, documentation, QC, and domain conformance are **aligned** with `rulings.md`. T3 ran live on `target_sandbox` with machine evidence in `live-T3-syncable-properties.md` and `tests/live_status.json`. The campaign delivered the intended remediation class (phantom `*RA`/`*RC` guards and wrong LCM members replaced or removed; R6 plural API; R7 sense-only RC cleanup; R8 `Name` in text sync). Pattern audit satisfies the shaped-bug horizontal gate; T9 should file the 15 enumerated siblings without re-opening wave-1 sites.

The **close keyword gate** is stricter: T9 may use `closes #325` only if **every** original issue #325 site is both **fixed in code** and **live-verified with LCM read-back** (per project live-LCM rules and this campaign brief). That bar is **not** met.

---

## Seven #325 sites: fixed vs live-verified

| # | Issue site | Ruling | Code fixed | Live verified (LCM read-back) | T3 / notes |
|---|------------|--------|------------|-------------------------------|------------|
| 1 | `MovedTextMarkerOA` / moved-text create path | R5 | Yes -- `row.CellsOS`, setter order, `WordGroupRA` nav | **Yes** | Section (d) PASS: Create, Preposed round-trip, Delete |
| 2 | `MediaFilesRC` on IText sync | R4 | Yes -- `media_uris` via concrete `MediaFilesOA` -> `MediaURIsOC` | **No** | Section (c) **FAIL: unverified**; test skipped; `needs_human` (no project with populated media) |
| 3 | `LanguageRA` on etymology sync | R1 | Yes -- `language_rs` ordered GUID list; Apply replace | **Partial** | GSP `language_rs` PASS; **Apply re-read skipped** (Languages list empty in Target); deprecated Get/SetLanguage warn PASS. `test_language_rs_roundtrip` passes without seeding Apply proof |
| 4 | `LanguageNotesRA` in etymology GSP | R2 | Yes -- removed | **Yes** | `(a) LanguageNotesRA absent` True |
| 5 | `LanguageNotesRA` in etymology `Duplicate` | R2 | Yes -- removed | **Yes** | Duplicate LanguageNotes preserved (`T3_source_note`) |
| 6 | `LanguageNotesRA` in entry `Duplicate` | R2 | Yes -- removed (pattern-audit) | **Yes (indirect)** | Same live suite / R2 conformance; no separate duplicate assertion in T3 evidence file |
| 7 | `ReferenceTypeRA` on ILexReference | R3 | Yes -- `owner_guid` + `targets_rs` | **Partial** | Read payload PASS; **Apply only idempotent** (same props, no sequence mutation). Mutating `targets_rs` replace (Clear+Add) not exercised in T3 |

**In-scope additions (not counted in the seven, but bound to #325 close narrative):**

| Scope | Ruling | Code fixed | Live verified |
|-------|--------|------------|---------------|
| `DoNotShowMainEntryInRC` on ILexSense | R7 | Yes | **Yes** -- section (e) PASS |
| IText `Name` in sync | R8 | Yes | **Yes** -- section (c) Name PASS |

**Headline for T9:** All **seven** wave-1 phantom sites are **fixed in code**. **Not all seven** are **fully live-verified**. Sites **2** (media) and **3** (LanguageRS Apply round-trip) fail the strict read-back bar; site **7** is verified only on the idempotent Apply path, with **TargetsRS Clear+Add when the sequence must change** called out in QC/T6 as an unwatched NRE risk (same class as etymology `language_rs` replace when not blocked by `fill_gaps`).

---

## Known gaps (weighted)

1. **R4 / MediaFilesRC -> `media_uris` (site 2)** -- Highest weight for close gate. Ruling R4 and T1 `needs_human` remain open. Implementation conforms (T6); end-to-end serialize/apply against real `ICmMediaURI` data was **never** run. T7 and migration docs correctly note unverified media. Pattern audit also flags sibling breakage in `GetMediaFiles` / `AddMediaFile` (`MediaFilesOC` vs `MediaURIsOC`) -- out of wave-1 but same defect family.

2. **R1 / LanguageRS Apply (site 3)** -- Medium weight. Empty Languages list in Target sandbox prevented seeding and **skipped** `(a) LanguageRS after Apply (re-read)` in the evidence artifact. Serialization, phantom-key removal, and R6 warnings are proven; **replace Apply is not read back from LCM** in this campaign run.

3. **R3 / TargetsRS replace (site 7)** -- Lower weight for "fixed" but relevant for "fully verified." T3 proves payload shape and stable idempotent Apply. A sync that **changes** `targets_rs` content relies on Clear+Add replace logic that T4 notes as future NRE watch only.

4. **R5 Preposed** -- **Closed for campaign purposes.** T3 (d) exceeded choice (a) minimum; no remaining R5 verification gap.

5. **T9 siblings (15)** -- Not a block on merge QC; **is** a block on treating #325 as the entire Category-8 surface area.

---

## Specialist verdict rollup

| Task | Agent | Verdict | Synthesis note |
|------|-------|---------|----------------|
| T3 | lex-verification | Live PASS with documented holes | `run_mode=live`; media skip; LanguageRS Apply re-read omitted |
| T4 | lex-qc | **APPROVE** | Style + pattern audit; R4 unverified expected, not QC block |
| T6 | lex-domain | **CONFORM** | Code matches rulings; R4 live bar explicitly diverges |
| T7 | lex-doc | **PASS** | Category 8 + migration aligned; media marked unverified |

**Campaign merge readiness (QC + domain + docs):** **Ready** for wave-1 merge subject to normal human review.  
**Campaign issue close readiness (`closes #325`):** **Not ready** under the binding all-seven-live-verified criterion.

---

## T9 instruction: `closes #325`

| Decision | **CLOSE_BLOCKED** |
|----------|-------------------|

T9 must **not** use `closes #325` on the merge commit unless the archivist receives updated live evidence that (1) exercises `media_uris` on a media-populated project with post-Apply read-back, and (2) completes LanguageRS Apply re-read with at least one seeded language GUID (and, if policy requires, a mutating `targets_rs` Apply read-back). Until then, prefer **`Addresses #325`** (or equivalent non-closing reference) and leave #325 open with a short comment linking `live-T3-syncable-properties.md`, the R4 `needs_human` line, and optional follow-up issues for media verification and RS replace paths.

Parallel T9 work: file **15** pattern-audit siblings per triage; do not conflate sibling filing with closing #325.

---

## Archivist rationale (one paragraph)

Wave-1 fixes for issue #325 are implemented consistently across Operations, tests, and docs, and T4/T6/T7 approve the branch for merge, but the campaign’s own close rule requires every original phantom site to be live-verified with LCM read-back—and that set is incomplete: `MediaFilesRC`/`media_uris` remains explicitly **FAIL: unverified** with no media-populated project, `LanguageRA`/`language_rs` never had Apply re-read after seeding because Target’s Languages list was empty, and `ReferenceTypeRA`/`owner_guid`+`targets_rs` was only proven on idempotent Apply while mutating reference-sequence replace paths share an documented NRE watch. Closing #325 now would overstate verification against CLAUDE live-LCM policy and R4’s binding `needs_human`; keep the issue open or reference it without a close keyword until media and LanguageRS (and optionally mutating TargetsRS) evidence is appended, while still merging the approved wave-1 change and filing the fifteen audit siblings separately.

---

## Return code for campaign orchestrator

**CLOSE_BLOCKED**
