# Cycle 1 -- lex-domain: ILcmUI member behaviour delta for issue #285

Note: authored by lex-domain (read-only toolset: Read/Grep/Glob/WebFetch, no
Write). Transcribed to disk by the main session verbatim from the agent's
return, so lex-lead can read it by path.

Sources read:
- `D:\Github\_Projects\_LEX\liblcm\src\SIL.LCModel\...` (liblcm core; confirms
  the actual LCM call sites)
- `D:\Github\_Projects\_LEX\FieldWorks\Src\FdoUi\FwLcmUI.cs` (the WinForms
  implementation being replaced as default)

## Member-by-member behaviour delta (`SIL.LCModel.ILcmUI`)

### `SynchronizeInvoke`

- **FwLcmUI:** real `ISynchronizeInvoke` (a `ThreadHelper` message-pump thread).
- **HeadlessLcmUI:** `None`.
- **Delta:** two liblcm sites dereference it unguarded --
  `UnitOfWorkService.SendPropChangedNotifications` (`UnitOfWorkService.cs:537`,
  and via `UnitOfWork.cs:307/422`, `UndoStack.cs:343`) and
  `UndoStack.DoTasksForEndOfPropChanged` (`:383`). Both are empty/no-op for a
  flexicon session: `ChangeInformation.HasNotifier` is true only for
  `IPropertyChangeNotifier`, whose sole liblcm implementer is `Scripture`
  (`DomainImpl/Scripture.cs`); the subscriber list is populated only via
  `AddNotification`, which nothing in a headless run calls.
  `DoTasksForEndOfPropChanged`'s task queue is filled only from a narrow
  re-entrant path (`NonUndoableUnitOfWorkHelper.DoSomehow`'s postponed-task
  constructor), reachable only *from inside* a PropChanged subscriber callback
  -- also empty.
- **Acceptable:** yes for the current flexicon surface (no
  Grammar/Lexicon/TextsWords/Notebook/Lists/System op registers a
  change-watcher or touches Scripture). Flag as residual risk if a future
  feature adds an `IVwNotifyChange` subscriber.

### `LastActivityTime`

- **FwLcmUI:** real timestamp via `UserActivityMonitor`.
- **HeadlessLcmUI:** real timestamp, updated by explicit `TouchActivity()`.
- **Delta:** feeds `SaveOnIdle`'s autosave-defer heuristic; a long headless run
  that never calls `TouchActivity()` may autosave sooner.
- **Acceptable:** yes -- non-destructive (an earlier autosave, never a lost
  one).

### `TouchActivity`

- Not part of `ILcmUI`; absent from `FwLcmUI` too. HeadlessLcmUI-only
  convenience hook, with no LCM call site at all. N/A.

### `ConflictingSave`

- **FwLcmUI:** modal `ConflictingSaveDlg`, dangerous polarity (anything but OK
  results in a discard).
- **HeadlessLcmUI:** raises `FP_ConflictingSaveError` (or returns False); never
  discards.
- **Delta:** already the issue's subject.
- **Acceptable:** yes -- this is the point of #285.

### `DisplayMessage`

- **FwLcmUI:** modal `MessageBox` via `Invoke`.
- **HeadlessLcmUI:** `logger.log`.
- **Delta:** the message goes to the log, not a dialog.
- **Acceptable:** yes -- purely informational; also removes the documented
  `m_helpTopicProvider == null` NRE.

### `ReportException`

- **FwLcmUI:** modal `ErrorReporter.ReportException` via `Invoke`.
- **HeadlessLcmUI:** `logger.error`, returns False.
- **Delta:** no dialog; the return value is ignored everywhere anyway -- all
  three liblcm call sites (`CmObjectSurrogate.cs:586`,
  `DomainObjectServices.cs:473`, `:527`) discard the return and always
  `break`/fall through regardless.
- **Acceptable:** yes -- the return value is dead code in liblcm, so no
  retry/abandon logic depends on it.

### `ReportDuplicateGuids`

- **FwLcmUI:** modal dialog via `Invoke`. **HeadlessLcmUI:** `logger.error`.
- Log instead of dialog; informational, void return. Acceptable.

### `DisplayCircularRefBreakerReport`

- **FwLcmUI:** modal `MessageBox` via `Invoke`. **HeadlessLcmUI:**
  `logger.warning`.
- Log instead of dialog; informational. Acceptable.

### `Retry`

- **FwLcmUI:** modal Retry/Cancel `MessageBox`.
- **HeadlessLcmUI:** always returns False (declines).
- **Delta:** **zero call sites anywhere in liblcm's own source** -- only ever
  called from FieldWorks application-layer code outside `SIL.LCModel`, never
  reached via `LcmCache.CreateCacheFromExistingData`.
- **Acceptable:** yes -- a dead path for flexicon.

### `OfferToRestore` -- THE ONE REAL FINDING

- **FwLcmUI:** modal Yes/No; Yes auto-swaps the `.bak` over the corrupt file.
- **HeadlessLcmUI:** always declines (logs, returns False).
- **Delta:** **genuinely reachable.** Called from `XMLBackendProvider`'s private
  `OfferToRestore()` (`XMLBackendProvider.cs:272/279/285`), triggered when the
  `.fwdata` fails to parse (`ArgumentException` / `XmlException` /
  `IOException`) *and* a sibling `.bak` exists -- squarely inside the normal
  load path used by `CreateCacheFromExistingData`. FwLcmUI's Yes silently
  restores the backup; Headless instead takes the `else` branch
  (`UnlockProject(); throw LcmInitializationException`). A caller relying on the
  silent auto-restore now gets an exception.
- **Acceptable:** yes -- unattended auto-restore of an unknown-age backup is
  itself a data-loss risk (the same polarity problem `ConflictingSave` was
  flagged for), and FwLcmUI's modal dialog would hang in a headless process
  anyway (no message pump). Raising and letting the caller or a human decide is
  the correct default.

### `RestoreLinkedFilesInProjectFolder`, `ChooseFilesToUse`, `CannotRestoreLinkedFilesToOriginalLocation`

- **FwLcmUI:** modal dialogs (`FilesToRestoreAreOlder`,
  `RestoreLinkedFilesToProjectsFolder`,
  `CantRestoreLinkedFilesToOriginalLocation`).
- **HeadlessLcmUI:** non-destructive defaults, logged.
- **Delta:** all three are called *only* from `ProjectRestoreService`
  (`DomainServices/BackupRestore/ProjectRestoreService.cs:337/396/427`), a
  standalone class instantiated explicitly by a "Restore Project from Backup"
  caller. `LcmCache.CreateCacheFromExistingData` -- flexicon's only call site
  (`FLExLCM.py`) -- never constructs `ProjectRestoreService`.
- **Acceptable:** unreachable from flexicon's call path; **dead code** for this
  library, confirmed by grepping every caller of the `ProjectRestoreService`
  constructor.

## Verdict

Going member by member against the live liblcm source and the WinForms
implementation being replaced, only one non-`ConflictingSave` member has a
realistic, checkable behaviour delta for a default caller: `OfferToRestore`,
reachable whenever `CreateCacheFromExistingData` opens a corrupt `.fwdata` with
a stale sibling `.bak` -- a scenario the current flexicon default (`FwLcmUI`)
would resolve via a silent-to-the-script, human-mediated auto-restore, and the
proposed default (`HeadlessLcmUI`) resolves by raising
`LcmInitializationException`. That is a genuine change, but it is the same
"don't let an unattended process discard or overwrite data based on a stale
backup" principle that already justified the `ConflictingSave` flip, and it also
sidesteps a guaranteed dialog hang in a process with no message pump -- so it is
the correct default, not a regression.

`Retry` and the three `ProjectRestoreService`-only members
(`RestoreLinkedFilesInProjectFolder`, `ChooseFilesToUse`,
`CannotRestoreLinkedFilesToOriginalLocation`) are confirmed unreachable from
flexicon's only call site. `SynchronizeInvoke` returning `None` is dereferenced
unguarded at exactly two liblcm sites, but both are empty/no-op for any flexicon
session that registers no `IVwNotifyChange` subscriber and does not touch
`Scripture` -- true of the entire current API surface, so safe today but worth a
regression note if a future feature adds a change-watcher. `ReportException`'s
return value is proven dead in all three liblcm call sites, so the
non-interactive branch changes nothing about retry/abandon logic.

**Conclusion:** there is no realistic flexicon caller whose *correct* behaviour
depends on the current `FwLcmUI` default. The one caller who would notice
anything (a corrupt-project-plus-stale-backup scenario) gets a safer, explicit
failure instead of a silent or hung one.

## Follow-ups for the implementer

1. `OfferToRestore` is a real, documentable behaviour change on the
   corrupt-`.fwdata`-plus-`.bak` path. It belongs in the CHANGELOG entry
   alongside `ConflictingSave`, not left implicit.
2. The `SynchronizeInvoke is None` safety argument is contingent on no
   `IVwNotifyChange` subscriber and no `Scripture` access. Worth an in-tree
   comment in `headless_ui.py` so a future change-watcher feature does not
   silently invalidate it.
