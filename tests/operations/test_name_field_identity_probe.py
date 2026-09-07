#
#   test_name_field_identity_probe.py
#
#   READ-ONLY-TO-PRODUCTION live probe for
#   specs/name-field-whitespace-identity/ (cycle 1).
#
#   Measures (does NOT fix) whether the dedup paths for names in FLEx --
#   Texts.Exists/Create, Anthropology.Find/Exists/Create, and
#   Checks.FindCheckType/CreateCheckType -- strip the search NEEDLE while
#   leaving the stored HAYSTACK unstripped, and whether a non-str payload
#   can silently produce an empty persisted name (Q-242B).
#
#   TECHNIQUE: layer-B raw-MakeString bypass (same technique proven by
#   tests/operations/test_issue242_whitespace_probe.py's test_p3) -- write a
#   name DIRECTLY via TsStringUtils.MakeString to simulate the POST-FIX
#   stored state (a name-field writer that no longer strips before
#   persisting), without touching any file under flexicon/.
#
#   This is a NEW, self-contained probe file -- it does not import from or
#   extend test_issue242_whitespace_probe.py (different feature, different
#   fixtures, per the cycle-1 task brief).
#
#   PREDICTIONS were committed to
#   specs/name-field-whitespace-identity/evidence/live-probe-cycle1.md
#   BEFORE this file was written and BEFORE any live run, per the C28
#   forward rule.
#
#   Uses target_sandbox / target_sandbox_path (tests/conftest.py)
#   EXCLUSIVELY. Never the real Target project, never scripts/restore_*.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_NF_"


def _safe(fn, label):
    """Run fn(), print+return (result, None) or print+return (None, 'Type: msg')."""
    try:
        result = fn()
        print(f"[PROBE] {label}: OK -> {result!r}")
        return result, None
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        print(f"[PROBE] {label}: RAISED {msg}")
        return None, msg


def _seed_valid_check_list(project):
    """
    UNPLANNED DISCOVERY, worked around here for PN4/PN5/PN6 ONLY (see the
    per-test docstrings and the evidence file's RESULTS section for the
    full writeup): CheckOperations._GetCheckList()
    (CheckOperations.py:1168-1179) is a HARDCODED stub that unconditionally
    `return None`s, regardless of project state. This forces
    _GetOrCreateCheckList() (:1181-1205) down its "create a new list"
    branch on EVERY call, which itself calls
    `self.project.project.ServiceLocator.GetInstance(...)` at :1198 --
    but `ILcmServiceLocator` has no `GetInstance` method (grep confirms
    every OTHER call site in this same file, and in every other Operations
    class in this codebase, uses `.GetService(...)`). The result:
    CreateCheckType() raises AttributeError on EVERY call, for EVERY
    payload, str or not -- this appears to have NEVER worked against a
    live LCM. This is orthogonal to the name-field whitespace/identity
    question this probe exists to answer, but it blocks reaching
    FindCheckType/CreateCheckType's own name-handling logic (the actual
    code under study for PN4/PN5/PN6) through the public API at all.

    Workaround (TEST-INSTANCE ONLY, zero lines under flexicon/ touched,
    confirmed by `git diff --stat -- flexicon/` at the end of this run):
    pre-seed a real, valid ICmPossibilityList (built with the CORRECT
    `.GetService(...)` call) and monkeypatch this ONE function-scoped
    `target_sandbox` instance's `Checks._GetCheckList` to return it. This
    makes `_GetOrCreateCheckList`'s `if check_list: return check_list`
    branch (:1189-1190) fire, so the broken `GetInstance` line is never
    reached -- CreateCheckType then proceeds to its OWN name-handling
    logic (:192-229), which is what PN4/PN5/PN6 actually measure. Nothing
    under flexicon/ is modified; this is a plain Python attribute
    assignment on one test's fixture instance, gone at teardown.
    """
    from SIL.LCModel import ICmPossibilityListFactory

    factory = project.project.ServiceLocator.GetService(ICmPossibilityListFactory)
    with project.Transaction("PN4/5/6 seed valid check list (test-only workaround)"):
        check_list = factory.Create()
    project.Checks._GetCheckList = lambda: check_list
    return check_list


class _NonStrPayload:
    """A plain object with no .strip() method and no meaningful __str__,
    used for the non-str-branch probes (PN5, PN7). Deliberately distinct
    from #242's _NonStrPayload (which had a whitespace-bearing __str__) --
    this probe needs a payload that has NO string-like behaviour at all,
    to isolate the isinstance(name, str) branch cleanly."""

    def __str__(self):
        return "<non-str-payload>"


# ===========================================================================
# PN1 -- CONTROL: needle IS stripped, haystack IS stripped (both via the
# public Create() path), so a padded needle still finds the unpadded name.
# ===========================================================================

@pytest.mark.live_phase("TextOperations", "read")
def test_pn1_control_padded_needle_finds_unpadded_public_api_name(target_sandbox):
    """
    PN1 (control): Texts.Create("TEST_NF_Gen") persists the STRIPPED name
    (Create's own `.strip()` at TextOperations.py:152 applies to the
    persisted copy too, not just the validation copy). Exists() then strips
    its OWN needle argument at :458 before matching. So a padded needle
    ("TEST_NF_Gen ") is predicted to still find the unpadded stored name.
    """
    project = target_sandbox
    name = f"{TEST_PREFIX}Gen"

    text, create_exc = _safe(lambda: project.Texts.Create(name), "PN1 Create")
    assert create_exc is None, f"Create raised unexpectedly: {create_exc}"

    stored_name = project.Texts.GetName(text) if hasattr(project.Texts, "GetName") else None
    print(f"[TABLE][PN1] stored name (best-effort read): {stored_name!r}")

    padded_needle = name + " "
    found, exists_exc = _safe(lambda: project.Texts.Exists(padded_needle), "PN1 Exists(padded)")
    assert exists_exc is None, f"Exists raised unexpectedly: {exists_exc}"

    print(f"[VERDICT][PN1] Exists({padded_needle!r}) -> {found!r} (PREDICTED True)")
    assert found is True, (
        f"PN1 MISS: expected Exists({padded_needle!r}) to be True (needle "
        f"stripped by Exists(), haystack persisted stripped by Create()) -- "
        f"got {found!r}"
    )


# ===========================================================================
# PN2 -- CORE: layer-B bypass write for Texts; needle-only strip proof.
# ===========================================================================

@pytest.mark.live_phase("TextOperations", "modify")
def test_pn2_core_texts_haystack_never_stripped(target_sandbox):
    """
    PN2 (CORE), FLIPPED to assert T2's FIXED behaviour (tasks.md T2,
    spec.md C4): create a text, then set its Name DIRECTLY via
    TsStringUtils.MakeString to "TEST_NF_Raw " (layer B, bypassing
    Texts.SetName/Create -- simulates a name persisted with its original
    whitespace, which is now the REAL behaviour of Create/SetName post-fix,
    not just a simulation of it). Then:
      - Exists("TEST_NF_Raw")  -> PREDICTED True
      - Exists("TEST_NF_Raw ") -> PREDICTED True
    Both predicted True because Exists() now strips BOTH the needle and the
    haystack inline before comparing (TextOperations.py:461/:464), so a
    padded stored name is found by either a padded or unpadded needle.

    PRE-FIX BEHAVIOUR (historical record, cycle 1, `spec.md` C1): before
    T2's comparison-symmetry fix, Exists() stripped only the needle
    parameter (old `:458`) and built the haystack key straight from the
    raw `text.Name` with no stripping at all -- so BOTH
    Exists("TEST_NF_Raw") and Exists("TEST_NF_Raw ") returned False against
    this same padded haystack. That was the measured, binding result this
    test originally locked down (see `evidence/live-probe-cycle1.md`); this
    flip is the intended, authorised consequence of C3/C4 landing, not a
    silent behaviour change discovered by accident.
    """
    from SIL.LCModel.Core.Text import TsStringUtils

    project = target_sandbox
    raw_name = f"{TEST_PREFIX}Raw "  # trailing space, byte-for-byte

    text, create_exc = _safe(
        lambda: project.Texts.Create(f"{TEST_PREFIX}Raw_placeholder"), "PN2 seed Create"
    )
    assert create_exc is None, f"Seed Create raised: {create_exc}"

    wsHandle = project.project.DefaultAnalWs

    def _bypass_write():
        with project.Transaction("PN2 bypass write raw name"):
            ts = TsStringUtils.MakeString(raw_name, wsHandle)
            text.Name.set_String(wsHandle, ts)

    _, bypass_exc = _safe(_bypass_write, "PN2 bypass write")
    assert bypass_exc is None, f"Bypass write raised: {bypass_exc}"

    # Confirm the raw haystack really is stored with the trailing space,
    # read directly (not through this library's Exists/Find machinery).
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    raw_reread = ITsString(text.Name.BestAnalysisAlternative).Text
    print(f"[TABLE][PN2] raw stored Name (direct read): {raw_reread!r}")
    assert raw_reread == raw_name, (
        f"Precondition failed: expected the bypass write to store "
        f"{raw_name!r} verbatim -- got {raw_reread!r}"
    )

    unpadded_needle = f"{TEST_PREFIX}Raw"
    padded_needle = f"{TEST_PREFIX}Raw "

    found_unpadded, exc1 = _safe(lambda: project.Texts.Exists(unpadded_needle), "PN2 Exists(unpadded)")
    found_padded, exc2 = _safe(lambda: project.Texts.Exists(padded_needle), "PN2 Exists(padded)")
    assert exc1 is None and exc2 is None, f"Exists raised unexpectedly: {exc1} / {exc2}"

    print(
        f"[VERDICT][PN2] Exists({unpadded_needle!r}) -> {found_unpadded!r} "
        f"(PREDICTED True, post-fix); Exists({padded_needle!r}) -> "
        f"{found_padded!r} (PREDICTED True, post-fix)"
    )

    if found_unpadded is not True or found_padded is not True:
        print(
            "[REFUTATION][PN2] MEASURED OPPOSITE TO PREDICTION -- the needle "
            "did NOT find the padded haystack even after T2's comparison-"
            "symmetry fix. This REFUTES the fix's premise (both sides "
            "stripped inline). Reported plainly, NOT reconciled."
        )
    assert found_unpadded is True, (
        f"PN2 MISS (unpadded needle, post-fix): expected True, got {found_unpadded!r}"
    )
    assert found_padded is True, (
        f"PN2 MISS (padded needle, post-fix): expected True, got {found_padded!r}"
    )


# ===========================================================================
# PN3 -- same layer-B shape for Anthropology.Find/Exists.
# ===========================================================================

@pytest.mark.live_phase("AnthropologyOperations", "modify")
def test_pn3_anthropology_haystack_never_stripped(target_sandbox):
    """
    PN3, FLIPPED to assert T3's FIXED behaviour (tasks.md T3, spec.md C4):
    layer-B store an item named "TEST_NF_Anthro_Raw " (trailing space --
    this now matches what the REAL, fixed Create()/CreateSubitem()
    themselves persist, not merely a simulation of a future state). Then:
      - Find(unpadded)   -> PREDICTED the item (not None)
      - Find(padded)     -> PREDICTED the item (not None)
      - Exists(unpadded) -> PREDICTED True
      - Exists(padded)   -> PREDICTED True
    All four predicted to find the item because Find() now strips BOTH the
    needle and the haystack inline before comparing
    (AnthropologyOperations.py:562/:565), so a padded stored name is found
    by either a padded or unpadded needle. `casefold=False` unchanged.

    PRE-FIX BEHAVIOUR (historical record, cycle 1, `spec.md` C1): before
    T3's comparison-symmetry fix, Find() stripped only the needle
    parameter (old `:558`) and built the haystack key straight from the
    raw `item.Name` with no stripping at all -- so Find(unpadded) and
    Find(padded) BOTH returned None, and Exists(unpadded)/Exists(padded)
    BOTH returned False, against this same padded haystack. That was the
    measured, binding result this test originally locked down (see
    `evidence/live-probe-cycle1.md`); this flip is the intended, authorised
    consequence of C3/C4 landing, not a silent behaviour change discovered
    by accident.
    """
    from SIL.LCModel.Core.Text import TsStringUtils

    project = target_sandbox
    raw_name = f"{TEST_PREFIX}Anthro_Raw "  # trailing space

    item, create_exc = _safe(
        lambda: project.Anthropology.Create(f"{TEST_PREFIX}Anthro_placeholder"),
        "PN3 seed Create",
    )
    assert create_exc is None, f"Seed Create raised: {create_exc}"

    wsHandle = project.project.DefaultAnalWs

    def _bypass_write():
        with project.Transaction("PN3 bypass write raw name"):
            ts = TsStringUtils.MakeString(raw_name, wsHandle)
            item.Name.set_String(wsHandle, ts)

    _, bypass_exc = _safe(_bypass_write, "PN3 bypass write")
    assert bypass_exc is None, f"Bypass write raised: {bypass_exc}"

    from SIL.LCModel.Core.KernelInterfaces import ITsString

    raw_reread = ITsString(item.Name.get_String(wsHandle)).Text
    print(f"[TABLE][PN3] raw stored Name (direct read): {raw_reread!r}")
    assert raw_reread == raw_name, (
        f"Precondition failed: expected the bypass write to store "
        f"{raw_name!r} verbatim -- got {raw_reread!r}"
    )

    unpadded_needle = f"{TEST_PREFIX}Anthro_Raw"
    padded_needle = f"{TEST_PREFIX}Anthro_Raw "

    find_unpadded, fexc1 = _safe(lambda: project.Anthropology.Find(unpadded_needle), "PN3 Find(unpadded)")
    find_padded, fexc2 = _safe(lambda: project.Anthropology.Find(padded_needle), "PN3 Find(padded)")
    exists_unpadded, eexc1 = _safe(lambda: project.Anthropology.Exists(unpadded_needle), "PN3 Exists(unpadded)")
    exists_padded, eexc2 = _safe(lambda: project.Anthropology.Exists(padded_needle), "PN3 Exists(padded)")
    assert all(e is None for e in (fexc1, fexc2, eexc1, eexc2)), (
        f"Unexpected exception(s): {fexc1} / {fexc2} / {eexc1} / {eexc2}"
    )

    print(
        f"[VERDICT][PN3] Find(unpadded) -> {find_unpadded!r} (PREDICTED the "
        f"item, post-fix); Find(padded) -> {find_padded!r} (PREDICTED the "
        f"item, post-fix); Exists(unpadded) -> {exists_unpadded!r} "
        f"(PREDICTED True, post-fix); Exists(padded) -> {exists_padded!r} "
        f"(PREDICTED True, post-fix)"
    )

    if find_unpadded is None or find_padded is None:
        print(
            "[REFUTATION][PN3] MEASURED OPPOSITE TO PREDICTION -- the "
            "needle did NOT find the padded haystack even after T3's "
            "comparison-symmetry fix. This REFUTES the fix's premise (both "
            "sides stripped inline). Reported plainly, NOT reconciled."
        )
    assert find_unpadded is not None, f"PN3 MISS: Find(unpadded) expected the item, got None"
    assert find_padded is not None, f"PN3 MISS: Find(padded) expected the item, got None"
    assert exists_unpadded is True, f"PN3 MISS: Exists(unpadded) expected True, got {exists_unpadded!r}"
    assert exists_padded is True, f"PN3 MISS: Exists(padded) expected True, got {exists_padded!r}"


# ===========================================================================
# PN4 -- same layer-B shape for Checks.FindCheckType.
# ===========================================================================

@pytest.mark.live_phase("CheckOperations", "modify")
def test_pn4_checks_haystack_never_stripped(target_sandbox):
    """
    PN4 (binding under the refutation clause): same layer-B shape as PN2/
    PN3, applied to Checks.FindCheckType. Needle-strip at
    CheckOperations.py:341; haystack key built raw at :350 (via
    check_type.Name.get_String(wsHandle), no .strip() in that line or in
    normalize_match_key). Predicted None for both the unpadded and padded
    needle.

    NOTE: requires _seed_valid_check_list() to work around an UNPLANNED,
    unrelated, pre-existing bug discovered this cycle -- see that helper's
    docstring. CreateCheckType raises AttributeError on every call without
    this test-only workaround (zero flexicon/ lines touched).
    """
    from SIL.LCModel.Core.Text import TsStringUtils

    project = target_sandbox
    raw_name = f"{TEST_PREFIX}Check_Raw "  # trailing space

    _seed_valid_check_list(project)

    check, create_exc = _safe(
        lambda: project.Checks.CreateCheckType(f"{TEST_PREFIX}Check_placeholder"),
        "PN4 seed CreateCheckType",
    )
    assert create_exc is None, f"Seed CreateCheckType raised: {create_exc}"

    wsHandle = project.project.DefaultAnalWs

    def _bypass_write():
        with project.Transaction("PN4 bypass write raw name"):
            ts = TsStringUtils.MakeString(raw_name, wsHandle)
            check.Name.set_String(wsHandle, ts)

    _, bypass_exc = _safe(_bypass_write, "PN4 bypass write")
    assert bypass_exc is None, f"Bypass write raised: {bypass_exc}"

    from SIL.LCModel.Core.KernelInterfaces import ITsString

    raw_reread = ITsString(check.Name.get_String(wsHandle)).Text
    print(f"[TABLE][PN4] raw stored Name (direct read): {raw_reread!r}")
    assert raw_reread == raw_name, (
        f"Precondition failed: expected the bypass write to store "
        f"{raw_name!r} verbatim -- got {raw_reread!r}"
    )

    unpadded_needle = f"{TEST_PREFIX}Check_Raw"
    padded_needle = f"{TEST_PREFIX}Check_Raw "

    find_unpadded, fexc1 = _safe(
        lambda: project.Checks.FindCheckType(unpadded_needle), "PN4 FindCheckType(unpadded)"
    )
    find_padded, fexc2 = _safe(
        lambda: project.Checks.FindCheckType(padded_needle), "PN4 FindCheckType(padded)"
    )
    assert fexc1 is None and fexc2 is None, f"Unexpected exception(s): {fexc1} / {fexc2}"

    print(
        f"[VERDICT][PN4] FindCheckType(unpadded) -> {find_unpadded!r} "
        f"(PREDICTED None); FindCheckType(padded) -> {find_padded!r} "
        f"(PREDICTED None)"
    )

    if find_unpadded is not None or find_padded is not None:
        print(
            "[REFUTATION][PN4] MEASURED OPPOSITE TO PREDICTION -- the needle "
            "DID find the padded haystack. This REFUTES the ruling's premise "
            "that dedup paths strip the needle only, never the haystack. "
            "Reported plainly, NOT reconciled."
        )
    assert find_unpadded is None, f"PN4 MISS: FindCheckType(unpadded) expected None, got {find_unpadded!r}"
    assert find_padded is None, f"PN4 MISS: FindCheckType(padded) expected None, got {find_padded!r}"


# ===========================================================================
# PN5 -- Q-242B: non-str payload into CreateCheckType silently persists an
# EMPTY name, no exception.
# ===========================================================================

@pytest.mark.live_phase("CheckOperations", "add")
def test_pn5_q242b_nonstr_payload_persists_empty_name(target_sandbox):
    """
    PN5 (Q-242B): Checks.CreateCheckType(<a plain non-str object>) ->
    PREDICTED NO exception, and a check type is created whose Name
    re-reads from the LCM as empty ("") or the "***" null marker.
    CheckOperations.py:196's
        name = name.strip() if isinstance(name, str) else ""
    converts any non-str payload to a literal empty string with no
    exception, because the preceding _ValidateParam(name, "name") at :194
    only checks for None (BaseOperations.py:2376-2377), not type.

    Re-reads the object FRESH from the LCM after the write (via GetName()
    AND the raw ITsString accessor) -- asserting on what was passed in
    would prove nothing.

    NOTE: requires _seed_valid_check_list() to work around an UNPLANNED,
    unrelated, pre-existing bug discovered this cycle -- see that helper's
    docstring. CreateCheckType raises AttributeError on every call without
    this test-only workaround (zero flexicon/ lines touched).
    """
    project = target_sandbox
    payload = _NonStrPayload()

    _seed_valid_check_list(project)

    check, create_exc = _safe(
        lambda: project.Checks.CreateCheckType(payload), "PN5 CreateCheckType(non-str)"
    )
    print(f"[VERDICT][PN5] CreateCheckType(non-str) -> exc={create_exc!r} (PREDICTED None)")
    assert create_exc is None, (
        f"PN5 MISS: expected CreateCheckType(non-str) to raise NO exception -- "
        f"got {create_exc}"
    )
    assert check is not None, "PN5: CreateCheckType(non-str) returned no object despite no exception"

    reread_name = project.Checks.GetName(check)
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    wsHandle = project.project.DefaultAnalWs
    raw_reread = ITsString(check.Name.get_String(wsHandle)).Text
    print(
        f"[TABLE][PN5] re-read via GetName(): {reread_name!r}; "
        f"raw ITsString re-read: {raw_reread!r}"
    )
    assert reread_name in ("", "***"), (
        f"PN5 MISS: expected the persisted name to re-read as '' or '***' -- "
        f"got {reread_name!r}"
    )


# ===========================================================================
# PN6 -- Q-242B second path: whitespace-only STRING into CreateCheckType
# silently persists an EMPTY name via the SAME line, different branch.
# ===========================================================================

@pytest.mark.live_phase("CheckOperations", "add")
def test_pn6_q242b_whitespace_string_persists_empty_name(target_sandbox):
    """
    PN6 (Q-242B second path): Checks.CreateCheckType("   ") ->
    PREDICTED NO exception, empty name persisted. "   ".strip() at :196
    yields "", and _ValidateParam("", "name") at :197 does not reject an
    empty string (only None), so the whitespace-only string silently
    becomes a persisted empty name via the str branch of the same line
    PN5 exercised via the non-str branch.

    NOTE: requires _seed_valid_check_list() to work around an UNPLANNED,
    unrelated, pre-existing bug discovered this cycle -- see that helper's
    docstring. CreateCheckType raises AttributeError on every call without
    this test-only workaround (zero flexicon/ lines touched).
    """
    project = target_sandbox

    _seed_valid_check_list(project)

    check, create_exc = _safe(
        lambda: project.Checks.CreateCheckType("   "), "PN6 CreateCheckType('   ')"
    )
    print(f"[VERDICT][PN6] CreateCheckType('   ') -> exc={create_exc!r} (PREDICTED None)")
    assert create_exc is None, (
        f"PN6 MISS: expected CreateCheckType('   ') to raise NO exception -- "
        f"got {create_exc}"
    )
    assert check is not None, "PN6: CreateCheckType('   ') returned no object despite no exception"

    reread_name = project.Checks.GetName(check)
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    wsHandle = project.project.DefaultAnalWs
    raw_reread = ITsString(check.Name.get_String(wsHandle)).Text
    print(
        f"[TABLE][PN6] re-read via GetName(): {reread_name!r}; "
        f"raw ITsString re-read: {raw_reread!r}"
    )
    assert reread_name in ("", "***"), (
        f"PN6 MISS: expected the persisted name to re-read as '' or '***' -- "
        f"got {reread_name!r}"
    )


# ===========================================================================
# PN7 -- the three-way split: how a non-str payload fails differs by site.
# ===========================================================================

@pytest.mark.live_phase("TextOperations", "read")
def test_pn7_three_way_split_nonstr_payload(target_sandbox):
    """
    PN7: a plain non-str payload (no .strip() method) passed as the name
    argument behaves differently depending on which validator the call
    site uses first:
      - Texts.Create          -> PREDICTED TypeError (_ValidateStringNotEmpty
                                  type-checks, TextOperations.py:151)
      - Discourse.CreateChart -> PREDICTED TypeError (same validator,
                                  DiscourseOperations.py:320)
      - Anthropology.Create   -> PREDICTED AttributeError (bare .strip()
                                  after a None-only _ValidateParam,
                                  AnthropologyOperations.py:263-265)
      - Texts.SetName         -> PREDICTED AttributeError (same shape,
                                  TextOperations.py:606-608)
    """
    project = target_sandbox
    payload = _NonStrPayload()

    # Need a valid text for CreateChart and SetName targets.
    text, seed_exc = _safe(
        lambda: project.Texts.Create(f"{TEST_PREFIX}p7_text"), "PN7 seed text"
    )
    assert seed_exc is None, f"Seed text Create raised: {seed_exc}"

    _, create_exc = _safe(lambda: project.Texts.Create(payload), "PN7 Texts.Create(non-str)")
    _, chart_exc = _safe(
        lambda: project.Discourse.CreateChart(text, payload), "PN7 Discourse.CreateChart(non-str)"
    )
    _, anthro_exc = _safe(
        lambda: project.Anthropology.Create(payload), "PN7 Anthropology.Create(non-str)"
    )
    _, setname_exc = _safe(
        lambda: project.Texts.SetName(text, payload), "PN7 Texts.SetName(non-str)"
    )

    print(
        f"[TABLE][PN7] Texts.Create->{create_exc!r} "
        f"Discourse.CreateChart->{chart_exc!r} "
        f"Anthropology.Create->{anthro_exc!r} "
        f"Texts.SetName->{setname_exc!r}"
    )
    print(
        "[VERDICT][PN7] predicted: Texts.Create=TypeError, "
        "Discourse.CreateChart=TypeError, Anthropology.Create=AttributeError, "
        "Texts.SetName=AttributeError"
    )

    assert create_exc is not None and create_exc.startswith("TypeError"), (
        f"PN7 MISS: Texts.Create(non-str) expected TypeError -- got {create_exc!r}"
    )
    assert chart_exc is not None and chart_exc.startswith("TypeError"), (
        f"PN7 MISS: Discourse.CreateChart(non-str) expected TypeError -- got {chart_exc!r}"
    )
    assert anthro_exc is not None and anthro_exc.startswith("AttributeError"), (
        f"PN7 MISS: Anthropology.Create(non-str) expected AttributeError -- got {anthro_exc!r}"
    )
    assert setname_exc is not None and setname_exc.startswith("AttributeError"), (
        f"PN7 MISS: Texts.SetName(non-str) expected AttributeError -- got {setname_exc!r}"
    )

    # Confirm SetName's failed attempt did not mutate the text's name.
    assert project.Texts.GetName(text) == f"{TEST_PREFIX}p7_text", (
        "Texts.SetName(non-str) raised, but the text's name changed anyway -- "
        "the raise must happen BEFORE any write."
    )


# ===========================================================================
# PN8 -- THE duplicate-explosion proof.
# ===========================================================================

@pytest.mark.live_phase("TextOperations", "add")
def test_pn8_duplicate_explosion_via_unstripped_haystack(target_sandbox):
    """
    PN8, FLIPPED to assert T2's FIXED behaviour -- THE C8 anti-regression
    pin (tasks.md T2, spec.md C8): layer-B store a text named
    "TEST_NF_Dup " (trailing space -- this now matches what the REAL,
    fixed Create() itself would persist, not merely a simulation of a
    future state). Then call Texts.Create("TEST_NF_Dup ") through the
    PUBLIC API with the SAME padded name -> PREDICTED it RAISES
    FP_ParameterError ("already exists"), because Exists() now strips
    BOTH sides of the comparison (T2's fix), so the second call's padded
    needle matches the first (bypass-written) record's padded haystack.

    C8's SECOND half is also checked here: the FIRST (bypass-written)
    text's stored Name must re-read BYTE-IDENTICAL (trailing space
    intact) -- re-read from the LCM, not merely the value passed in.

    PRE-FIX BEHAVIOUR (historical record, cycle 1, `spec.md` C2/C8): before
    T2's fix, this same scenario measured the OPPOSITE -- Create()'s own
    duplicate check called self.Exists(name) where `name` had ALREADY been
    stripped (old `:152`) to "TEST_NF_Dup", and Exists("TEST_NF_Dup")
    against the raw unstripped haystack "TEST_NF_Dup " returned False (PN2's
    mechanism), so the SECOND Create() call SUCCEEDED, producing two
    distinct IText objects -- the duplicate-explosion this feature exists
    to close. That run also flagged a non-binding sub-detail: the second
    (public-API) record's stored name was NOT byte-identical to the first,
    because pre-fix Create() persisted its own already-stripped local
    `name`, not the caller's original argument. Per `spec.md` C2's own
    prediction, once C4 lands both persist AND comparison together, that
    intermediate "duplicate persists non-byte-identically" state is no
    longer reachable in practice -- this flipped test confirms exactly
    that: there is no longer a second record to compare at all, because
    the second call now raises instead of persisting.
    """
    from SIL.LCModel.Core.Text import TsStringUtils
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = target_sandbox
    dup_name = f"{TEST_PREFIX}Dup "  # trailing space

    first_text, seed_exc = _safe(
        lambda: project.Texts.Create(f"{TEST_PREFIX}Dup_placeholder"), "PN8 seed Create"
    )
    assert seed_exc is None, f"Seed Create raised: {seed_exc}"

    wsHandle = project.project.DefaultAnalWs

    def _bypass_write():
        with project.Transaction("PN8 bypass write raw dup name"):
            ts = TsStringUtils.MakeString(dup_name, wsHandle)
            first_text.Name.set_String(wsHandle, ts)

    _, bypass_exc = _safe(_bypass_write, "PN8 bypass write")
    assert bypass_exc is None, f"Bypass write raised: {bypass_exc}"

    first_raw = ITsString(first_text.Name.BestAnalysisAlternative).Text
    print(f"[TABLE][PN8] first (bypass) text stored Name: {first_raw!r}")
    assert first_raw == dup_name, (
        f"Precondition failed: expected bypass write to store {dup_name!r} "
        f"verbatim -- got {first_raw!r}"
    )

    second_text, create_exc = _safe(
        lambda: project.Texts.Create(dup_name), "PN8 Create(padded, public API)"
    )
    print(
        f"[VERDICT][PN8] Create({dup_name!r}) via public API -> exc={create_exc!r} "
        f"(PREDICTED FP_ParameterError, post-fix)"
    )

    if create_exc is None:
        print(
            "[REFUTATION][PN8] MEASURED OPPOSITE TO PREDICTION -- Create() "
            "SUCCEEDED instead of raising, meaning the duplicate guard did "
            "NOT fire despite T2's comparison-symmetry fix. This REFUTES "
            "the fix's premise. Reported plainly, NOT reconciled."
        )
    assert create_exc is not None and create_exc.startswith("FP_ParameterError"), (
        f"PN8 MISS (BINDING, C8 pin half 1): expected Texts.Create({dup_name!r}) "
        f"to RAISE FP_ParameterError ('already exists'), post-fix -- got "
        f"{create_exc!r} instead (second_text={second_text!r})"
    )

    # C8 pin half 2: the FIRST (bypass-written) text's stored Name must
    # re-read BYTE-IDENTICAL from the LCM after the write -- re-read here,
    # not merely re-asserted against the value passed in earlier.
    first_reread = ITsString(first_text.Name.BestAnalysisAlternative).Text
    print(f"[TABLE][PN8] first text stored Name, re-read after the rejected duplicate attempt: {first_reread!r}")
    assert first_reread == dup_name, (
        f"PN8 MISS (BINDING, C8 pin half 2): expected the first text's "
        f"stored Name to re-read byte-identical to {dup_name!r} -- got "
        f"{first_reread!r}"
    )

    # Confirm exactly ONE IText matches this name post-fix -- no duplicate
    # was created (the rejected second Create() call must not have
    # persisted a partial/second record).
    dup_texts = []
    for t in project.Texts.GetAll():
        t_name = ITsString(t.Name.BestAnalysisAlternative).Text
        if t_name and t_name.strip() == dup_name.strip():
            dup_texts.append((str(t.Guid), t_name))
    print(f"[SUMMARY][PN8] texts matching {dup_name!r} post-fix (stripped comparison): {dup_texts}")

    assert len(dup_texts) == 1, (
        f"PN8 MISS (BINDING): expected exactly ONE IText object matching "
        f"{dup_name!r} post-fix (the duplicate must have been REJECTED, "
        f"not persisted) -- found {len(dup_texts)}: {dup_texts}"
    )


# ===========================================================================
# T1 -- DiscourseOperations persist fix (spec.md C4/C8, tasks.md T1).
# CreateChart/SetChartName no longer rebind `name = name.strip()` before
# persisting; the caller's original bytes now reach TsStringUtils.MakeString.
# Per C3's explicit per-family carve-out, DiscourseOperations has NO
# comparison/dedup method -- only the persist half of C8 is pin-worthy here.
# ===========================================================================

def _patch_discourse_factory_bug():
    """
    UNPLANNED DISCOVERY #1, worked around here for PN9/PN10 ONLY (see this
    docstring, `_build_real_chart()`'s docstring below for discovery #2,
    the T1 evidence file's RESULTS section, and the programmer report's
    CONTRACT CONTRADICTIONS FOUND section): DiscourseOperations.py's
    CreateChart (`flexicon/code/TextsWords/DiscourseOperations.py:335`,
    UNTOUCHED by this task's T1 edit, which only removed the `.strip()`
    rebindings at the OLD `:327`/`:482`) references the bare name
    `IConstChartFactory`, which is NOT imported anywhere in the module.
    The import list at `:16-24` was already corrected to
    `IDsConstChartFactory` (see the inline "Fixed: was IConstChartFactory"
    comment on that import line, `git blame` dates it to commit
    8716a5f2d, 2025-11-26), but the usage site at `:335` was never updated
    to match (introduced by d0aac1a54, 2026-06-23). Effect: CreateChart()
    raises `NameError` on EVERY call, for EVERY payload, BEFORE this
    bug is worked around here.

    Workaround (MODULE-NAMESPACE PATCH, test session only, ZERO lines
    under flexicon/ touched beyond T1's two authorised `.strip()`
    removals -- confirmed by `git diff --stat -- flexicon/`): bind the
    already-imported, correctly-named `IDsConstChartFactory` to the
    missing bare name `IConstChartFactory` in the DiscourseOperations
    module's namespace, so the existing (buggy, unrelated, NOT fixed
    here) line resolves at runtime instead of raising `NameError`. This
    does not change which factory is used -- both names would refer to
    the SAME already-corrected LCM interface. Do NOT fix the underlying
    bug in `flexicon/code/TextsWords/DiscourseOperations.py` here -- it
    is out of T1's exact two-expression scope; it is recorded, not
    fixed, exactly as `spec.md` section 3 treats the analogous
    `CheckOperations._GetCheckList()` bug.

    NOTE, discovered AFTER this patch was written (see PN9 below): fixing
    discovery #1 alone is NOT enough to reach CreateChart's persist line.
    A SECOND, independent, unrelated, deeper bug (discovery #2) blocks it
    completely and cannot be worked around by any test-harness-only
    patch (proven empirically, not merely asserted -- see PN9's
    docstring). PN9 therefore does NOT call CreateChart() through to a
    successful return; it characterizes the (unrelated) failure instead.
    """
    import flexicon.code.TextsWords.DiscourseOperations as _disc_mod
    from SIL.LCModel import IDsConstChartFactory

    if not hasattr(_disc_mod, "IConstChartFactory"):
        _disc_mod.IConstChartFactory = IDsConstChartFactory


def _build_real_chart(project, initial_name):
    """
    Construct a real, correctly-owned IDsConstChart WITHOUT going through
    the broken public `Discourse.CreateChart()` (see PN9's docstring for
    why it cannot succeed today), so `SetChartName` -- the OTHER T1 site --
    can still be live-verified end-to-end through its own real public API.

    UNPLANNED DISCOVERY #2 (this is the reason `_build_real_chart` exists
    at all, not just a convenience helper): CreateChart's own collection
    check, `hasattr(text_obj.ContentsOA, "ChartsOC")`
    (DiscourseOperations.py:340, UNTOUCHED by T1), is checking the WRONG
    LCM interface for chart ownership. Confirmed by direct reflection on
    the live LCM assemblies: `IStText` (the type of `IText.ContentsOA`)
    has NO `ChartsOC` member at all (`dir(IStText)` contains zero
    "*hart*" names); the real owner of `ChartsOC` in the LCM model is
    `IDsDiscourseData`, a project-level singleton reached via
    `LangProject.DiscourseDataOA`, which has no ownership relationship to
    any individual `IText`/`IStText` whatsoever. This means CreateChart's
    `if hasattr(...): ... else: raise FP_ParameterError("Text contents
    does not support charts")` branch takes the `else` on EVERY call, for
    EVERY text, unconditionally -- independent of and deeper than
    discovery #1 (the `IConstChartFactory` NameError). Both bugs predate
    this feature and are unrelated to the name-field whitespace/identity
    question; NEITHER is fixed here (out of T1's exact two-expression
    scope) -- both are recorded, exactly as `spec.md` section 3 treats
    the analogous `CheckOperations._GetCheckList()` bug.

    Also confirmed empirically (throwaway probe, not committed) that this
    specific blocker CANNOT be worked around by a test-harness-only
    monkeypatch the way discovery #1 was: pythonnet regenerates a fresh
    Python wrapper object on every `.ContentsOA` property access, so a
    Python-level attribute assigned to one wrapper instance
    (`text.ContentsOA.ChartsOC = stub`) is invisible the next time
    CreateChart's OWN code calls `text_obj.ContentsOA` internally. There
    is no non-invasive way to make the real `CreateChart()` method
    succeed without editing `flexicon/code/TextsWords/DiscourseOperations.py`
    itself -- which T1's exact scope forbids. This is why PN9 below
    characterizes the failure instead of asserting success, and why this
    helper builds the chart through the CORRECT LCM ownership path
    (`LangProject.DiscourseDataOA.ChartsOC`) so SetChartName -- the site
    that does NOT depend on CreateChart working -- can still be fully,
    honestly live-verified.
    """
    from SIL.LCModel import IDsConstChartFactory, IDsDiscourseDataFactory
    from SIL.LCModel.Core.Text import TsStringUtils

    lp = project.project.LangProject
    discourse_data = lp.DiscourseDataOA
    wsHandle = project.project.DefaultAnalWs

    with project.Transaction("T1 probe: ensure DiscourseDataOA exists"):
        if not discourse_data:
            dd_factory = project.project.ServiceLocator.GetService(IDsDiscourseDataFactory)
            discourse_data = dd_factory.Create()
            lp.DiscourseDataOA = discourse_data

        chart_factory = project.project.ServiceLocator.GetService(IDsConstChartFactory)
        chart = chart_factory.Create()
        discourse_data.ChartsOC.Add(chart)
        ts = TsStringUtils.MakeString(initial_name, wsHandle)
        chart.Name.set_String(wsHandle, ts)

    return chart


@pytest.mark.live_phase("DiscourseOperations", "add")
def test_pn9_t1_createchart_blocked_by_unrelated_preexisting_bug(target_sandbox):
    """
    T1-P1, REVISED after live measurement (not a MISS of T1's own fix --
    see below): the ORIGINAL prediction was that, after removing the
    `.strip()` rebinding, `Discourse.CreateChart(text, "TEST_NF_Chart_Raw ")`
    would persist the chart's Name byte-identically. That prediction is
    UNTESTABLE through the public API today: CreateChart() raises
    `FP_ParameterError("Text contents does not support charts")` on EVERY
    call, for EVERY payload, due to UNPLANNED DISCOVERY #2 (see
    `_build_real_chart`'s docstring) -- a bug that is independent of,
    deeper than, and unrelated to T1's whitespace fix, and confirmed
    (by direct LCM reflection) to predate this task. This test locks
    down that CHARACTERIZATION plainly, rather than asserting a false
    pass or silently skipping: the exception is identical for a padded
    and unpadded name (proving T1's own edit is not the cause), so this
    is reported as `FAIL: unverified` for the CreateChart persist pin
    specifically, escalated in the programmer report's CONTRACT
    CONTRADICTIONS FOUND section, NOT smoothed over. T1's actual code
    change at the persist line is confirmed correct BY INSPECTION only
    (the caller's `name` now flows unmodified into
    `TsStringUtils.MakeString(name, wsHandle)`); this test proves the
    surrounding method cannot reach that line at all today, live-or-not.
    """
    _patch_discourse_factory_bug()  # discovery #1 -- does not fully unblock; see docstring above

    project = target_sandbox
    padded_name = f"{TEST_PREFIX}Chart_Raw "  # trailing space
    unpadded_name = f"{TEST_PREFIX}Chart_Raw_Unpadded"

    text, seed_exc = _safe(
        lambda: project.Texts.Create(f"{TEST_PREFIX}Chart_Raw_text"), "PN9 seed text"
    )
    assert seed_exc is None, f"Seed text Create raised: {seed_exc}"

    _, padded_exc = _safe(
        lambda: project.Discourse.CreateChart(text, padded_name), "PN9 CreateChart(padded)"
    )
    _, unpadded_exc = _safe(
        lambda: project.Discourse.CreateChart(text, unpadded_name), "PN9 CreateChart(unpadded)"
    )

    print(
        f"[VERDICT][PN9] CreateChart(padded) -> {padded_exc!r}; "
        f"CreateChart(unpadded) -> {unpadded_exc!r} "
        f"(both PREDICTED to fail IDENTICALLY, proving the blocker is "
        f"unrelated to T1's whitespace edit)"
    )
    assert padded_exc is not None and padded_exc.startswith("FP_ParameterError"), (
        f"PN9: expected the KNOWN unrelated blocker (FP_ParameterError: "
        f"Text contents does not support charts) -- got {padded_exc!r}. "
        f"If this now says something ELSE, discovery #2 may have been "
        f"fixed/changed by someone -- re-investigate before assuming T1 "
        f"is verified."
    )
    assert padded_exc == unpadded_exc, (
        f"PN9 MISS: padded and unpadded CreateChart calls failed "
        f"DIFFERENTLY ({padded_exc!r} vs {unpadded_exc!r}) -- this would "
        f"suggest T1's own edit IS implicated, contradicting this test's "
        f"characterization; escalate immediately."
    )


@pytest.mark.live_phase("DiscourseOperations", "modify")
def test_pn10_t1_setchartname_persists_raw_bytes(target_sandbox):
    """
    T1-P2 (anti-regression pin, persist half of C8 only, FULLY live-
    verified through the real public `SetChartName` API): Discourse.
    SetChartName(chart, "TEST_NF_Chart_Renamed ") (trailing space) is
    PREDICTED to persist the chart's Name BYTE-IDENTICAL to the caller's
    original argument, because SetChartName no longer rebinds
    `name = name.strip()` before TsStringUtils.MakeString(name, wsHandle).
    The chart itself is built via `_build_real_chart()` (correct LCM
    ownership path, `LangProject.DiscourseDataOA.ChartsOC`), NOT via the
    broken public `CreateChart()` (see PN9) -- SetChartName does not
    depend on CreateChart working, so this is a genuine, complete live
    verification of T1's SetChartName edit specifically. Re-read from the
    LCM directly after the write -- asserting on the value passed in
    would prove nothing.
    """
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = target_sandbox
    initial_name = f"{TEST_PREFIX}Chart_Rename_Seed"
    padded_name = f"{TEST_PREFIX}Chart_Renamed "  # trailing space

    chart = _build_real_chart(project, initial_name)

    _, setname_exc = _safe(
        lambda: project.Discourse.SetChartName(chart, padded_name), "PN10 SetChartName(padded)"
    )
    assert setname_exc is None, f"SetChartName raised unexpectedly: {setname_exc}"

    wsHandle = project.project.DefaultAnalWs
    raw_reread = ITsString(chart.Name.get_String(wsHandle)).Text
    print(f"[TABLE][PN10] chart stored Name (direct read): {raw_reread!r}")
    print(
        f"[VERDICT][PN10] SetChartName({padded_name!r}) stored Name -> "
        f"{raw_reread!r} (PREDICTED byte-identical to {padded_name!r})"
    )
    assert raw_reread == padded_name, (
        f"PN10 MISS: expected SetChartName to persist {padded_name!r} "
        f"byte-identically -- got {raw_reread!r}"
    )


@pytest.mark.live_phase("DiscourseOperations", "read")
def test_pn11_t1_createchart_whitespace_only_still_rejected(target_sandbox):
    """
    T1-P4 (regression guard, not new scope): CreateChart/SetChartName's
    unchanged `_ValidateStringNotEmpty` call still rejects a whitespace-only
    name with FP_ParameterError. Confirms removing the `.strip()` rebinding
    did not weaken the existing validation (which runs on the caller's
    argument directly, before any stripping ever happened).
    """
    from flexicon.code.FLExProject import FP_ParameterError

    project = target_sandbox

    text, seed_exc = _safe(
        lambda: project.Texts.Create(f"{TEST_PREFIX}Chart_WsOnly_text"), "PN11 seed text"
    )
    assert seed_exc is None, f"Seed text Create raised: {seed_exc}"

    _, create_exc = _safe(
        lambda: project.Discourse.CreateChart(text, "   "), "PN11 CreateChart('   ')"
    )
    print(f"[VERDICT][PN11] CreateChart('   ') -> {create_exc!r} (PREDICTED FP_ParameterError)")
    assert create_exc is not None and create_exc.startswith("FP_ParameterError"), (
        f"PN11 MISS: CreateChart('   ') expected FP_ParameterError -- got {create_exc!r}"
    )


# ===========================================================================
# PN12 -- T3 -- AnthropologyOperations.Create: THE C8 anti-regression pin,
# BOTH halves, through the real public API (spec.md C8, tasks.md T3).
# ===========================================================================

@pytest.mark.live_phase("AnthropologyOperations", "add")
def test_pn12_t3_anthropology_create_duplicate_explosion_pin(target_sandbox):
    """
    PN12, THE C8 anti-regression pin for AnthropologyOperations.Create
    (tasks.md T3, spec.md C8), through the REAL public API end to end (no
    layer-B bypass needed here, unlike PN3/PN8, because Create() itself is
    now the thing under test for BOTH halves):

      Anthropology.Create("TEST_NF_Anth ") (trailing space) called TWICE ->
      - the SECOND call is PREDICTED to RAISE FP_ParameterError ("already
        exists"), because Create()'s own `self.Exists(name)` check
        (:269-270) now reaches Find()'s symmetric, inline-stripped
        comparison (T3's fix) with the SAME padded name that the first
        call persisted.
      - the FIRST item's stored Name is PREDICTED to re-read
        BYTE-IDENTICAL ('TEST_NF_Anth ', trailing space intact) from the
        LCM, re-read AFTER the rejected duplicate attempt -- a genuine
        re-query, not a re-assertion of the value passed in (same pattern
        as T2's PN8 `first_reread`).

    PRE-FIX BEHAVIOUR (historical record): before T3 landed, Create()'s own
    non-reassigning `.strip()` did not exist yet -- the local `name` was
    REASSIGNED to its stripped form at old `:265`, so (a) the SECOND
    Create() call's `self.Exists(name)` check ran against an unstripped
    haystack that was itself the STRIPPED local from the first persist,
    making the duplicate check pass trivially in the single-call-family
    case tested here (both calls persist "TEST_NF_Anth" with no trailing
    space, since the stripped local -- not the caller's original argument
    -- was what reached `TsStringUtils.MakeString`), and (b) the first
    item's stored Name never carried the caller's trailing space at all.
    This test's post-fix assertions (byte-identical WITH the trailing
    space, second call REJECTED) are only reachable once T3's persist fix
    (throwaway strip, no reassignment) and comparison fix (Find's inline
    symmetric strip) are BOTH in place together, per C2/C8.
    """
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = target_sandbox
    padded_name = f"{TEST_PREFIX}Anth "  # trailing space, byte-for-byte

    first_item, first_exc = _safe(
        lambda: project.Anthropology.Create(padded_name), "PN12 Create #1 (padded)"
    )
    assert first_exc is None, f"PN12: first Create raised unexpectedly: {first_exc}"
    assert first_item is not None, "PN12: first Create returned no object despite no exception"

    wsHandle = project.project.DefaultAnalWs
    first_raw = ITsString(first_item.Name.get_String(wsHandle)).Text
    print(f"[TABLE][PN12] first item stored Name (direct read, before duplicate attempt): {first_raw!r}")
    assert first_raw == padded_name, (
        f"PN12 precondition failed: expected the first Create() to persist "
        f"{padded_name!r} verbatim -- got {first_raw!r}"
    )

    second_item, second_exc = _safe(
        lambda: project.Anthropology.Create(padded_name), "PN12 Create #2 (padded, duplicate)"
    )
    print(
        f"[VERDICT][PN12] Create({padded_name!r}) called a second time -> "
        f"exc={second_exc!r} (PREDICTED FP_ParameterError, post-fix)"
    )

    if second_exc is None:
        print(
            "[REFUTATION][PN12] MEASURED OPPOSITE TO PREDICTION -- the "
            "second Create() SUCCEEDED instead of raising, meaning the "
            "duplicate guard did NOT fire despite T3's comparison-symmetry "
            "fix. This REFUTES the fix's premise. Reported plainly, NOT "
            "reconciled."
        )
    assert second_exc is not None and second_exc.startswith("FP_ParameterError"), (
        f"PN12 MISS (BINDING, C8 pin half 1): expected the second "
        f"Anthropology.Create({padded_name!r}) to RAISE FP_ParameterError "
        f"('already exists'), post-fix -- got {second_exc!r} instead "
        f"(second_item={second_item!r})"
    )

    # C8 pin half 2: the FIRST item's stored Name must re-read
    # BYTE-IDENTICAL from the LCM after the rejected duplicate attempt --
    # a genuine re-query, not merely re-asserted against the value read
    # before the second call.
    first_reread = ITsString(first_item.Name.get_String(wsHandle)).Text
    print(
        f"[TABLE][PN12] first item stored Name, re-read after the "
        f"rejected duplicate attempt: {first_reread!r}"
    )
    assert first_reread == padded_name, (
        f"PN12 MISS (BINDING, C8 pin half 2): expected the first item's "
        f"stored Name to re-read byte-identical to {padded_name!r} -- got "
        f"{first_reread!r}"
    )

    # Confirm exactly ONE item matches this name post-fix -- no duplicate
    # was created (the rejected second Create() call must not have
    # persisted a partial/second record).
    dup_items = []
    for it in project.Anthropology.GetAll():
        it_name = ITsString(it.Name.get_String(wsHandle)).Text
        if it_name and it_name.strip() == padded_name.strip():
            dup_items.append((str(it.Guid), it_name))
    print(f"[SUMMARY][PN12] items matching {padded_name!r} post-fix (stripped comparison): {dup_items}")

    assert len(dup_items) == 1, (
        f"PN12 MISS (BINDING): expected exactly ONE ICmAnthroItem matching "
        f"{padded_name!r} post-fix (the duplicate must have been REJECTED, "
        f"not persisted) -- found {len(dup_items)}: {dup_items}"
    )


# ===========================================================================
# PN13 -- T3 -- AnthropologyOperations.CreateSubitem: persist half ONLY.
# No dedup check exists here (spec.md C5's explicit observation) -- do NOT
# assert a duplicate-rejection half for CreateSubitem.
# ===========================================================================

@pytest.mark.live_phase("AnthropologyOperations", "add")
def test_pn13_t3_anthropology_createsubitem_persists_raw_bytes(target_sandbox):
    """
    PN13 (persist-only pin, tasks.md T3): CreateSubitem(parent,
    "TEST_NF_Sub ") (trailing space) is PREDICTED to persist the subitem's
    Name BYTE-IDENTICAL to the caller's original argument, because
    CreateSubitem no longer reassigns `name = name.strip()` before
    `TsStringUtils.MakeString(name, wsHandle)` -- same throwaway-strip
    mechanism as Create() above.

    NO dedup assertion here, deliberately: `spec.md` C5 observes
    CreateSubitem has no dedup check at all, unlike Create, and this
    feature does NOT add one. Calling CreateSubitem twice with the same
    padded name is expected to SUCCEED both times, producing two distinct
    subitems -- that is pre-existing, out-of-scope behaviour, not
    re-verified here.
    """
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = target_sandbox
    padded_name = f"{TEST_PREFIX}Sub "  # trailing space

    parent, parent_exc = _safe(
        lambda: project.Anthropology.Create(f"{TEST_PREFIX}Sub_parent"), "PN13 seed parent Create"
    )
    assert parent_exc is None, f"PN13: seed parent Create raised: {parent_exc}"

    subitem, sub_exc = _safe(
        lambda: project.Anthropology.CreateSubitem(parent, padded_name), "PN13 CreateSubitem(padded)"
    )
    assert sub_exc is None, f"PN13: CreateSubitem raised unexpectedly: {sub_exc}"
    assert subitem is not None, "PN13: CreateSubitem returned no object despite no exception"

    wsHandle = project.project.DefaultAnalWs
    stored = ITsString(subitem.Name.get_String(wsHandle)).Text
    print(f"[TABLE][PN13] subitem stored Name (direct read): {stored!r}")
    print(
        f"[VERDICT][PN13] CreateSubitem({padded_name!r}) stored Name -> "
        f"{stored!r} (PREDICTED byte-identical to {padded_name!r})"
    )
    assert stored == padded_name, (
        f"PN13 MISS: expected CreateSubitem to persist {padded_name!r} "
        f"byte-identically -- got {stored!r}"
    )


# ===========================================================================
# PN14 -- T3 -- Shape-B preservation: a non-str payload still raises
# AttributeError at BOTH Create and CreateSubitem, unchanged from pre-fix
# (proves T3's throwaway-strip mechanism, not plain deletion, was used).
# ===========================================================================

@pytest.mark.live_phase("AnthropologyOperations", "read")
def test_pn14_t3_shapeb_nonstr_payload_still_attributeerror(target_sandbox):
    """
    PN14 (Shape-B preservation pin, tasks.md T3 rule 1): a plain non-str
    payload (no .strip() method) passed as `name` is PREDICTED to still
    raise AttributeError at BOTH Create() and CreateSubitem(), unchanged
    from pre-fix -- because both sites' only upstream guard is the
    null-check-only `_ValidateParam` (no isinstance check), so the
    throwaway, non-reassigning `name.strip()` call T3 introduced is
    STILL the thing that raises, exactly as it did before this fix (when
    `.strip()` was the reassignment target instead of a throwaway call).
    This is the live proof that T3 followed cycle-2's T2 precedent
    (`reviews/cycle2-t2-programmer.md`) rather than T1's plain-deletion
    shape, which would have silently swallowed this AttributeError and
    changed the exception type -- forbidden by C7(b).

    Anthropology.Create(non-str) is ALSO covered by PN7 above (unchanged
    by this task); PN14 adds CreateSubitem's own non-str check, which PN7
    does not cover, and re-confirms Create's for completeness in one place
    alongside it.
    """
    project = target_sandbox
    payload = _NonStrPayload()

    parent, parent_exc = _safe(
        lambda: project.Anthropology.Create(f"{TEST_PREFIX}ShapeB_parent"), "PN14 seed parent Create"
    )
    assert parent_exc is None, f"PN14: seed parent Create raised: {parent_exc}"

    _, create_exc = _safe(
        lambda: project.Anthropology.Create(payload), "PN14 Anthropology.Create(non-str)"
    )
    _, subitem_exc = _safe(
        lambda: project.Anthropology.CreateSubitem(parent, payload), "PN14 Anthropology.CreateSubitem(non-str)"
    )

    print(
        f"[TABLE][PN14] Anthropology.Create(non-str)->{create_exc!r} "
        f"Anthropology.CreateSubitem(non-str)->{subitem_exc!r}"
    )
    print(
        "[VERDICT][PN14] predicted: Create=AttributeError, "
        "CreateSubitem=AttributeError (both unchanged from pre-fix)"
    )

    assert create_exc is not None and create_exc.startswith("AttributeError"), (
        f"PN14 MISS: Anthropology.Create(non-str) expected AttributeError -- got {create_exc!r}"
    )
    assert subitem_exc is not None and subitem_exc.startswith("AttributeError"), (
        f"PN14 MISS: Anthropology.CreateSubitem(non-str) expected AttributeError -- got {subitem_exc!r}"
    )


# ===========================================================================
# PN15 -- T3 -- Q-242D disclosure measurement (NOT a fix): what does
# Create("   ") actually do post-fix? Measure and record; do not "fix" it.
# ===========================================================================

@pytest.mark.live_phase("AnthropologyOperations", "add")
def test_pn15_t3_q242d_whitespace_only_create_measurement(target_sandbox):
    """
    PN15 (Q-242D disclosure measurement, tasks.md T3 rule 6 / spec.md C7(b)
    boundary -- explicitly NOT a fix): Anthropology.Create("   ")
    (whitespace-only string) is PREDICTED to raise NO exception and to
    persist the literal three-space string "   " verbatim, because:
      - `_ValidateParam("   ", "name")` (:263) is a null-check only -- it
        does not reject a non-empty (even whitespace-only) string.
      - The throwaway `name.strip()` call T3 introduced (:265-270) is
        NON-REASSIGNING, so it has no effect on what gets persisted either
        way -- pre-fix, "   ".strip() == "" WAS reassigned and persisted as
        an empty name; post-fix, "   " itself reaches
        `TsStringUtils.MakeString`.
      - `self.Exists("   ")` (:269) delegates to Find("   "), whose own
        `if not name or not name.strip(): return None` guard (:555,
        UNCHANGED by T3) returns None for an all-whitespace needle, so the
        dedup check never rejects this call regardless of what has already
        been persisted.

    This is a DELIBERATE, DISCLOSED behaviour change (post-fix: persists
    "   "; pre-fix: persisted ""), explicitly ruled OUT OF SCOPE to fix by
    `spec.md` C7(b) / tasks.md T3 rule 6 (Q-242C/Q-242D territory, not this
    feature's). This test measures and records the value; it does NOT
    assert any particular value is "correct" beyond confirming the
    measurement matches the stated prediction, and it does NOT add a
    whitespace-only rejection.
    """
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = target_sandbox
    whitespace_only = "   "

    item, create_exc = _safe(
        lambda: project.Anthropology.Create(whitespace_only), "PN15 Create('   ')"
    )
    print(f"[VERDICT][PN15] Create('   ') -> exc={create_exc!r} (PREDICTED None, disclosure only)")
    assert create_exc is None, (
        f"PN15 MEASUREMENT NOTE: expected Create('   ') to raise NO "
        f"exception (Q-242D, disclosed not fixed) -- got {create_exc!r}. "
        f"If this now raises, Q-242C/Q-242D's premise for this family has "
        f"changed; escalate, do not silently update this assertion."
    )
    assert item is not None, "PN15: Create('   ') returned no object despite no exception"

    wsHandle = project.project.DefaultAnalWs
    stored = ITsString(item.Name.get_String(wsHandle)).Text
    print(f"[TABLE][PN15] Create('   ') stored Name (direct read, MEASURED): {stored!r}")
    print(
        f"[SUMMARY][PN15] Q-242D disclosure: Anthropology.Create('   ') "
        f"post-fix persists {stored!r} (predicted {whitespace_only!r}) -- "
        f"measured, NOT fixed, per spec.md C7(b)/tasks.md T3 rule 6."
    )
    assert stored == whitespace_only, (
        f"PN15 MEASUREMENT: expected the persisted name to measure as "
        f"{whitespace_only!r} -- got {stored!r}. Record the MEASURED value "
        f"in the evidence file either way; do not silently adjust this "
        f"prediction after the fact per the C28 forward rule."
    )
