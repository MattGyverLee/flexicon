#!/usr/bin/env python
#
# research_phase2_lcm_api.py
#
# Research script to verify Phase 2 LCM APIs exist and are functional
#
# Usage:
#   python research_phase2_lcm_api.py
#
# Prerequisites:
#   - FieldWorks installed and a test project available
#   - flexicon installed or in development mode
#

import sys
import os

# Ensure flexicon is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def research_lcm_apis():
    """
    Research script to discover which LCM undo/redo APIs are available.
    """
    print("[PHASE 2 RESEARCH] LCM Undo/Redo API Discovery")
    print("=" * 60)

    try:
        from flexicon import FLExProject, FLExInitialize
    except ImportError as e:
        print(f"[ERROR] Cannot import flexicon: {e}")
        return False

    try:
        FLExInitialize()
    except Exception as e:
        print(f"[WARN] FLExInitialize failed: {e}")
        print("[NOTE] Continuing anyway - may work in limited form")

    # Open a test project
    project = FLExProject()
    try:
        print("\n[STEP 1] Opening test project...")
        # Try to open any available project
        try:
            from flexicon import AllProjectNames

            projects = AllProjectNames()
            if not projects:
                print("[ERROR] No FieldWorks projects found")
                print("[INFO] Please create a test project in FieldWorks first")
                return False

            test_project = projects[0]
            print(f"[OK] Found projects: {projects}")
            print(f"[INFO] Using project: {test_project}")

            project.OpenProject(test_project, writeEnabled=True)
            print("[OK] Project opened in write mode")
        except Exception as e:
            print(f"[ERROR] Cannot open project: {e}")
            return False

        # ====== QUESTION 1: BeginUndoTask ======
        print("\n" + "=" * 60)
        print("[QUESTION 1] Does BeginUndoTask exist?")
        print("-" * 60)

        project_raw = project.project
        has_begin_undo_task_project = hasattr(project_raw, "BeginUndoTask")
        has_begin_undo_task_mca = hasattr(project_raw.MainCacheAccessor, "BeginUndoTask")

        print(f"project.project.BeginUndoTask: {has_begin_undo_task_project}")
        print(f"project.MainCacheAccessor.BeginUndoTask: {has_begin_undo_task_mca}")

        if has_begin_undo_task_project:
            print("[RESULT] ✅ Found on project.project")
        elif has_begin_undo_task_mca:
            print("[RESULT] ✅ Found on MainCacheAccessor")
        else:
            print("[RESULT] ❌ NOT FOUND")

        # ====== QUESTION 2: UndoStack.Mark ======
        print("\n" + "=" * 60)
        print("[QUESTION 2] Does UndoStack.Mark exist?")
        print("-" * 60)

        has_undo_stack = hasattr(project_raw, "UndoStack")
        print(f"project.project.UndoStack exists: {has_undo_stack}")

        if has_undo_stack:
            undo_stack = project_raw.UndoStack
            has_mark = hasattr(undo_stack, "Mark")
            has_rollback = hasattr(undo_stack, "RollbackToMark")
            print(f"UndoStack.Mark: {has_mark}")
            print(f"UndoStack.RollbackToMark: {has_rollback}")

            if has_mark and has_rollback:
                print("[RESULT] ✅ Found both Mark and RollbackToMark")
            else:
                print("[RESULT] ⚠️  Partial (missing one or both methods)")
        else:
            print("[RESULT] ❌ UndoStack not found")

        # ====== QUESTION 3: All undo-related methods ======
        print("\n" + "=" * 60)
        print("[QUESTION 3] All undo/redo/task methods on project object")
        print("-" * 60)

        undo_methods = [
            m
            for m in dir(project_raw)
            if any(x in m.lower() for x in ["undo", "redo", "mark", "task"]) and not m.startswith("_")
        ]

        if undo_methods:
            print(f"Found {len(undo_methods)} methods:")
            for m in sorted(undo_methods):
                print(f"  - {m}")
        else:
            print("No undo/redo/mark/task methods found")

        # ====== QUESTION 4: MainCacheAccessor methods ======
        print("\n" + "=" * 60)
        print("[QUESTION 4] All undo-related methods on MainCacheAccessor")
        print("-" * 60)

        mca = project_raw.MainCacheAccessor
        mca_methods = [
            m
            for m in dir(mca)
            if any(x in m.lower() for x in ["undo", "redo", "mark", "task"]) and not m.startswith("_")
        ]

        if mca_methods:
            print(f"Found {len(mca_methods)} methods:")
            for m in sorted(mca_methods):
                print(f"  - {m}")
        else:
            print("No undo/redo/mark/task methods found")

        # ====== QUESTION 5: Try BeginUndoTask (if exists) ======
        print("\n" + "=" * 60)
        print("[QUESTION 5] Can BeginUndoTask work?")
        print("-" * 60)

        if has_begin_undo_task_project or has_begin_undo_task_mca:
            try:
                # Get the method
                if has_begin_undo_task_project:
                    begin_fn = project_raw.BeginUndoTask
                else:
                    begin_fn = project_raw.MainCacheAccessor.BeginUndoTask

                print(f"[INFO] BeginUndoTask found: {begin_fn}")

                # Try calling it
                print("[INFO] Attempting to call BeginUndoTask('test')...")
                begin_fn("test operation")
                print("[OK] BeginUndoTask called successfully")

                # Try to end it
                if has_begin_undo_task_project and hasattr(project_raw, "EndUndoTask"):
                    project_raw.EndUndoTask()
                    print("[OK] EndUndoTask called successfully")
                elif has_begin_undo_task_mca and hasattr(mca, "EndUndoTask"):
                    mca.EndUndoTask()
                    print("[OK] EndUndoTask called successfully")
                else:
                    print("[WARN] EndUndoTask not found")

                print("[RESULT] ✅ BeginUndoTask appears to work")
            except Exception as e:
                print(f"[ERROR] BeginUndoTask failed: {e}")
                print("[RESULT] ❌ BeginUndoTask doesn't work")
        else:
            print("[SKIP] BeginUndoTask not found, skipping")

        # ====== SUMMARY ======
        print("\n" + "=" * 60)
        print("[SUMMARY]")
        print("-" * 60)

        summary = {
            "BeginUndoTask exists": has_begin_undo_task_project or has_begin_undo_task_mca,
            "UndoStack.Mark exists": has_undo_stack,
        }

        for key, value in summary.items():
            status = "✅" if value else "❌"
            print(f"{status} {key}")

        print("\n[NEXT STEP] Review results above to determine Phase 2 feasibility")
        return True

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        try:
            project.CloseProject()
            print("\n[OK] Project closed")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        success = research_lcm_apis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[CANCELLED] User interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
