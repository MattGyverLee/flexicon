# T4 QC -- Issue #325 Syncable Properties (re-run)

**Task:** T4 (lex-qc)
**Campaign:** 325-syncable-properties
**Working directory:** C:/Github/flexicon-325
**Branch:** fix/325-syncable-properties (uncommitted wave-1 diff vs `main` at `7e77099`)
**Date:** 2026-09-22 (re-run after pattern-audit unblock)
**Reviewer:** lex-qc

**Inputs reviewed:**
- `specs/325-syncable-properties/rulings.md`
- `specs/325-syncable-properties/evidence/T1b-breaking-changes.md`
- `specs/325-syncable-properties/evidence/T2a-implementation.md`
- `specs/325-syncable-properties/evidence/pattern-audit.md` (unblock deliverable)
- `specs/325-syncable-properties/evidence/live-T3-syncable-properties.md`
- `tests/live_status.json` (post-T3)
- Uncommitted diff: 7 Operations/test files + new live/ratchet tests + `specs/325-syncable-properties/`

**Prior T4 (BLOCK):** Missing `pattern-audit.md`. Re-evaluated after file landed (~60s poll).

---

## Verdict

**APPROVE**

Pattern-audit gate is satisfied. Style/guards and live T3 evidence remain acceptable per prior review; R4 media stays `needs_human` and is not a QC style block.

---

## Gate checklist

| Gate | Result | Notes |
|------|--------|-------|
| Pattern audit in programmer deliverables | **PASS** | `specs/325-syncable-properties/evidence/pattern-audit.md` contains `## Pattern audit: dead hasattr / wrong-suffix LCM member in sync and copy paths`, original #325 sites table, **15** sibling line items for T9, explicit clears (WordGroupRA, StratumRA, ExampleOperations, TextOperations MediaURIsOC), VariantOperations `ShowComplexFormsIn` triage aligned with ratchet allowlist. |
| T2a verification vs T3 | **PASS** | `T2a-implementation.md` offline section points at `live-T3-syncable-properties.md` (`run_mode`: live). `## Verification status` is **PASS (via T3)** -- no standalone **FAIL: unverified** without T3 pointer. |
| T3 `run_mode=live` | **PASS** | `live-T3-syncable-properties.md` + `tests/live_status.json` both `"run_mode": "live"`. |
| T3 LCM read-back values | **PASS with documented gap** | (b) `owner_guid` + stable after Apply; (d) `Preposed` re-read; (e) payload keys; R8 Name keys `['en']`. **(a) `LanguageRS after Apply (re-read)` skipped** when Languages list empty (Target sandbox). Binding T3 marks (a) PASS; merge may optionally seed Languages for full R1 Apply re-read -- not a T4 block. |
| (c) media R4 | **needs_human (expected)** | Documented xfail/skip in live suite; not a QC style block. |

---

## Pattern audit QC read

**Bug class:** Nonexistent or wrong-suffix LCM members behind `hasattr` in `GetSyncableProperties` / `Duplicate` / Apply paths -- matches #325 / Category 8 shaped fix.

**Sweep documentation:** Horizontal scope stated (`flexicon/code/**/*Operations.py`); methodology cites baseline + T0 JSON; original wave-1 sites mapped to R1--R8; siblings enumerated with file:line and severity.

**Spot-check:** `VariantOperations.py:618` `hasattr(item, "ShowComplexFormsIn")` confirmed in tree; audit triage matches ratchet allowlist intent.

**Minor nit (non-blocking):** Audit cites `python scripts/_pattern_audit_sweep.py`; that path is not present in the working tree at re-run time. Evidence is still actionable (line-level siblings + clears). Consider adding the script or revising the method line if the sweep is re-run.

**Ratchet:** `tests/test_syncable_properties_member_ratchet.py` remains complementary, not a substitute for the audit file (correctly stated in both artifacts).

---

## Style / conventions (unchanged from prior T4 -- still PASS)

| Area | Assessment |
|------|------------|
| File headers / module shape | **PASS** |
| `BaseOperations` validation | **PASS** |
| `FP_*` exceptions | **PASS** |
| `writeEnabled` / `_EnsureWriteEnabled()` | **PASS** |
| Logging | **PASS** |
| `flexlibs2` | **PASS** -- no new alias references |
| Casting / interfaces | **PASS** |
| R7 scope (LexEntry `DoNotShowMainEntryInRC` untouched) | **PASS** |
| R6 test debt (`test_setlanguage_persists_to_the_lcm` xfail) | **PASS (deferred per T1b)** |

**Optional follow-ups (not T4 gates):**
- Remove stale `# VERIFY in T3` on `ConstChartMovedTextOperations.Create` now that T3 (d) PASS.
- Re-run T3 (a) with >=1 language possibility seeded when a project with Languages list is available.

---

## Ruling / API alignment (code read -- unchanged)

R1--R8 implementations in the reviewed diff align with `rulings.md` and T1b constraints. LexReference Apply idempotent skip when GUID lists match (T3 patch) is documented behavior; Etymology `language_rs` Apply still Clear+Add when not fill_gaps-blocked -- note for future live NRE watch only.

---

## T3 evidence review (lex-qc lens)

**Commands:** offline `-m "not requires_live_project"` + live `test_325_syncable_properties_live.py` with `FLEXLIBS_REQUIRE_LIVE=1`.

**Machine evidence:** `tests/live_status.json` timestamp `2026-09-22T21:59:00Z`; 7 pass / 1 skip (media).

**Read-back samples:** owner_guid, targets_rs count, Preposed, Duplicate LanguageNotes, Name dict keys.

---

## Required actions before merge (informational, not QC block)

1. **Human:** R4 media project for (c) when available.
2. **Optional:** Seed Languages in Target (or Sena 3) and refresh (a) Apply re-read lines in live evidence.
3. **T9:** File siblings from `pattern-audit.md` (15 items) per campaign triage policy.

---

## Summary

Re-run T4 clears the prior **BLOCK** on missing pattern audit. Documentation, conventions, and live verification meet lex-qc bar for wave-1 #325 syncable-properties work.

**Return code for campaign:** **APPROVE**.
