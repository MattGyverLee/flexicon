"""Live check for the peer schema guard (capability "peer-schema-guard").

Run with FieldWorks holding Sena 3 open in shared mode, so this process
attaches as a non-master peer. With the guard on:
  1. Ensure("en", ..., is_vernacular=False) -- en is an active analysis WS --
     returns (ws, False) and writes nothing;
  2. Ensure("qaa-x-zzexcl", ...) raises FP_ExclusiveAccessRequiredError and
     writes nothing.
Then re-reads the WS lists from a FRESH open to show nothing changed.

Sena 3 only (the designated test project). Plain ASCII output.
Usage: PYTHONPATH=<this worktree> python evidence/peer_schema_guard_live.py
"""
import os
import sys

PROJECT = "Sena 3"
PROBE_TAG = "qaa-x-zzexcl"


def _open(write_enabled):
    from flexicon import FLExInitialize, FLExProject

    FLExInitialize()
    p = FLExProject()
    p.OpenProject(PROJECT, writeEnabled=write_enabled)
    return p


def _lists(p):
    ws = p.WritingSystems
    vern = [str(ws.GetLanguageTag(w)) for w in ws.GetVernacular()]
    anal = [str(ws.GetLanguageTag(w)) for w in ws.GetAnalysis()]
    in_store = ws.ExistsInStore(PROBE_TAG)
    return vern, anal, in_store


def main():
    import flexicon
    from flexicon import FP_ExclusiveAccessRequiredError

    assert PROJECT == "Sena 3"
    print(f"[ENV ] flexicon={flexicon.__file__}")
    print(f"[ENV ] FLEXLIBS_REQUIRE_LIVE={os.environ.get('FLEXLIBS_REQUIRE_LIVE')}")
    print(f"[ENV ] peer-schema-guard in CAPABILITIES = {'peer-schema-guard' in flexicon.CAPABILITIES}")

    p = _open(True)
    print(f"[PRE ] vern/anal/probe-in-store = {_lists(p)}")
    p.SetPeerSchemaGuard(True)
    print(f"[GUARD] PeerSchemaGuard = {p.PeerSchemaGuard}")

    ws, created = p.WritingSystems.Ensure("en", "English", is_vernacular=False)
    print(f"[NOOP] Ensure('en', analysis) -> created={created}, tag={ws.Id}")

    try:
        p.WritingSystems.Ensure(PROBE_TAG, "zz exclusive probe")
        print("[FAIL] Ensure of an absent tag did NOT raise")
        refused = False
    except FP_ExclusiveAccessRequiredError as exc:
        print(f"[REFUSE] {type(exc).__name__}: {exc}")
        refused = True
    print(f"[POST] in-session vern/anal/probe-in-store = {_lists(p)}")
    p.CloseProject()

    q = _open(False)
    print(f"[READ] fresh-open vern/anal/probe-in-store = {_lists(q)}")
    q.CloseProject()
    print("PASS" if refused and not created else "FAIL")
    return 0 if refused and not created else 1


if __name__ == "__main__":
    sys.exit(main())
