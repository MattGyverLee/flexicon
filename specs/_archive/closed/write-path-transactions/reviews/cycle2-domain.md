# Domain Expert Review — Save Cadence, Shared Mode, RefreshFromDisk, Conflicting Save

**Date:** 2026-08-14
**Reviewer:** Domain Expert Agent (FLEx/linguistics)
**Cycle:** 2

> Persistence note: the lex-domain agent definition grants Read/Grep/Glob/WebFetch
> only, with no write-capable tool, so this report was returned inline and written
> to this path by the orchestrator. Content is the agent's verbatim assessment.
> The agent-definition gap should be fixed before the next domain dispatch.

## Q1 — Save Cadence

`UnitOfWorkService.SaveOnIdle` (liblcm `UnitOfWorkService.cs:226-262`) only fires when
the FSM is back at `ReadyForBeginTask` (line 240), no undo-stack mark is open (251), 10s
have passed since the last save (255), and the user has been idle 2s (258, waived after
5 min busy). In `undoable=False`, flexicon holds one `BeginNonUndoableTask()` open for
the whole session (`FLExProject.py:236-241/255-257`), so the FSM never returns to
`ReadyForBeginTask` and none of this ever runs — nothing reaches disk until
`CloseProject()`.

From the user side, watching a shared-mode FLEx window during a headless run: a long
silent run that then dumps everything at close is *worse*, not better, for two
linguist-relevant reasons. First, a linguist doing Send/Receive or co-editing expects to
see colleagues' work land incrementally — a session that appears to do nothing for
twenty minutes then flushes 2,000 entries at once looks like a hang or a corruption
event, not progress. Second, and more serious: if the script crashes at entry 1,500 of
2,000, a FLEx user's mental model of "undo/save" gives them nothing to recover — the
entire session's work is gone, because it was never committed. That is a materially
worse failure mode than "I lost the last edit," which is what a linguist is trained to
expect from any editor.

A partially-applied dataset visible mid-run is acceptable to a linguist — it is exactly
what Send/Receive and multi-user FLEx already trains users to expect (colleagues'
partial batches showing up over time). What is not acceptable is a crash that loses
everything with no visible trace it ever ran.

**Recommendation:** per-operation save cadence (i.e., `undoable=True` + Track B
per-operation brackets) is the only mode a linguist should be asked to trust for any run
long enough to matter; `undoable=False` should be positioned as short-lived,
single-process, non-interactive only.

## Q2 — Shared Mode

Spec D3 is correct and I concur without reservation. Shared mode's `ChangeReconciler`
machinery is explicitly built around the undo stack (rewriting before-states so foreign
work "predates" local work so it can still be undone). `undoable=False`'s session-long
non-undoable envelope is precisely the stack the reconciler cannot revert, and it
maximizes the unsaved/conflict window to the entire run. A linguist working alongside a
headless script in Send/Receive mode has no way to know their unsaved edits are sitting
in a footprint that grows for the whole run — that is an unacceptable, invisible risk to
their own concurrent work.

**Recommendation:** promise: shared-mode-safe operation only under `undoable=True` with
per-operation brackets (D2/B1/B2 landed). Prohibit: `undoable=False` whenever a project
may be open elsewhere or under Send/Receive — this should be an enforced precondition,
not a documentation note.

## Q3 — RefreshFromDisk

This matches a real, common linguist workflow: two people (or a linguist plus a script)
working the same project, one saving from FLEx while the other's session is live.
Without `Refresh()`, one foreign save permanently wedges the headless session's saving
for the rest of the run — a failure a user would never diagnose from the outside; they'd
just see a script that "silently stopped saving." Requiring `writeEnabled=True` is
correct and defensible: a read-only session cannot accumulate a pending-reconciliation
block in the first place (there's no open UnitOfWork to reconcile against), so gating
matches `SaveChanges()`'s existing precedent and avoids exposing a no-op on read-only
sessions.

**Recommendation:** ship as-is; document explicitly that this is the headless equivalent
of clicking FLEx's Edit > Refresh, and that scripts running against a possibly-shared
project should call it proactively after any detected external change, not just
reactively after a wedge is discovered.

## Q4 — Conflicting Save

Raising `FP_ConflictingSaveError` is the right behaviour for headless code — a linguist
running a script unattended cannot answer a modal dialog, and `SilentLcmUI`'s
unconditional discard is worse: it would silently throw away the script's (or,
transitively, the linguist's) work with no trace. An exception is the one channel that
reaches the script author.

What the script author needs to be told, concretely: stop, do not retry blindly, and
either (a) abandon the run and re-open the project fresh, replaying only the unapplied
portion, or (b) close without saving and manually reconcile in FLEx's own UI where a
human can inspect what collided. The error message already says this; it should
additionally point at `RefreshFromDisk()` as the recovery step once the foreign change
has been reconciled, and make clear that a caught `FP_ConflictingSaveError` means real
object-level data collided (per `ChangeReconciler.OkToReconcileChanges`) — not a
spurious lock — so re-running without addressing the underlying concurrent edit will
fail again.

**Recommendation:** approve current raise-based design as-is; add to script-author
guidance that catching this exception should trigger a full stop + re-open, not an
automatic retry loop.

---

**Domain score:** 92/100 — terminology and workflow reasoning are sound and match how
linguists actually use FLEx/Send-Receive; the one gap is tooling on the agent's end to
persist this to the reviews path (see note above), not a domain finding.
