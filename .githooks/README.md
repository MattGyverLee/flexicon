# Git hooks

## Enable them once per clone

`core.hooksPath` is local config, not something a checkout can carry:

```
git config core.hooksPath .githooks
```

## commit-msg: the close-keyword guard

`commit_msg_guard.py` blocks commit messages that would make GitHub close
an issue you did not intend to close. It is covered by
`tests/test_commit_msg_guard.py`.

### The hazard it exists for

`closes #N` is the intended convention when a commit genuinely resolves an
issue, and is used that way in 100+ commits on `main`. The hazard is using
one of those verbs in **prose about** an issue. GitHub does not read your
intent, and a possessive or descriptive phrasing still fires:

```
BAD:   test(243): pin the fail-open branch; close #243's crew review (T9)
       -> GitHub parsed "close #243" and CLOSED issue #243, against an
          explicit ruling that it stay open. This really happened
          (commit b0e3d14); see specs/242-paragraph-whitespace/spec.md
          section 6 and evidence/n7-issue-state.md.
BAD:   fix(x): Fixes #242's P8 anomaly
GOOD:  test(243): pin the fail-open branch; close the crew review for #243
GOOD:  fix(x): fix the P8 anomaly reported in #242
```

The keyword fires only when the commit reaches the default branch, so it
can lie dormant on a feature branch and trigger on merge. If a crew or
campaign record says an issue is to be left open, that is binding: phrase
around the verb.

### What it blocks, and what it deliberately does not

The guard blocks only four hazard shapes:

1. a **negation** -- "do NOT close #250"
2. a **possessive** -- "close #243's crew review"
3. a **quotation** -- `said "partially closes #151"`
4. **narration** of a close that already happened

The genuine convention is deliberately untouched: a close keyword in a
footer (`Closes #N.`) or a subject parenthetical
(`feat(x): y (closes #N)`) always passes, and a negation elsewhere on such
a line does not trigger the guard.

### Backtest

Run against all 801 commits on `main`: 136 contain a close keyword, 130
pass, and the 6 it blocks are all genuine hazards -- the three that
actually fired (#242, #243, #250), two `does not close #237` bodies, and
one quoted directive.

### Overriding it

If a prose form is genuinely intended, say so explicitly rather than
disabling the hook:

```
Close-Keyword-Override: <why this should genuinely close the issue>
```
