# T11 Archivist — Issue #326: Phonological Wrapper Members

Worktree `C:/Github/flexicon-326`, branch `fix/326-phonological-wrapper-members`.
This task landed the tree; no production code or tests were edited except a
CHANGELOG amendment noted below.

## Preflight

- `git config core.hooksPath` → `.githooks` (already set locally; not changed globally)
- `gh repo set-default MattGyverLee/flexicon` → `MattGyverLee/flexicon`
- `git status -sb` at start: this branch in this worktree

## Commits

Commits 2 and 3 were combined: `phonological_rule.py` mixed metathesis and
redup hunks, and interactive `git add -p` is unsupported.

| SHA | Subject | commit-msg hook |
|---|---|---|
| `46db663483af89b8027ffee477a59519761197b1` | `fix(phonology): read FeatureStructureRA for context segment and natural_class` | **PASS** |
| `d5bb0203dc3ac8b49cad5f4fcc4af5dad1d92cab` | `fix(phonology): derive metathesis parts from StrucDescOS; deprecate redup APIs until v5.0.0` | **PASS** |
| `322c9a86f5ca21954ef355de008bf2ae6de25dc2` | `test(phonology): cover metathesis, context links, and redup deprecation` | **PASS** |
| `adfb976c501e45647dab6a625a169b6d7971736c` | `docs(phonology): document real LCM members for contexts and metathesis` | **PASS** |
| `19869247e85ce637a743d8f0d636576ba8e97ff5` | `chore(326): changelog and crew evidence; closes #326` | **PASS** |

`--no-verify` was not used. `Close-Keyword-Override` was not used. Only the
final landing commit uses `closes #326`.

## CHANGELOG verify/amend

T7 already had an `[Unreleased]` entry covering:

- **BREAKING (behavioural)** `metathesis_parts` repair (`StrucDescOS` + switch indices)
- `segment` / `natural_class` now return real objects via `FeatureStructureRA`
- `has_redup_parts` / `redup_parts` / `as_reduplication_rule` / `redup_rules` deprecated with `DeprecationWarning`, removed in v5.0.0

**Amended:** one paragraph stating the internal `IPhReduplicationRule` slot
was removed from the `lcm_casting` interface cache. No duplicate T7 entry.

## history.md

**Skipped.** This repo's `history.md` records version cuts and campaign-scale
judgements, not each non-upstream issue landing. `CHANGELOG.md` is the
per-issue record.

## PR

https://github.com/MattGyverLee/flexicon/pull/355

Created with `--repo MattGyverLee/flexicon --base main --head fix/326-phonological-wrapper-members`.
Not merged.

## Untracked files left on disk

- `tests/operations/test_issue326_t8_verification_live.py` (evidence-only T8 scratch; intentionally not committed)
- This report (`T11-archivist.md`) is added in a follow-up commit after the PR exists, per task instruction
