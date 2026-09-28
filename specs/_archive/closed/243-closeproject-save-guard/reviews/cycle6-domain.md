# Domain Expert Review — Issue #243 Adjudication (Cycle 6)

## Q1 — Is custom-field editing genuinely blocked on a shared project?

**REFUTED (as stated).** Custom field creation/deletion in real FieldWorks is a schema (MetaDataCache) mutation, and FLEx's own UI does gate it — but the gate is a **local in-process transaction-state check**, not a **sharing/multi-user** check. Send/Receive (Chorus/FLEx Bridge) propagates model changes exactly like any other change set; a custom field added by one S/R participant merges into other clients' projects on the next sync, same as any other CmObject change — S/R has no special "custom fields forbidden" rule. LAN-shared (ShareMyProjects) FLEx does warn users that concurrent editing while another client has the project open is risky in general, but that risk is not specific to custom fields — it's the same generic "don't edit the same project from two live clients at once" caution that applies to any write. The user's premise conflates "FLEx's UI refuses to let you add a custom field while you're mid-edit of a record" (transaction-depth restriction) with "sharing forbids it" (false).

## Q2 — Are there other operations that genuinely need exclusivity?

**PARTIALLY TRUE / premise incomplete.** Several other operations are exclusivity-sensitive for reasons independent of custom fields, meaning "custom fields are the only edit that can't be done shared" is factually incomplete even by the domain's own standards:

- **Writing-system add/remove/change** — also a MetaDataCache/LangProject-level mutation with knock-on renumbering of WS handles; same class of hazard as custom fields, arguably worse because WS handles are cached by ID across the whole in-memory object graph.
- **Model migration on version upgrade** — explicitly single-client by design; FLEx refuses to open a project needing migration if another process holds it, and S/R will not sync a migrated model back to un-migrated peers until they also upgrade.
- **Project rename/relocation** — filesystem-level, inherently exclusive; nothing to do with LCM transactions per se but genuinely requires no other client have the file open.
- **Possibility-list restructuring** (especially deleting/moving list items with wide references) — not schema-level, but can produce dangling reference corruption under concurrent access; same risk shape as any wide-reference delete.
- **Deleting objects with wide references** — general LCM referential-integrity hazard, not custom-field-specific.

So the user's "only edit" claim should be corrected to: custom fields are *one instance* of a broader class (schema/metadata mutations + version-sensitive operations), not a unique case.

## Q3 — Is the refusal in CustomFieldOperations.py about sharing, or about transaction depth?

**CONFIRMED: purely transaction depth, not sharing.** `CustomFieldOperations.py:280-325` (guard at line 306: `getattr(action_handler, "CurrentDepth", 0) > 0`) checks the local `IActionHandler`'s open-UnitOfWork state — this is per-process, in-memory state entirely independent of whether the project is shared. The cited issue #21 mechanism (raw `IFwMetaDataCacheManaged.AddCustomField` inside an active task creates the field in memory only; subsequent `SetValue` calls reference a field that never persists to disk, corrupting the project on next FLEx UI open) is a **single-user, single-process** corruption path.

**Yes/no answer: yes, the #21 corruption would still occur** on a fully exclusive, non-shared project if the schema mutation happened while `CurrentDepth > 0` — exclusivity does nothing to prevent it, because the bug is about UoW/task nesting order in one process, not about a second writer. This is the key finding: the guard's rationale text (lines 292-298) correctly names transaction depth as the cause and never invokes sharing at all; the user's phrasing about "shared projects" is not what this guard is protecting against.

## Q4 — What does "without sacrificing shared-project edits" correctly constrain, given the SaveChanges/RefreshFromDisk hazard?

**CONFIRMED hazard, and yes, a blanket depth guard would break the documented recovery workflow.** `FLExProject.py:758-800`'s `RefreshFromDisk()` exists specifically because another client (typically FLEx itself, opened on the same project in shared mode) can wedge auto-save via LCM's pending-reconciliation guard (`UnitOfWorkService.cs:245`), and its shipped `Example` (lines 792-797) is `RefreshFromDisk()` immediately followed by `SaveChanges()` — called back-to-back, no intervening `EndUndoTask`/`EndNonUndoableTask`.

Under **`undoable=False`**, `CurrentDepth` is pinned at 1 for the entire session (`BeginNonUndoableTask()` at `OpenProject()`, not closed until `CloseProject()` — `FLExProject.py:310`, `CurrentDepth` docstring lines 466-478), so a blanket `CurrentDepth > 0` refusal on `SaveChanges()` would **always** fire in that mode and permanently break the documented recovery sequence — exactly the scenario the user is worried about sacrificing.

Under `undoable=True` (default since 4.4.0), depth sits at 0 between operations and 1 only inside an active `UndoableOperation` block, so the same guard would correctly allow the recovery call as written (both calls happen outside any open block) and only refuse `SaveChanges()` called mid-operation — which is the actually-unsafe case.

**Correct constraint:** any depth guard added to `SaveChanges()` must be conditioned on `undoable` mode (or exempt the `undoable=False` session-envelope depth of 1 from the check), not a flat `> 0` refusal, or it silently disables the shared-project reconciliation path FLExProject.py:758-800 exists to provide.

---

**Reviewed By:** Domain Expert Agent (cycle 6)
**Persisted by:** main session (lex-domain has no Write tool)

## MAIN-SESSION NOTE — unresolved conflict flagged for /lex-lead

Q4's conclusion appears to conflict with the Phase 1 analysis in lex-lead's own
cycle-6 planning message, and the conflict is material to the guard's shape:

- **Q4 above** says a blanket `CurrentDepth > 0` guard "would **always** fire" under
  `undoable=False` and so "permanently break the documented recovery sequence."
- **But per C16 / probe P-7**, mid-session `SaveChanges()` under `undoable=False`
  *already* always raises `Commit at wrong place.` and destroys the change set
  (measured 0/25 in memory, before `CloseProject()` is entered). If that is right,
  the `RefreshFromDisk()` -> `SaveChanges()` recovery workflow **cannot work today**
  in that mode, so a refusal there would not be sacrificing a working edit — it
  would replace a destructive failure with a safe one.

Both cannot be true. Either the recovery workflow is already broken under
`undoable=False` (making a blanket guard harmless there), or there is a path by
which `SaveChanges()` succeeds at depth 1 that P-7 did not exercise. This is
exactly what T8a/P-10 measures. Adjudicate against the P-10 evidence, not against
either prose account.
