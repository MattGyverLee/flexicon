# Status -- issue #285, headless UI default

Branch: `fix/285-headless-ui-default` (NOT pushed, no PR opened).
Spurt 1 complete, 3 crew cycles. All quality gates green.

Note: this repo has no root `STATUS.md`; the crew handoff for this feature
lives here and in `.crew-handoff.json` alongside it.

## What landed

| Commit | Contents |
|---|---|
| `4526245` | Defects 1-3: `ui=None` -> bare `HeadlessLcmUI()` (`FLExLCM.py:102-103`); `HeadlessLcmUI` exported top level (`__init__.py:118`); CHANGELOG entry; five doc/docstring sites; regression test inverted plus two new tests |
| `2d7356a` | Cycle-1 spec artifacts (domain + verification reports, pre-fix evidence) |
| `d2ff8ff` | Merge of `origin/main` (`068571d`, PR #286 / issue #249); both `[Unreleased]` CHANGELOG entries preserved |
| `49f22b2` | Domain follow-ups: `OfferToRestore` disclosed in CHANGELOG; `SynchronizeInvoke is None` contingency pinned in-tree |
| `b61aa8a` | `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` section 5 stale claim marked SUPERSEDED (pure addition, history preserved) |

## Gates

- Offline suite: **1728 passed / 0 failed / 693 deselected**
  (`python -m pytest -m "not requires_live_project" -q`)
- Live verification: **PASS, both sides**, `run_mode: live` on each half.
  - Pre-fix (`evidence/live-prefix-conflict.md`, worktree `8e657e8`): a genuine
    LCM conflict was staged via `BackendProviderType.kSharedXML` on a tempdir
    copy of Target with two concurrent `LcmCache` writers. `ui=None` produced a
    **silent discard** in a bare-script context and a reproducible **>105s
    block** under the mandated pytest invocation -- the issue's "either blocks
    or silently discards" measured as *both*, selected by invocation context.
  - Post-fix (`evidence/live-postfix-conflict.md`, worktree `4526245`):
    `ui=None` raises `FP_ConflictingSaveError`, and the session's edit was
    confirmed still intact by re-query of a freshly re-fetched object -- so
    the exception message's "unsaved changes were NOT discarded" claim is
    measured, not merely asserted. Explicit `FwLcmUI` still reaches the
    historical path, so the opt-out is real.
- QC: **90/100** APPROVE-WITH-NITS; sole P1 cleared in `b61aa8a`.
  (Run via a seeded `general-purpose` agent -- `lex-qc` is not dispatchable
  as an Agent `subagent_type` in this session. See "Open items".)
- Domain: **PASS**. No realistic caller's *correct* behaviour depended on the
  `FwLcmUI` default. One real non-`ConflictingSave` delta found and disclosed
  (`OfferToRestore`); `Retry` and the three linked-files members proved
  unreachable from flexicon's only call site.

## Open items -- user decision required, deliberately not done

1. **Push + PR.** The user asked only that #285 be resolved on a branch, so
   the branch is unpushed and no PR exists. The `Closes #285.` footer is
   dormant until merge, by design.
2. **`ProgressDialogWithTask(th)` (`flexicon/code/FLExLCM.py:109`) -- unfiled
   follow-up.** Found by QC's pattern-audit sweep as an unswept sibling of the
   same "headless-hostile UI on the open path" axis. It is a *distinct* hazard
   from #285 (resource allocation + leak, not a data-discard branch) and needs
   its own live evidence, so #285 was deliberately not widened. Facts already
   traced: the `IThreadedProgress` parameter is mandatory
   (`liblcm/src/SIL.LCModel/LcmCache.cs:137`); construction is not inert --
   the private ctor (`ProgressDialogWithTask.cs:75`) calls
   `InitOnOwnerThread()`, which creates a `BackgroundWorker` and a real
   WinForms `Form` and force-creates the Win32 handle; the object is
   `IDisposable` and is never disposed, leaking a handle per `OpenProject`;
   it is latent rather than active only because the open path never drives
   `Message`/`Step` and nothing calls `Invoke` on it; and FieldWorks contains
   four separate hand-rolled `NullThreadedProgress` classes solving exactly
   this problem for headless console tools. Inherited from upstream
   `cdfarrow/flexlibs` (traces to Initial commit `532325aa`), not introduced
   here. Only the user authorizes opening an issue.
3. **`lex-qc` roster gap.** `C:\Users\thoua\.claude\agents\lex-qc.md` exists
   with valid frontmatter but the Agent tool rejects the `subagent_type`;
   it is registered only as a Skill. Surfaced, unfixed.
