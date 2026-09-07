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
    PN2 (CORE, binding under the refutation clause): create a text, then
    set its Name DIRECTLY via TsStringUtils.MakeString to "TEST_NF_Raw "
    (layer B, bypassing Texts.SetName/Create's own strip -- simulates
    POST-FIX stored state). Then:
      - Exists("TEST_NF_Raw")  -> PREDICTED False
      - Exists("TEST_NF_Raw ") -> PREDICTED False
    Both predicted False because the needle is stripped either way but the
    haystack (raw stored name, with its trailing space) is never stripped
    by Exists() (TextOperations.py:458 strips only the `name` PARAMETER;
    :464 builds the haystack key straight from `text.Name`, and
    normalize_match_key does no stripping at all).
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
        f"(PREDICTED False); Exists({padded_needle!r}) -> {found_padded!r} "
        f"(PREDICTED False)"
    )

    if found_unpadded is not False or found_padded is not False:
        print(
            "[REFUTATION][PN2] MEASURED OPPOSITE TO PREDICTION -- the needle "
            "DID find the padded haystack. This REFUTES the ruling's premise "
            "that dedup paths strip the needle only, never the haystack. "
            "Reported plainly, NOT reconciled."
        )
    assert found_unpadded is False, (
        f"PN2 MISS (unpadded needle): expected False, got {found_unpadded!r}"
    )
    assert found_padded is False, (
        f"PN2 MISS (padded needle): expected False, got {found_padded!r}"
    )


# ===========================================================================
# PN3 -- same layer-B shape for Anthropology.Find/Exists.
# ===========================================================================

@pytest.mark.live_phase("AnthropologyOperations", "modify")
def test_pn3_anthropology_haystack_never_stripped(target_sandbox):
    """
    PN3: same layer-B shape as PN2, applied to Anthropology.Find/Exists.
    Find's needle-strip is at AnthropologyOperations.py:558; the haystack
    key is built raw at :565 (via item.Name.get_String(wsHandle), no
    .strip() in that line or in normalize_match_key). Predicted None (Find)
    / False (Exists) for both the unpadded and padded needle.
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
        f"[VERDICT][PN3] Find(unpadded) -> {find_unpadded!r} (PREDICTED None); "
        f"Find(padded) -> {find_padded!r} (PREDICTED None); "
        f"Exists(unpadded) -> {exists_unpadded!r} (PREDICTED False); "
        f"Exists(padded) -> {exists_padded!r} (PREDICTED False)"
    )

    assert find_unpadded is None, f"PN3 MISS: Find(unpadded) expected None, got {find_unpadded!r}"
    assert find_padded is None, f"PN3 MISS: Find(padded) expected None, got {find_padded!r}"
    assert exists_unpadded is False, f"PN3 MISS: Exists(unpadded) expected False, got {exists_unpadded!r}"
    assert exists_padded is False, f"PN3 MISS: Exists(padded) expected False, got {exists_padded!r}"


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
    PN8 (binding under the refutation clause): layer-B store a text named
    "TEST_NF_Dup " (trailing space, bypassing Create's own strip), then
    call Texts.Create("TEST_NF_Dup ") through the PUBLIC API ->
    PREDICTED it SUCCEEDS (no FP_ParameterError for "already exists"),
    because Create()'s own duplicate check (:155) calls
    self.Exists(name) where `name` has ALREADY been stripped (:152) to
    "TEST_NF_Dup", and per PN2's mechanism Exists("TEST_NF_Dup") against
    the raw unstripped haystack "TEST_NF_Dup " returns False.

    FLAGGED NUANCE (stated in the predictions file before this run):
    because Create() persists the ALREADY-STRIPPED local `name` (not the
    original argument), the SECOND text's stored Name is predicted to be
    "TEST_NF_Dup" (no trailing space) -- not byte-identical to the first
    (bypass-created) text's stored "TEST_NF_Dup " (with trailing space).
    The BINDING claim under the refutation clause is "Create SUCCEEDS
    despite a pre-existing collision, yielding two text objects" -- that
    is asserted below. The byte-identical-name sub-detail is measured and
    reported separately, plainly, not smoothed into the headline verdict.
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
    print(f"[VERDICT][PN8] Create({dup_name!r}) via public API -> exc={create_exc!r} (PREDICTED None/success)")

    if create_exc is not None:
        print(
            "[REFUTATION][PN8] MEASURED OPPOSITE TO PREDICTION -- Create() "
            "raised instead of succeeding, meaning the duplicate guard DID "
            "fire despite the padded haystack. This REFUTES the ruling's "
            "premise. Reported plainly, NOT reconciled."
        )
    assert create_exc is None, (
        f"PN8 MISS (BINDING): expected Texts.Create({dup_name!r}) to SUCCEED "
        f"(duplicate guard bypassed by the unstripped haystack) -- it raised "
        f"{create_exc!r} instead"
    )
    assert second_text is not None, "PN8: Create() returned no object despite no exception"

    second_raw = ITsString(second_text.Name.BestAnalysisAlternative).Text
    print(f"[TABLE][PN8] second (public-API) text stored Name: {second_raw!r}")

    # Count distinct IText objects a naive normalized-substring search would
    # consider "the Dup text", by re-reading from the LCM.
    dup_texts = []
    for t in project.Texts.GetAll():
        t_name = ITsString(t.Name.BestAnalysisAlternative).Text
        if t_name and t_name.strip() == dup_name.strip():
            dup_texts.append((str(t.Guid), t_name))
    print(f"[SUMMARY][PN8] texts whose stripped name matches {dup_name.strip()!r}: {dup_texts}")

    assert len(dup_texts) == 2, (
        f"PN8 MISS (BINDING): expected exactly TWO distinct IText objects "
        f"matching {dup_name.strip()!r} after the duplicate-explosion -- "
        f"found {len(dup_texts)}: {dup_texts}"
    )

    if second_raw == first_raw:
        print(
            "[VERDICT][PN8] sub-detail CONFIRMED: both texts' stored Name "
            "values are byte-identical."
        )
    else:
        print(
            f"[VERDICT][PN8] sub-detail MISS (non-binding, reported plainly): "
            f"the two texts' stored Name values are NOT byte-identical -- "
            f"first={first_raw!r} (raw bypass, trailing space preserved) vs "
            f"second={second_raw!r} (public-API Create(), which strips "
            f"BEFORE persisting at TextOperations.py:152, so its own "
            f"trailing space never reaches storage). The BINDING duplicate-"
            f"explosion claim (two objects, same effective identity to a "
            f"human) still holds regardless of this sub-detail."
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
