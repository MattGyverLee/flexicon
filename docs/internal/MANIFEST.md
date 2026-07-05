# Documentation Manifest

The canonical index of every doc the `/lex-doc` agent maintains. Each entry declares its purpose, what code changes should trigger a review, and its current status.

**Statuses:**
- `live` — current, expected to track the codebase, drift counts as a bug
- `archived` — kept for history; no update triggers apply
- `template` — lives under `docs/_templates/`; updated only when the pattern it embodies changes
- `external-managed` — owned by another tool/process (e.g. Sphinx-generated reference); the agent does not edit

**Trigger format:** a list of patterns (commit subjects, changed file globs, or release events) that should cause `/lex-doc` to drift-check this entry.

---

## Release docs

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `CHANGELOG.md` | Versioned user-visible change record (Keep a Changelog format) | Every public-API commit; `feat`/`fix`/`refactor`/`docs`/`chore` on `main`; release cut | live |
| `docs/MIGRATION_GUIDE.md` | Cross-version migration guidance (v1 -> v2 -> ...) | `refactor!`, `feat!`, deprecation; planned removal | live |
| `docs/_archive/RELEASE_NOTES_v2.3.0.md` | Per-release narrative notes for v2.3.0 (Feb 28 2026) | (none — frozen) | archived |
| `docs/internal/RELEASE_v3_0_0.md` | Planning / draft notes for v3 | active development toward v3 | live |

## Architecture docs

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `docs/ARCHITECTURE.md` | High-level overview of wrapper + collection pattern | New domain, module restructuring, change to public-API shape | live |
| `docs/ARCHITECTURE_WRAPPERS.md` | Wrapper-class guide (concrete patterns, internal casting) | Changes under `flexlibs2/code/Shared/wrapper_base.py`, new wrapper class | live |
| `docs/ARCHITECTURE_COLLECTIONS.md` | SmartCollection guide | Changes under `flexlibs2/code/Shared/smart_collection.py`, new collection subclass | live |
| `docs/API_SURFACE.md` | Generated snapshot of SIL/LCM API usage (imports, namespaces, dependency hotspots) | Regenerate via `python tools/extract_api_usage.py --code-dir flexlibs2/code --all` at release cuts or yearly | external-managed (refreshed 2026-05-27) |

## Convention docs

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `docs/CATALOG_CONVENTIONS.md` | CatalogSourceId prefix policies (GOLD / PHON / INFL / synthetic) | Changes under `flexlibs2/code/Shared/catalog*.py`; new catalog domain | live |
| `docs/EXCEPTION_HANDLING.md` | FLEx-specific exception taxonomy and patterns | New `FP_*Error` class; change to `_EnsureWriteEnabled` / `_ValidateParam` | live |
| `docs/internal/CONTRACT_TESTING.md` | LibLCM contract test conventions | New contract test category; FW version bump | live |
| `docs/internal/TESTING_STRATEGY.md` | Project-wide testing approach | Test infrastructure changes (conftest, fixtures) | live |
| `docs/internal/TESTING_UNDO_REDO.md` | Undo/redo testing patterns | Changes to transaction framework | live |
| `docs/TRANSACTION_GUIDE.md` | Transaction management patterns | Changes to `Transaction()` context manager; Phase 2 transaction work | live |
| `docs/internal/PRE_COMMIT_SETUP.md` | Pre-commit hook setup + rationale | Changes under `.pre-commit-config.yaml`; new linter | live |
| `docs/CUSTOM_FIELDS.md` | Custom-field corruption mechanism + workflow guidance | Changes to `CustomFieldOperations.CreateField` | live |
| `docs/LINGUISTIC_SAFETY_GUIDE.md` | Linguistic-data safety practices (WS handling, NFD/NFC, etc.) | Changes to string normalization, WS handling, multilingual surfaces | live |

## Usage docs

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `docs/USAGE_AFFIX_TEMPLATES.md` | Affix-template workflows | Changes to affix-template operations | live |
| `docs/USAGE_ALLOMORPHS.md` | Allomorph operations workflows | `flexlibs2/code/Lexicon/AllomorphOperations.py` | live |
| `docs/USAGE_ANNOTATIONS.md` | Annotation workflows | Annotation-related operations | live |
| `docs/USAGE_COMPOUND_RULES.md` | Compound-rule workflows | Compound-rule operations | live |
| `docs/USAGE_CONTEXTS.md` | Phonological context workflows | `PhonologicalRuleOperations` context-handling | live |
| `docs/USAGE_MORPHOSYNTAX.md` | MSA workflows | `MSAOperations`, `LexSenseOperations.SetPartOfSpeech` | live |
| `docs/USAGE_PHONOLOGICAL_RULES.md` | Phonological rule workflows | `PhonologicalRuleOperations`, `WireRule`, alpha-features | live |
| `docs/USAGE_PROHIBITIONS.md` | Phonological prohibition workflows | Prohibition / restriction operations | live |
| `docs/operations/LexEntryOperations_README.md` | Per-class README for LexEntryOperations | `flexlibs2/code/Lexicon/LexEntryOperations.py` | live |
| `docs/operations/LEXSENSE_OPERATIONS_EXAMPLE.md` | Example workflows for LexSenseOperations | `flexlibs2/code/Lexicon/LexSenseOperations.py` | live |
| `docs/operations/PRONUNCIATION_OPERATIONS_SUMMARY.md` | Summary of pronunciation operations | Pronunciation-related operations | live |
| `docs/operations/PRONUNCIATION_OPERATIONS_USAGE.md` | Pronunciation usage patterns | Pronunciation-related operations | live |
| `docs/operations/TEXTOPERATIONS_USAGE.md` | TextOperations usage patterns | `flexlibs2/code/TextsWords/TextOperations.py` | live |
| `docs/operations/WRITING_SYSTEM_OPERATIONS_SUMMARY.md` | Writing-system operations summary | WS-related operations | live |

## Audit / inventory docs

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `docs/API_ISSUES_CATEGORIZED.md` | Known API issues + workarounds | Issue closed/opened against an API surface | live |
| `docs/internal/API_BUGS_FOUND_AND_FIXED.md` | Historical record of fixed bugs | Bug fixed and ready to record | live |
| `docs/FUNCTION_REFERENCE.md` | Hand-maintained function-level reference (method → LibLCM mapping, grouped by phase + Post-v2.0 supersection) | New `@OperationsMethod`-decorated method; removed/renamed public method | live (refreshed 2026-05-27, Phase 5/6 additions integrated) |
| `docs/internal/MERGE_OPERATIONS_AUDIT.md` | Audit of merge-related operations | Changes to merge operations / `validate_merge_compatibility` | live |
| `docs/internal/RESEARCH_NEEDED.md` | Open research questions | New unresolved API question; resolved question moved out | live |
| `docs/REVERSAL_API_MIGRATION.md` | Reversal-index API migration notes | Reversal-index operations changes | live |
| `docs/audit/LCM_AUDIT_INDEX.md` | Index of LCM capability audits | LCM audit refresh; FW version bump | live (refreshed 2026-05-27) |
| `docs/audit/LCM_AUDIT_SUMMARY.md` | Summary of LCM capability audits (decision-maker read) | LCM audit refresh | live (refreshed 2026-05-27) |
| `docs/audit/LCM_CAPABILITIES_AUDIT.md` | Detailed LCM capability audit | LCM audit refresh; FW version bump | live (partially refreshed 2026-05-27 — see TODO block at top of doc) |
| `docs/audit/LCM_CAPABILITIES_AUDIT_REFERENCES.md` | Cross-references for LCM audit | LCM audit refresh; FW version bump | live (partially refreshed 2026-05-27 — line numbers reference `reports/audit/api_usage_extract.json`) |
| `docs/audit/LCM_AUDIT_QUICK_REFERENCE.txt` | Quick-reference companion to the LCM audit set | LCM audit refresh | live (refreshed 2026-05-27) |
| `docs/audit/README_LCM_AUDIT.md` | Entry-point doc for the LCM audit set | Audit set restructuring | live (refreshed 2026-05-27) |
| `docs/internal/LISTS_CONSOLIDATION_TEMPLATE.md` | One-time refactoring guide for migrating 4 ops classes to `PossibilityItemOperations` (work landed; refactor partially superseded — see issue #54) | (none — historical) | archived |

## Project guidance

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `CLAUDE.md` | Project conventions for Claude Code (root) | New convention; design-philosophy update | live |
| `README.rst` | User-facing entry point | Installation, supported versions, top-level API summary | live |
| `history.md` | Live version-history file at repo root — sync surface with cdfarrow/flexlibs upstream. Format: `### N.N.N - DD MMM YYYY` (legacy upstream style, distinct from Keep-a-Changelog CHANGELOG.md). Sole source of v1.x history. | Every release; entries added in **parallel** with `CHANGELOG.md` | live (upstream-sync) |

## Templates

| Template | Purpose | Update Triggers | Status |
|---|---|---|---|
| `docs/_templates/CHANGELOG_ENTRY.md` | Single-entry stanza for CHANGELOG `[Unreleased]` | Format changes to the stanza | template |
| `docs/_templates/MIGRATION_GUIDE_SECTION.md` | Full section template for a breaking change | Format changes | template |
| `docs/_templates/MODULE_HEADER.md` | Standard Python file header (module/class/platform/copyright) | House style header changes | template |

## External-managed

| Doc | Purpose | Update Triggers | Status |
|---|---|---|---|
| `docs/sphinx/conf.py` | Sphinx build config | Sphinx version bump; theme change | external-managed |
| `docs/sphinx/flexlibs.rst` | Sphinx-generated API reference index | Generated from docstrings | external-managed |
| `docs/sphinx/readme.txt` | Sphinx README | Sphinx build process change | external-managed |

---

## Notes for `/lex-doc`

### Resolved (2026-05-27 first-run audit)

- **`docs/API_SURFACE.md`** is generated (via `tools/extract_api_usage.py`), not maintained by drift-checking. Reclassified `external-managed`. Refreshed 2026-05-27 (files analyzed 66 -> 73; SIL imports 527 -> 569; unique classes 194 -> 233; factories 42 -> 74). Tool default code-dir was wrong (`../flexlibs/code` finds 0 files); use `--code-dir flexlibs2/code --all`.
- **`docs/FUNCTION_REFERENCE.md`** is hand-maintained. Refreshed 2026-05-27 with Phase 5/6 additions in a "Recent Additions (Post-v2.0)" supersection (+47 method entries, +232 lines). Original 14 Phase sections preserved.
- **`docs/internal/LISTS_CONSOLIDATION_TEMPLATE.md`** was a one-time refactoring guide, not a reusable template. Refactor landed; per issue #54 the resulting `AgentOperations(PossibilityItemOperations)` inheritance turned out to be wrong, so the doc is partially superseded too. Reclassified `archived`. Not moved.

### Open follow-ups for user decision

- **`flexlibs2/__init__.py` declares version `3.0.0` but `CHANGELOG.md` latest is v2.4.0** — surfaced during the API_SURFACE refresh. Either the package version string is ahead of releases, or the CHANGELOG needs a v3.0.0 entry.
- **`CHANGELOG.md` v2.4.0/v2.4.1 duplicate + reversed dates** — filed as issue #146. Recommend verifying against `git tag --list 'v2.4*'`.
- ~~**`reports/audit/` JSON corpus**~~ — Resolved 2026-05-28. Tracked (4 files, ~300KB total). The corpus is load-bearing: `docs/audit/LCM_CAPABILITIES_AUDIT_REFERENCES.md` cites it by file:line so reproducibility across the team matters more than commit-history churn. Regenerate via `python tools/extract_api_usage.py --code-dir flexlibs2/code --all` from repo root. **Caveat:** the tool emits OS-native path separators in JSON (`code\\BaseOperations.py` on Windows, `code/BaseOperations.py` on POSIX). Refreshing on a different OS will produce a noisy diff. Either always refresh on Windows, or fix the tool to emit `as_posix()` paths (one-line change at [tools/extract_api_usage.py:120](tools/extract_api_usage.py#L120)) before adding a CI regeneration job.
- **CI-driven regeneration?** — Investigate whether `API_SURFACE.md` should be regenerated automatically (CI job) and whether `FUNCTION_REFERENCE.md` should be auto-generated from `@OperationsMethod` introspection rather than hand-maintained. Both are currently stale-by-default until someone re-runs the refresh. **Blocked on**: path-separator normalization in `extract_api_usage.py` (see corpus note above) — until the tool emits POSIX paths, any Linux-runner CI will report constant drift against the tracked Windows-generated JSONs.
- ~~**`LCM_AUDIT_*` set at repo root**~~ — Done 2026-05-27. Refreshed (counts, file lists, per-domain ops listings) and relocated to `docs/audit/` (6 files). Deep prose in `LCM_CAPABILITIES_AUDIT.md` and per-import file/line refs in `LCM_CAPABILITIES_AUDIT_REFERENCES.md` are partially refreshed — see `## TODO` blocks at the top of those docs. No inbound link rewrites needed (cross-refs between the 6 files are bare filenames). Future refreshes: `python tools/extract_api_usage.py --code-dir flexlibs2/code --all` produces the JSON corpus the audit set reads.
- **`RELEASE_NOTES_v2.3.0.md` archive move** — Done 2026-05-27. Moved to `docs/_archive/RELEASE_NOTES_v2.3.0.md` via `git mv`. Manifest path updated.
- **`history.md` archive move REVERTED 2026-05-27** — File moved back to repo root after user clarified it's a live upstream-sync surface (one of the few remaining links with cdfarrow/flexlibs upstream). Manifest entry reclassified from `archived` to `live (upstream-sync)`. Lesson: load-bearing duplicates can look archive-worthy on filename inspection alone; verify intent against upstream parity before classifying. See `~/.claude/projects/.../memory/project_history_md_upstream_sync.md`.

### Standing notes

- Whenever a doc is added under `docs/`, register it in the appropriate category table above in the same PR.
- Whenever a doc is retired, mark `archived` here rather than deleting the file.

## Notes for the user

This manifest is the **single source of truth** for what docs `/lex-doc` is responsible for. When a new doc is added to `docs/`, it must be registered here in the same PR. When a doc is no longer maintained, mark its status as `archived` here rather than deleting the file.

To onboard a new category: add a new `## Category` heading and table. The agent doesn't care about category boundaries — they exist for human readability.
