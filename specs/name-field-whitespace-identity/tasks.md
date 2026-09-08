# TASKS -- name-field-whitespace-identity

Derived from `spec.md` NF1-NF11 (all FROZEN, 2026-09-08).
Origin: Q-242A in `specs/tier1-silent-data-loss/QUEUE.md`.

**Checkpoint 1 (the ruling) is DONE. Checkpoints 2-4 are BLOCKED on
`specs/242-paragraph-whitespace/spec.md` C18** -- the environment cannot
execute the live tests OR the offline suite, so nothing below can be
verified, and per CLAUDE.md an unverified write-path change is
`FAIL: unverified`, never a clean result. Do not start Checkpoint 2 until
C18 is resolved.

---

## Checkpoint 1 -- Rule the dedup-identity question (DONE, 2026-09-08)

- [x] T1 -- Census every `normalize_match_key` comparison site; classify
      asymmetric / symmetric. Result: 40 pairs, 10 asymmetric, 0 casefold
      divergence (`spec.md` NF1).
- [x] T2 -- Establish whether the identity defect is caused by fixing the
      strip, or pre-existing. Result: **pre-existing, and reachable
      through this library's own public API** in both halves --
      duplicate-explosion (4 sites) and unreachable-object (5 sites).
      This refuted the premise of the question as filed (`spec.md` NF2).
- [x] T3 -- Rule the question. `"Genesis "` IS `"Genesis"` for identity;
      case unchanged per-site (`spec.md` NF3). Store verbatim, compare
      normalized (`spec.md` NF4).
- [x] T4 -- Rule the fix locus and scope (`spec.md` NF5, NF6), including
      the four binding conditions after the impact assessment found a
      counter-example.
- [x] T5 -- Record hazards H1-H8, provenance, the C8 citation defect, and
      the adjudicated inter-pass disagreements (`spec.md` NF7, NF9, NF10,
      NF11).

**Q-242A is UNBLOCKED by this checkpoint.** Its stated blocker was this
ruling.

---

## Checkpoint 2 -- The matcher (BLOCKED on C18)

Order matters: the probe must measure the defect BEFORE the fix lands, per
the C28 forward rule.

- [ ] T1 -- Write `tests/operations/test_name_field_identity_probe.py`.
      **It does not exist** -- `evidence/live-probe-cycle1.md` names it but
      it was never written or committed (`spec.md` NF8). Predictions
      PN1-PN8 are already committed (`bdbce02`), so do NOT edit them; the
      harness must be built to measure them as written.
- [ ] T2 -- Run the probe against the UNFIXED code. Confirm or refute
      PN1-PN8 and the NF2 halves empirically. **A refuted prediction is a
      successful cycle** -- the evidence file's refutation clause binds.
      Fill in its RESULTS section in a second commit.
- [ ] T3 -- Add unit cases to `tests/test_normalize_match_key.py` for
      `" x "`, `"   "` and `" *** "`. **None exist today in either
      direction** (`spec.md` NF7 H7), so the suite currently cannot catch
      this change failing. These land WITH the change, not after.
- [ ] T4 -- `normalize_match_key`: `text = normalize_text(text).strip(" \t\r\n")`,
      placed AFTER the null-marker check (NF5 condition 1, NF7 H4) and
      using the restricted character set (NF5 condition 2, NF7 H5).
- [ ] T5 -- Fence `ScrDraftOperations.Find` off the shared helper (NF5
      condition 3, NF7 H2). Containment is not equality. Comment it so a
      future reader does not "tidy" it back.
- [ ] T6 -- Drop the now-redundant needle-only `.strip()` at all **10**
      bucket-A sites. **Use both greps** -- 7 are inline
      (`normalize_match_key(name.strip(), ...)`) and 3 are reassignment-style
      (`name = name.strip()` first); an inline-only pattern match silently
      misses three (`spec.md` NF11 item 3).
- [ ] T7 -- Add needle guards at the unguarded sites so a whitespace-only
      needle cannot degenerate into the promiscuous `""` key (NF5
      condition 4, NF7 H6): `PhonemeOperations.py:462` and `:929`,
      `PhonologicalRuleOperations.py:332`, `POSOperations.py:343`,
      `DataNotebookOperations.py:479`.
- [ ] T8 -- Re-run the probe. The NF2 halves must now be fixed: uniqueness
      guards fire, created objects are findable.

## Checkpoint 3 -- The 8 filed writer sites (BLOCKED on C18)

- [ ] T1 -- Apply #242 C8's binding shape at all 8 Q-242A sites:
      `x = v if isinstance(v, str) else str(v)`; guard on `x.strip()`;
      persist the ORIGINAL `v`. Sites: `CheckOperations.py:196`/`:432`,
      `TextOperations.py:152`/`:608`, `DiscourseOperations.py:327`/`:482`,
      `AnthropologyOperations.py:265`/`:374`.
- [ ] T2 -- Do NOT touch the coercion defect at `CheckOperations.py:196`/
      `:341`/`:432` -- that is **Q-242B**, ruled out of scope by NF6 and
      deliberately triaged at higher severity. This feature edits those
      FILES without fixing that DEFECT; keep the two apart in the diff and
      the commit message.
- [ ] T3 -- Live-verify: pre-state and post-state read back from the LCM by
      re-querying after the write. `target_sandbox` / `target_sandbox_path`
      ONLY. Per #242 C16, paste `run_mode` AND `run_timestamp` verbatim
      into the evidence file -- `tests/live_status.json` is gitignored and
      does not survive the run.

## Checkpoint 4 -- Docs (BLOCKED on C18)

- [ ] T1 -- CHANGELOG. Two distinct entries, not one:
      a **`### Fixed`** entry for the matcher asymmetry and the two NF2
      halves (**pre-existing**, per NF2/NF9 -- classified like #242's C12),
      and a **`### Changed`** entry with a `**BREAKING (behavioural): ...**`
      lead for the 8 writer sites (per #242 C9's convention, which now has
      four instances at `CHANGELOG.md:15`, `:63`, `:95`, `:500`).
- [ ] T2 -- Document the equality-vs-containment split in
      `normalize_match_key`'s docstring, so the fence is discoverable from
      the helper rather than only from this spec.
- [ ] T3 -- Docstring notes at the 8 writer sites, matching #242 C14's
      binding text.

## Open, NOT this feature's to close

- [ ] **C18** (`specs/242-paragraph-whitespace/spec.md`) -- restore a
      3.8-3.13 interpreter with `pythonnet >=3.0.3,<3.1`, or rule on
      relaxing the pin. `needs_human`. **Everything above is blocked on
      this.**
- [ ] **NF7 H1** -- `strip_display_marker`'s ordering defect
      (`morph_type_utils.py:108-109`): a `" -suffix"` needle keeps its `-`
      marker. Pre-existing, NOT fixed by this feature (the marker strip
      runs first, at the call site). Needs its own ruling.
- [ ] **NF10** -- #242 C8 cites a "CLAUDE.md-named caller-managed-flag
      anti-pattern" that does not appear in `CLAUDE.md`. For #242's owner:
      locate the rule, write it down, or restate C8's ground as the
      82-vs-12 argument alone.
- [ ] **NF1's case-sensitivity inconsistency** -- 21 sites
      case-insensitive, 19 case-sensitive. Newly documented, ruled out of
      scope by NF3, and deliberately NOT filed as a defect: each site is
      internally consistent, so this is a consistency question. Do not cite
      NF3 as precedent for harmonising it.
- [ ] **Q-242B**, **Q-242C** -- remain in
      `specs/tier1-silent-data-loss/QUEUE.md`, untouched by NF6.

## Hard constraints

- `target_sandbox` / `target_sandbox_path` ONLY. Never the real Target,
  never `scripts/restore_*.py`.
- Never bare `pytest` -- it collects and EXECUTES ~322
  `requires_live_project` tests in-place against real projects. Offline is
  `python -m pytest tests -m "not requires_live_project" -q`.
- Derive every live count with `--collect-only`. "No tests collected" is a
  ZERO, never a pass.
- The C28 forward rule: predictions are committed BEFORE the measuring run.
  PN1-PN8 are already committed at `bdbce02` -- do not edit them to match
  what you measure.
- NF1-NF11 are FROZEN. Do not implement NF5 with any variation -- no bare
  `.strip()`, no placement before the null-marker check, no unfenced
  `ScrDraftOperations.Find` -- without citing and overturning the item by
  number.
- This spec does not edit `specs/tier1-silent-data-loss/QUEUE.md` or its
  `.crew-handoff.json`; campaign-level files belong to the main session.
