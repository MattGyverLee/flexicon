# Target audit -- issue #542, cycle 1 leftover check (read-only)

**Date:** 2026-09-26
**Purpose:** Verify the cycle-1 live test
`tests/operations/test_issue542_affix_slot_readers_live.py` (commit
`ac736e0`) left the 'Target' project clean, per its `finally:` blocks.
**Mode:** READ-ONLY. Target was opened with `writeEnabled=False`. No
restore script was run. No write access was attempted at any point.

## 1. Objects the cycle-1 test creates (read from `ac736e0`)

Test file: `tests/operations/test_issue542_affix_slot_readers_live.py`
`TEST_PREFIX = "TEST_542_"`

| Test | Objects created | Cleanup in `finally:` |
|---|---|---|
| `test_slot_readers_round_trip_via_object_and_hvo` | POS `TEST_542_pos` (abbr `T542`); affix slots `TEST_542_slot_req` (renamed to `TEST_542_slot_req_renamed` mid-test) and `TEST_542_slot_opt`, both owned by that POS; LexEntry `TEST_542_prefix` (morph type "prefix") with its auto-created sense; an inflectional-affix MSA on that sense filling `slot_required` | `project.LexEntry.Delete(entry)` then `project.POS.Delete(pos)` -- deletes the entry (and its sense/MSA) and the owning POS (and, by LCM ownership, its owned `AffixSlotsOC` entries) |
| `test_get_affix_slots_returns_affixslot_wrapper` | POS `TEST_542_wrap_pos` (abbr `T542W`); affix slot `TEST_542_wrap_slot` on it; affix template `TEST_542_wrap_template` on the same POS, with the slot added as a prefix slot | `project.POS.Delete(pos)` -- expected to cascade-delete the owned slot and template |
| `test_bad_slot_input_raises_parameter_error` | POS `TEST_542_bad_pos` (abbr `T542B`) | `project.POS.Delete(pos)` |
| `test_sena3_affix_slots_are_readable_if_present` | Nothing -- opens Sena 3 read-only, creates no objects | `project.CloseProject()` only |

All created-object names use the `TEST_542_` prefix. All three
write-path tests delete only the top-level POS (and, in test 1, the
LexEntry) in their `finally:` blocks; slots/templates are owned children
of the POS and are expected to cascade-delete with it in LCM's owning
sequence/collection semantics.

## 2. Audit script (read-only, run from the worktree)

Run as:
```
cd C:\Github\flexicon-542
PYTHONPATH=C:\Github\flexicon-542 python <scratchpad>/audit_target_542.py
```

Opens `Target` with `writeEnabled=False`, asserts that, walks the full
POS hierarchy (via `project.POS.GetAll()`, which already recurses, plus
an explicit `SubPossibilitiesOS` walk for the `AffixSlotsOC` /
`AffixTemplatesOS` checks), and checks every `LexEntry` headword. Closes
the project at the end. Never opens with `writeEnabled=True`; never
calls a restore script.

```python
#
#   audit_target_542.py
#
#   READ-ONLY audit of the 'Target' FLEx project for leftover TEST_542_
#   objects potentially left behind by
#   tests/operations/test_issue542_affix_slot_readers_live.py (cycle 1,
#   commit ac736e0). Opens Target with writeEnabled=False. Does not write,
#   does not restore, does not retry with write access.
#
#   Run from C:\Github\flexicon-542 so it imports the worktree code:
#       python <this file>
#

import os
import sys
import traceback

TEST_PREFIX = "TEST_542_"


def _init_flex():
    """Mirror the session-setup FLEx init sequence used by tests/flex_plugin.py."""
    import clr
    from Microsoft.Win32 import Registry

    RegKey = r"SOFTWARE\SIL\FieldWorks\9"
    try:
        rKey = Registry.LocalMachine.OpenSubKey(RegKey)
        if rKey is None:
            rKey = Registry.CurrentUser.OpenSubKey(RegKey)
        if rKey:
            fw_code_dir = rKey.GetValue("RootCodeDir")
            if fw_code_dir and os.path.exists(os.path.join(fw_code_dir, "FieldWorks.exe")):
                sys.path.append(fw_code_dir)
                print(f"[OK] FieldWorks path added: {fw_code_dir}")
    except Exception as e:
        print(f"[WARN] Could not read registry: {e}")

    clr.AddReference("FwUtils")
    clr.AddReference("SIL.WritingSystems")
    clr.AddReference("SIL.LCModel")

    from SIL.FieldWorks.Common.FwUtils import FwRegistryHelper, FwUtils

    FwRegistryHelper.Initialize()
    FwUtils.InitializeIcu()

    from flexicon.code.FLExInit import FLExInitialize
    FLExInitialize()
    print("[OK] FLExInitialize() complete")


def main():
    _init_flex()

    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    try:
        project.OpenProject("Target", writeEnabled=False)
    except Exception as exc:
        print("BLOCKED: could not open Target read-only: %r" % (exc,))
        traceback.print_exc()
        return 2

    try:
        assert project.writeEnabled is False, "expected read-only open"
        print("Opened Target read-only. writeEnabled=%r" % (project.writeEnabled,))

        # --- 1. POS hierarchy: any TEST_ names ---
        pos_hits = []
        def walk_pos(pos_list, path=""):
            for p in pos_list:
                try:
                    name = project.POS.GetName(p)
                except Exception:
                    name = getattr(p, "Name", None)
                    try:
                        name = str(name)
                    except Exception:
                        name = "<unreadable>"
                full_path = f"{path}/{name}" if path else name
                if name and TEST_PREFIX in str(name):
                    pos_hits.append((full_path, int(p.Hvo)))
                # recurse into subcategories
                try:
                    sub = list(p.SubPossibilitiesOS)
                except Exception:
                    sub = []
                if sub:
                    walk_pos(sub, full_path)

        try:
            all_pos = project.POS.GetAll()
        except Exception as exc:
            print("ERROR calling project.POS.GetAll(): %r" % (exc,))
            all_pos = []
        walk_pos(list(all_pos))

        print("\n--- POS hits (name contains %r) ---" % TEST_PREFIX)
        print("count=%d" % len(pos_hits))
        for full_path, hvo in pos_hits:
            print(f"  POS: {full_path!r} hvo={hvo}")

        # --- 2. AffixSlotsOC entries anywhere under any POS with TEST_ name ---
        slot_hits = []
        def walk_pos_for_slots(pos_list, path=""):
            for p in pos_list:
                try:
                    name = project.POS.GetName(p)
                except Exception:
                    name = "<unreadable>"
                full_path = f"{path}/{name}" if path else name
                try:
                    slots = list(p.AffixSlotsOC)
                except Exception:
                    slots = []
                for s in slots:
                    try:
                        sname = project.POS.GetSlotName(s)
                    except Exception:
                        sname = "<unreadable>"
                    if sname and TEST_PREFIX in str(sname):
                        slot_hits.append((full_path, sname, int(s.Hvo)))
                try:
                    sub = list(p.SubPossibilitiesOS)
                except Exception:
                    sub = []
                if sub:
                    walk_pos_for_slots(sub, full_path)

        walk_pos_for_slots(list(all_pos))
        print("\n--- AffixSlotsOC hits (name contains %r) ---" % TEST_PREFIX)
        print("count=%d" % len(slot_hits))
        for owner_path, sname, hvo in slot_hits:
            print(f"  Slot: {sname!r} on POS {owner_path!r} hvo={hvo}")

        # --- 3. AffixTemplatesOS entries anywhere under any POS with TEST_ name ---
        template_hits = []
        def walk_pos_for_templates(pos_list, path=""):
            for p in pos_list:
                try:
                    name = project.POS.GetName(p)
                except Exception:
                    name = "<unreadable>"
                full_path = f"{path}/{name}" if path else name
                try:
                    templates = list(p.AffixTemplatesOS)
                except Exception:
                    templates = []
                for t in templates:
                    tname = None
                    try:
                        from SIL.LCModel.Core.KernelInterfaces import ITsString
                        tname = ITsString(t.Name.get_String(project.project.DefaultAnalWs)).Text
                    except Exception:
                        try:
                            tname = str(t.Name)
                        except Exception:
                            tname = "<unreadable>"
                    if tname and TEST_PREFIX in str(tname):
                        template_hits.append((full_path, tname, int(t.Hvo)))
                try:
                    sub = list(p.SubPossibilitiesOS)
                except Exception:
                    sub = []
                if sub:
                    walk_pos_for_templates(sub, full_path)

        walk_pos_for_templates(list(all_pos))
        print("\n--- AffixTemplatesOS hits (name contains %r) ---" % TEST_PREFIX)
        print("count=%d" % len(template_hits))
        for owner_path, tname, hvo in template_hits:
            print(f"  Template: {tname!r} on POS {owner_path!r} hvo={hvo}")

        # --- 4. Lexical entries whose headword starts with TEST_542_ ---
        entry_hits = []
        try:
            all_entries = project.LexEntry.GetAll()
        except Exception as exc:
            print("ERROR calling project.LexEntry.GetAll(): %r" % (exc,))
            all_entries = []
        for e in all_entries:
            try:
                headword = project.LexEntry.GetHeadword(e)
            except Exception:
                headword = None
            hw_str = str(headword) if headword is not None else ""
            if TEST_PREFIX in hw_str:
                entry_hits.append((hw_str, int(e.Hvo)))

        print("\n--- LexEntry hits (headword contains %r) ---" % TEST_PREFIX)
        print("count=%d" % len(entry_hits))
        for hw, hvo in entry_hits:
            print(f"  Entry: {hw!r} hvo={hvo}")

        total = len(pos_hits) + len(slot_hits) + len(template_hits) + len(entry_hits)
        print("\n=== TOTAL LEFTOVER HITS: %d ===" % total)
        return 0
    finally:
        try:
            project.CloseProject()
            print("\nProject closed.")
        except Exception as exc:
            print("WARNING: error closing project: %r" % (exc,))

if __name__ == "__main__":
    sys.exit(main())
```

## 3. Raw output

```
[OK] FieldWorks path added: C:\Program Files\SIL\FieldWorks 9[OK] FLExInitialize() complete
Opened Target read-only. writeEnabled=False

--- POS hits (name contains 'TEST_542_') ---
count=0

--- AffixSlotsOC hits (name contains 'TEST_542_') ---
count=0

--- AffixTemplatesOS hits (name contains 'TEST_542_') ---
count=0

--- LexEntry hits (headword contains 'TEST_542_') ---
count=0

=== TOTAL LEFTOVER HITS: 0 ===

Project closed.
```

Target was not locked; it opened cleanly read-only, so no blocker was hit.

## 4. Verdict

**CLEAN.** No POS, affix slot, affix template, or lexical entry with a
`TEST_542_` name/headword was found anywhere in the Target project's POS
hierarchy or lexicon. The cycle-1 test's `finally:` blocks (delete
LexEntry, then delete the owning POS) did remove everything they claim to,
including the owned `AffixSlotsOC` / `AffixTemplatesOS` children, which
were not separately deleted but are gone regardless -- consistent with
LCM ownership cascading the delete. No cleanup action was taken by this
audit (none was needed).
