# Flexicon Claude Code Guidelines

Conventions and binding rules for this project. Reference material that
used to live here now sits in `docs/` -- this file is the checklist, those
are the explanations. Pointers are given inline.

## Project Overview

Flexicon is a Python library for accessing FieldWorks Language Explorer
(FLEx) projects via the Language and Culture Model (LCM) API. It provides
CRUD operations for FLEx data types across Grammar, Lexicon, Texts &
Words, Notebook, Lists, and System modules.

## Project Structure

```
flexicon/
├── flexicon/
│   ├── code/
│   │   ├── BaseOperations.py          # Parent class for all operations
│   │   ├── FLExProject.py             # Main project interface
│   │   ├── Grammar/                   # POS, Phonemes, Rules, etc.
│   │   ├── Lexicon/                   # Entries, Senses, Examples, etc.
│   │   ├── TextsWords/                # Texts, Wordforms, Analyses, etc.
│   │   ├── Notebook/                  # Notes, People, Locations, etc.
│   │   ├── Lists/                     # Publications, Agents, etc.
│   │   ├── System/                    # Writing Systems, Custom Fields, etc.
│   │   └── Shared/                    # Utilities (string_utils, filters, etc.)
│   └── sync/                          # Sync engine and related utilities
├── tests/                             # Test suites
└── docs/                              # API documentation and guides
```

## Code Style

### File headers

All Python files carry a header with module name, brief description,
class/component info, platform (Python.NET, FieldWorks 9+), and copyright.
Copy the shape from any existing Operations file.

### Operations classes

- Inherit from `BaseOperations`; use its validation methods
- Name as `[Domain]Operations.py` (e.g. `LexEntryOperations.py`)
- Organize by FLEx domain (Grammar, Lexicon, TextsWords, Notebook, Lists,
  System)
- Implement Create / Read / Update / Delete patterns
- Docstrings carry a description, a usage example showing access via
  `FLExProject`, and Args/Returns

### String handling

- Use `normalize_text()` from `Shared.string_utils` for the FLEx null
  marker (`'***'`)
- Normalize empty multilingual string fields to empty strings
- Use `best_analysis_text()` / `best_vernacular_text()` for language
  analysis

### Logging

`logger = logging.getLogger(__name__)`. Keep statements focused on
debugging and issue diagnosis.

### The `flexlibs2` name is a deprecated alias -- never write it in new code

The library was formerly published as `flexlibs2`; it is now **`flexicon`**
(distribution name `pyflexicon`). A `flexlibs2/` package still exists, but
it is an **inbound-only compatibility shim** for external callers
(FlexTools / FlexTrans scripts on disk), and it is **removed in flexicon
v5.0.0**.

Nothing internal may reference it -- not library code, not example
scripts, not docstrings, not tests. Enforced by
`tests/test_flexlibs2_alias_ratchet.py` (issue #240); every internal
reference would become a hard break at the v5.0.0 boundary.

## FLEx-Specific Conventions

### Exception handling

Import from `FLExProject`: `FP_ReadOnlyError`, `FP_NullParameterError`,
`FP_ParameterError`. See `docs/EXCEPTION_HANDLING.md`.

### LCM imports

- Import FLEx types from `SIL.LCModel`
- Use factory and repository interfaces for object creation
- Handle `ITsString` properly for multilingual text

### Same-name fields can have different LCM types across object types

...or not exist at all on the type you'd expect. `Source` is `ITsString`
on `ILexSense`, but `ILexEtymology` has **no `Source` field whatsoever**
(confirmed by live reflection, 2026-08-18; the free-text "source language"
data now lives on `LanguageNotes`, an `IMultiString`), and
`ICmBaseAnnotation` likewise has no `Source` field (that access pattern
belongs to `IStText.Source`, reached via a helper that navigates from the
annotation to its owning text).

Copying a working pattern from one Operations class to another without
checking the field's type -- or existence -- on the *target* LCM interface
is the root cause of issues #36/#39/#40. Current table and correct access
patterns: `docs/API_ISSUES_CATEGORIZED.md`, "Category 8".

### Write operations

Only write if `project.writeEnabled` is True -- lowercase `w`, the
attribute is `writeEnabled`, not `WriteEnabled`. Check write permission
before any Create/Update/Delete. Use the appropriate factory for creation.

## Live LCM Verification (REQUIRED)

**Any change written against the LCM must be verified against a live FLEx
database before it is reported as done.** A mock-only pass is not
verification and must never be presented as one. "No live LCM testing was
performed" is a FAILED verification, not a safety feature -- report it as
`FAIL: unverified`, never as a clean result.

Applies to every change touching an Operations class, a factory call, a
property setter, `FLExProject`, or the transaction/write path. Does not
apply to pure-docs, pure-typing, or pure-test-scaffolding changes.

### The two live write projects

**Reads are unrestricted.** Any project on the machine may be opened
read-only, at any time, with no gate -- which project holds a given element
is not knowable without looking. The table below allocates the two projects
that are safe to **write** to; it is not a list of what may be read.

| Project | Contents | Use for | Restore |
|---------|----------|---------|---------|
| **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate; the default when a test creates its own data | `python scripts/restore_target.py` |
| **Sena 3** | Fully populated example | Safe for reads and edits **in place, at any time**; the right choice when a test needs pre-existing data to modify rather than data it created itself | `python scripts/restore_sena3.py` |

Target is the default for write-path work, not a mandate -- Sena 3 is
equally sanctioned for in-place writes whenever the test needs existing
data. Where a test needs data that does not exist, add it to Target or copy
an existing project; never repurpose or destroy data another test reads.

### Fixtures

- `target_project` -- in-place, write-enabled, on the real Target.
  Capture-and-restore in a `finally:`; prefix created objects `TEST_`.
- `target_sandbox` -- write-enabled on a fresh tempdir copy of the Target
  `.fwbackup`. Nothing can leak. Use for destructive tests, or whenever
  the real Target is locked by an open FieldWorks.
- `sena3_sandbox` -- same, for Sena 3.

Canonical template: `tests/operations/test_target_live_smoke.py`. Copy its
structure.

### The two required invocations

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <your live test file> -m requires_live_project -q
```

Both are required and every brief quotes them explicitly. The offline run is
the gate for non-write-path work; the live run is REQUIRED and performed
unattended -- no human gate -- for any change touching an Operations class, a
factory call, a property setter, `FLExProject`, or the transaction/write
path.

`FLEXLIBS_REQUIRE_LIVE=1` converts every silent degradation into a hard
failure: FLEx init falling back to mocks, a locked Target, a missing
fixture. Without it, `tests/flex_plugin.py` prints `[WARN] MOCK MODE` and
the session still passes green -- which is exactly how unverified
write-path changes have been reported as done.

**Never run bare `pytest` or `pytest --ignore=tests/contract`.** Neither
applies an `-m` filter, so both collect and EXECUTE the ~322
`requires_live_project` tests in-place against real projects.

### Evidence is mandatory

A verification claim must cite machine-checkable evidence, not prose:

1. `tests/live_status.json` must show `"run_mode": "live"`. If it says
   `"mock"`, the run proved nothing.
2. Write `specs/<feature>/evidence/live-<task>.md` containing the exact
   command, the `run_mode` value, the pre-state and post-state values read
   back from the LCM, and the pass/fail line.

"Read back from the LCM" means re-querying the object after the write --
asserting on the value you just passed in proves nothing.

### When live verification is genuinely impossible

Say so explicitly and stop; do not substitute a mock pass. Report the
blocker (locked project, missing FieldWorks, needs a human decision) and
escalate. Per the LEX crew protocol, that is a `needs_human` handoff.

## Testing

- `tests/operations/` for operation-specific unit tests; `tests/test_*.py`
  for integration tests; `flexicon/sync/tests/` for sync engine
- File names: `test_[feature]_[aspect].py` or `test_[module].py`
- Test classes `Test[FeatureName]`; methods
  `test_[what_is_being_tested]_[expected_result]`
- pytest for execution; maintain `.coverage`; check `.pytest_cache/`
  behavior before modifying test infrastructure

## Git Conventions

### Branches

`main` is production-ready code **and the repository's default branch**.
Feature branches reference issues where applicable.

### Commits

Keep commits focused and logical. Include a `Co-Authored-By:` footer when
appropriate.

#### NEVER write close/fix/resolve immediately before an issue number
unless you actually intend GitHub to close that issue.

`closes #N` is the intended convention when a commit genuinely resolves an
issue. The hazard is using one of those verbs in **prose about** an issue
-- GitHub does not read intent, and a possessive or descriptive phrasing
still fires:

```
BAD:   close #243's crew review (T9)      -> actually closed #243
BAD:   fix(x): Fixes #242's P8 anomaly
GOOD:  close the crew review for #243
GOOD:  fix(x): fix the P8 anomaly reported in #242
```

The keyword fires only when the commit reaches the default branch, so it
can lie dormant on a feature branch and trigger on merge. If a crew or
campaign record says an issue is to be left open, that is binding.

Enforced by a `commit-msg` hook. **Enable it once per clone:**

```
git config core.hooksPath .githooks
```

Hazard shapes, the deliberate non-triggers, the backtest against all 801
commits on `main`, and the `Close-Keyword-Override:` escape hatch are
documented in `.githooks/README.md`.

#### Confirm which repo `gh` is talking to before trusting an issue result

Two remotes exist -- `origin` (`MattGyverLee/flexicon`) and `upstream`
(`cdfarrow/flexlibs`, the fork parent). With no default set, `gh` prefers
`upstream`, whose issue numbering tops out near #17, so every issue this
project cites returns "Could not resolve to an issue" -- which reads
exactly like "the issue does not exist." Run
`gh repo set-default MattGyverLee/flexicon` on a fresh checkout, or pass
`--repo` explicitly.

#### Every bug issue carries exactly one priority label: P0, P1, P2 or P3

Apply it at creation (`gh issue create ... --label bug --label P2`), not
later. If you edit an existing untagged bug, tag it as well.

| Label | Meaning |
|-------|---------|
| **P0** | Critical. Corrupts or loses FLEx project data, breaks opening or saving a project, breaks `import flexicon`, or is a security issue. No workaround. Drop everything else. |
| **P1** | High. A public operation fails on every call (always raises, or silently does the wrong thing) in a commonly used area, or an API rests on a wrong premise and needs redesign. Fix next. |
| **P2** | Medium. Broken or a silent no-op on a narrower or less-used path, or a missing wrapper that forces raw LCM access. A workaround exists. |
| **P3** | Low. Hygiene, docs, test-coverage gaps, "verify" tasks with no demonstrated defect, latent traps with no current user impact. |

Calibration examples: #309 (`OverlayOperations.Create` always raises) is
P1; #329 (setters that never reach the LCM) is P2; #281 (stranded
`import logging`) is P3. If you are unsure between two levels, pick the
higher one and say so in the issue body.

### Before committing

Verify style, confirm operations use BaseOperations validation, ensure
error handling uses the FLEx-specific exceptions.

## API Design Philosophy

Core principle: **user-centric, not technology-centric.** The API should
match how users think about objects, hiding LCM/pythonnet complexity while
maximizing functionality.

The six binding rules, each with worked before/after examples, the wrapper
and smart-collection patterns, and the casting standards are in
**`docs/API_DESIGN_PHILOSOPHY.md`**. In short:

1. **Hide interface/ClassName/casting complexity.** Operations classes
   cast internally. `cast_to_concrete()` is public (issue #271) but is the
   escape hatch, not the primary remedy.
2. **Maximize functionality in simple queries.** `GetAll()` returns
   everything with type diversity visible.
3. **Unify operations across types.** One `filter()` across all concrete
   types, not one per type.
4. **Provide smart properties and capability checks** (`has_output_specs`)
   instead of `ClassName` tests and manual casts.
5. **Don't add a flag for behaviour that should be unconditional.** A
   keyword whose `False` default preserves a bug is the anti-pattern; a
   genuinely call-site-dependent flag is fine.
6. **Warn on type mismatch, don't block.** Show the consequences and let
   the user decide.

Before changing `BaseOperations` validation, `FLExProject` core, module
structure, the API surface, wrapper/collection patterns, or the casting
architecture, read the relevant doc first:

- `docs/ARCHITECTURE.md` -- wrapper + collection overview
- `docs/ARCHITECTURE_WRAPPERS.md` -- wrapper classes guide
- `docs/ARCHITECTURE_COLLECTIONS.md` -- smart collections guide
- `docs/API_DESIGN_PHILOSOPHY.md` -- design rules and casting standards

## Documentation

- HTML API docs are generated and reachable via `flexicon.APIHelpFile`
- Keep docstrings accurate with parameter descriptions
- Update `docs/API_ISSUES_CATEGORIZED.md` when API behaviour changes
- Document breaking changes in the migration guide
- Comment non-obvious FLEx behaviour and LCM workarounds (e.g. null marker
  handling)

## Key Files

- `flexicon/code/BaseOperations.py` -- parent class, shared validation
- `flexicon/code/FLExProject.py` -- main project interface
- `flexicon/code/Shared/wrapper_base.py` -- `LCMObjectWrapper` base
- `flexicon/code/Shared/smart_collection.py` -- `SmartCollection` base
- `flexicon/code/Shared/string_utils.py` -- text normalization
- `flexicon/code/lcm_casting.py` -- casting utilities. `cast_to_concrete`
  is exported from the package top level and is public (issue #271); the
  rest (`clone_properties`, `validate_merge_compatibility`, the interface
  cache) is internal.
- `flexicon/code/PythonicWrapper.py` -- suffix-free property access
- `README.rst` -- user-facing documentation

## Don'ts

- This is a Windows system; no emojis in console messages. Use `[OK]`,
  `[DONE]`, `[PASS]`, `[ERROR]`, `[FAIL]`, `[INFO]`, `[NOTE]`, `[WARN]`,
  and dashes or asterisks for bullets.
- Call Python with `python`, not `python3`.
