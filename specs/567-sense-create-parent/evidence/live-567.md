# Issue #567 -- live evidence (Target sandbox)

## Design (lex-lead ruling)

`Senses.Create` is canonical over an entry-or-sense parent,
discriminated by ClassName (HVO included); `CreateSubsense` and
`LexEntry.AddSense` are thin delegating wrappers that narrow their
contracts (a provably-wrong parent type raises FP_ParameterError
naming the right method). This closes the latent trap where both
ILexEntry and ILexSense expose SensesOS, so Create(sense) silently
made a subsense and CreateSubsense(entry) silently made a top-level
sense. Mocks/stand-ins with no usable ClassName keep the historical
entry path. Precedents: POS Create(parent=None) + AddSubcategory
(#547); SemanticDomains.Create(parent=None).

Note: this branch is based on origin/main, which backed out the
#338 default publication exclusion (3d4b07d) -- new senses publish
everywhere, and no exclusion call was carried into the canonical
Create.

## Commands

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_567_sense_create_parent_live.py -m requires_live_project -q
python -m pytest tests/operations/test_issue338_publication_defaults_live.py tests/operations/test_lexicon_brackets_live.py tests/operations/test_lexentry_duplicate.py -m requires_live_project -q
python -m pytest -m "not requires_live_project" -q
```

Worktree: `C:/Github/flexicon-547`, branch `fix/567-sense-create-parent`.

## Result

- 567 live file: `7 passed` (Create with sense parent, sense-HVO
  parent, entry parent unchanged, CreateSubsense delegation +
  entry-parent rejection, AddSense delegation + sense-parent
  rejection).
- Neighbouring live suites: `34 passed, 1 xfailed` (publication
  defaults, lexicon brackets, LexEntry duplicate via AddSense).
- Offline suite: `2575 passed` (includes the
  write-path-transaction ratchet; both delegation sites carry
  their own `_TransactionCM` brackets per D5, B1 nesting).
- `tests/live_status.json` `run_mode`: `live`.

## Pre-state / post-state (read back from the LCM)

- `Create(sense, gloss)` re-read via `GetSubsenses(parent)` ==
  `[child]` and `GetParentSense(child) == parent`;
  `GetParentSense(parent) is None`.
- `CreateSubsense(entry)` / `(entry.Hvo)` raises FP_ParameterError
  with nothing written (gloss absent on re-read); same for
  `AddSense(sense)` / `(sense.Hvo)`.
- All created entries deleted (senses cascade).

## Pass/fail

PASS -- live-verified on the Target sandbox.
