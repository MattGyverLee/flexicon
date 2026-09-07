# Cycle 1 - GramTrans call-site audit: is a source GUID in scope?

Note: produced by the Explore agent in enforced read-only mode (no Write
tool); the main session persisted it verbatim to this path.

Consumer repo audited: `D:\Github\_Projects\_LEX\GramTrans` (branch main).
Stale worktrees ignored.

## Verdict table

| # | Call site | Source GUID in scope? | Effort |
|---|-----------|----------------------|--------|
| 1 | `wordforms.py:198` `agent_ops.Create(_AGENT_NAME)` | NO | small plumbing (~5 lines) |
| 2 | `reversals.py:559` `ReversalIndexes.Create(ws, ws)` | NO | small plumbing (~6 lines) |
| 3 | `reversals.py:642` `ReversalEntries.Create(...)` | YES | immediately usable |

## CALL SITE 1 - `wordforms.py:198` - GUID NOT in scope. Needs plumbing (small).

- `decision` is `models.ProvisionedAgent`, defined at
  `GramTrans\src\gramtrans\Lib\models.py:1627-1632`. Fields are only
  `target_agent: Any` and `created: bool`. No source-side GUID field.
- Producer is `wordforms.plan_agent(target, ctx)` at `wordforms.py:146-182`.
  It only ever reads `target.Agents` (`GetHumanAgents`, then
  `FindByType(True)`), constructing
  `ProvisionedAgent(target_agent=existing, created=existing is None)` at
  `wordforms.py:178-180`. The SOURCE project's agent is never fetched, so no
  source agent object survives into `apply_agent`.
- Only caller: `texts.py:748-749`.
- Caching: `plan_agent` stashes `ctx._wf_agent_decision`
  (`wordforms.py:152-154, 181`); `apply_agent` stashes `ctx._wf_agent`
  (`wordforms.py:191-193, 206`). Both per-run, so the guid would be consumed
  at most once -- no dedup conflict.
- Cheap fix: `ctx.source_handle` (the source FLExProject) is already the house
  accessor and is reachable inside both functions without a signature change
  -- cf. `wordforms.py:1140`, `wordforms.py:1267`, `texts.py:1325`,
  `reversals.py:929`. So a `source_agent_guid: str = ""` field on
  `ProvisionedAgent`, populated in `plan_agent` from
  `ctx.source_handle.Agents`, is ~5 lines.

## CALL SITE 2 - `reversals.py:559` - GUID NOT in scope. Needs plumbing (small).

- `ReversalDecision` (`models.py:1216-1278`) carries `source_entry_guid`,
  `target_index_ref`, `target_ws_id`, ... but no source *index* guid. Only ws
  ids reach `_ensure_target_index`.
- The source index object IS available one level up, at plan time:
  `plan_reversals` iterates `src_index` at `reversals.py:451` and already
  computes `references._guid_str(src_index)` at `reversals.py:464` and `:468`
  for the drop record. It is simply not propagated into
  `_build_entry_decision` (`reversals.py:474-478`) or the
  `ReversalDecision(...)` construction (`reversals.py:380-389`).
- Fix: add `source_index_guid: str = ""`, thread through
  `_build_entry_decision`. Two files, ~6 lines.

## CALL SITE 3 - `reversals.py:642` - GUID IS in scope. Immediately usable.

- `decision.source_entry_guid` is live in that exact function and already used
  at `reversals.py:627`, `:631`, `:646`, `:650`, `:654`. A
  `guid=decision.source_entry_guid or None` kwarg needs zero upstream
  plumbing.
- The sibling `_create_sub_entry` already does exactly this via the raw
  factory: `owned._create_owned_via_factory(factory,
  decision.source_entry_guid, "ReversalIndexEntry")` at
  `reversals.py:717-718`, with the 033 rationale comment at `:714-716`. The
  docstring at `reversals.py:614-616` explicitly names the missing wrapper
  `guid` param as the reason the top-level path diverges -- a `guid=` addition
  closes that documented gap.

## House pattern for `guid=`

Established. Representative line, `texts.py:829-831`:

```python
return text_ops.Create(name, None,
                       guid=plan.source_guid or None,
                       contents_guid=getattr(plan, "contents_guid", None) or None)
```

Same shape at `wordforms.py:664-665` (`gl_ops.Create(..., guid=gplan.source_guid or None)`),
`wordforms.py:998` (`wa_ops.Create(wordform, guid=plan.source_guid or None)`),
`wordforms.py:1085-1086`, `wordforms.py:1201`, `texts.py:1214`
(`para_ops.Create(..., guid=guid)`). Convention is always keyword-only,
`or None` fallback, wrapped in the module's `_safe`/except-Exception guard.

## Which flexicon the venv resolves

GramTrans has no `.venv`; it runs on the system interpreter
`D:\Apps\anaconda3\python.exe`. `import flexicon` resolves to
`D:\Github\_Projects\_LEX\flexicon\flexicon\__init__.py` via an **editable
install**: `D:\Apps\anaconda3\Lib\site-packages\__editable__.pyflexicon-4.3.1.pth`
plus `__editable___pyflexicon_4_3_1_finder.py`, dist-info `pyflexicon-4.3.1`.

**A library change in the flexicon repo is picked up with no reinstall.**
Matches the documented setup in `GramTrans\CLAUDE.md:70-76` and the
`pyflexicon>=4.3.1` floor in `GramTrans\pyproject.toml`.

## Pre-existing dedup logic in reversals.py

No GUID-based dedup anywhere in the module -- dedup is **by form**, which a
`guid=` param would sit alongside, not duplicate:

- `_find_existing_entry_by_form` (`reversals.py:585-604`) matches on
  `ReversalForm` alt equality; called from `_create_top_level_entry` at
  `:635-640` and `_create_sub_entry` at `:706-711`, both returning the
  existing entry before any create.
- `_ensure_target_index` dedups indexes by `target_ws_id` via
  `resolver_cache[_INDEX_CREATED_KEY]` (`reversals.py:553-556`, key defined at
  `:499`), because `ReversalIndexOperations.Create` raises
  `FP_ParameterError` on a duplicate WS (`:544-549`).

Interaction note: at call site 3 the form-dedup runs *first*, so on a repeat
Move the reused entry wins and `guid=` is never reached -- no conflict, but
also no guid repair of entries created by an earlier guid-less run. At call
site 2, a `guid=` on index create could collide with an index the ws-keyed
cache did not see; the existing `except Exception` at `:560-574` already
degrades to a `DroppedItemRecord` rather than raising.
