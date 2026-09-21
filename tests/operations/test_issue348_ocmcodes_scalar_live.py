#
#   test_issue348_ocmcodes_scalar_live.py
#
#   Live-LCM PROBE coverage for issue #348: ICmSemanticDomain.OcmCodes is
#   a scalar Unicode / System.String property (liblcm 11.0.0.0, confirmed
#   by the live-reflected contract snapshot at
#   tests/contract/snapshots/liblcm_baseline.json:7118-7122), NOT an
#   IMultiString. GetSyncableProperties, GetOcmCodes, and Duplicate() all
#   previously treated it as a MultiUnicode (get_String() /
#   CopyAlternatives()), which raised on every real domain regardless of
#   whether OcmCodes was unset (None, the common case -- the issue
#   measured 1792/1792 domains failing) or a populated string (still
#   raises: 'str' object has no attribute 'get_String').
#
#   This file is written but deliberately NOT executed as part of this
#   task (per task instructions). Run it against a live Target sandbox
#   with:
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest tests/operations/test_issue348_ocmcodes_scalar_live.py \
#           -m requires_live_project -q
#
#   tests/fixtures/ here has a Target .fwbackup and no Sena 3 backup, so
#   every test uses `target_sandbox` (function-scoped, tempdir copy,
#   nothing can leak into the real Target).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


class TestOcmCodesLiveType:
    """
    PROBE 1: confirm the ground-truth shape on a live, unpatched domain,
    and confirm the fixed GetSyncableProperties no longer raises across
    every domain in the sandbox project.
    """

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_ocm_codes_is_never_an_lcm_interface(self, target_sandbox):
        """
        type(domain.OcmCodes) must be NoneType or str for every domain --
        never an LCM interface object (which would indicate the pythonnet
        boundary is actually handing back a MultiUnicode wrapper and the
        #348 ruling is wrong).
        """
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert domains, (
            "Sandbox project has no semantic domains -- cannot probe "
            "OcmCodes type. Restore/seed the Target fixture with the "
            "standard SemDom catalog first."
        )

        for domain in domains:
            value = domain.OcmCodes
            assert value is None or isinstance(value, str), (
                f"domain {getattr(domain, 'Guid', '?')} has OcmCodes of "
                f"type {type(value).__name__}, expected NoneType or str. "
                "This contradicts the #348 ruling that OcmCodes is a "
                "scalar Unicode / System.String property."
            )

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_get_syncable_properties_never_raises_across_all_domains(
        self, target_sandbox
    ):
        """
        The reported bug: GetSyncableProperties raised on every domain
        whose OcmCodes was None (pre-fix: .get_String() called on a bare
        str/None). Confirm the fixed method returns props["OcmCodes"] ==
        "" for every unset domain, and a str for every domain overall,
        without raising. Report the pass count -- the issue measured
        1792/1792 domains failing pre-fix.
        """
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert domains, "Sandbox project has no semantic domains."

        total = len(domains)
        passed = 0
        failures = []

        for domain in domains:
            try:
                props = target_sandbox.SemanticDomains.GetSyncableProperties(
                    domain
                )
            except Exception as exc:
                failures.append((getattr(domain, "Guid", "?"), repr(exc)))
                continue

            if not isinstance(props.get("OcmCodes"), str):
                failures.append(
                    (
                        getattr(domain, "Guid", "?"),
                        f"OcmCodes was {props.get('OcmCodes')!r}, not a str",
                    )
                )
                continue

            passed += 1

        print(f"[issue #348] GetSyncableProperties: {passed}/{total} domains passed")

        assert not failures, (
            f"{len(failures)}/{total} domains failed GetSyncableProperties: "
            f"{failures[:5]}{'...' if len(failures) > 5 else ''}"
        )
        assert passed == total


class TestOcmCodesLivePopulate:
    """
    PROBE 2: populate one domain's OcmCodes by direct assignment (the
    Target sandbox's semantic domains are expected to be unset out of
    the box, so this is the only way to exercise a populated case --
    this is NOT pre-existing data), then confirm GetSyncableProperties
    and GetOcmCodes both read the real string back from the LCM.
    """

    @pytest.mark.live_phase("SemanticDomainOperations", "modify")
    def test_populate_then_read_back_via_get_syncable_properties(
        self, target_sandbox
    ):
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert domains, "Sandbox project has no semantic domains."

        domain = domains[0]
        test_value = f"{TEST_PREFIX}484"

        # Single scalar-property mutation -- no _TransactionCM wrapper
        # needed (BaseOperations convention: only 2+ mutation methods
        # need the transaction context manager).
        domain.OcmCodes = test_value

        # Read back from the LCM via the fixed accessor, not the value
        # just assigned.
        props = target_sandbox.SemanticDomains.GetSyncableProperties(domain)
        assert props["OcmCodes"] == test_value, (
            f"Expected {test_value!r} read back via GetSyncableProperties, "
            f"got {props['OcmCodes']!r}"
        )

    @pytest.mark.live_phase("SemanticDomainOperations", "modify")
    def test_populate_then_read_back_via_get_ocm_codes(self, target_sandbox):
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert domains, "Sandbox project has no semantic domains."

        domain = domains[0]
        test_value = f"{TEST_PREFIX}271"

        domain.OcmCodes = test_value

        result = target_sandbox.SemanticDomains.GetOcmCodes(domain)
        assert result == test_value, (
            f"Expected {test_value!r} read back via GetOcmCodes, "
            f"got {result!r}"
        )


class TestOcmCodesLiveDuplicate:
    """PROBE 3: Duplicate() on both an unset and a populated domain."""

    @pytest.mark.live_phase("SemanticDomainOperations", "modify")
    def test_duplicate_unset_domain_does_not_raise(self, target_sandbox):
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert domains, "Sandbox project has no semantic domains."

        # Find (or force) an unset domain; the pre-fix bug was that
        # CopyAlternatives(None) raised specifically on the unset case.
        source = None
        for candidate in domains:
            if candidate.OcmCodes is None:
                source = candidate
                break
        if source is None:
            source = domains[0]
            source.OcmCodes = None

        duplicate = target_sandbox.SemanticDomains.Duplicate(
            source, insert_after=False, deep=False
        )
        try:
            assert duplicate.OcmCodes in (None, ""), (
                f"Expected duplicate of an unset domain to carry an "
                f"empty/None OcmCodes, got {duplicate.OcmCodes!r}"
            )
        finally:
            target_sandbox.SemanticDomains.Delete(duplicate)

    @pytest.mark.live_phase("SemanticDomainOperations", "modify")
    def test_duplicate_populated_domain_copies_the_value(self, target_sandbox):
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert domains, "Sandbox project has no semantic domains."

        source = domains[0]
        test_value = f"{TEST_PREFIX}117"
        source.OcmCodes = test_value

        duplicate = target_sandbox.SemanticDomains.Duplicate(
            source, insert_after=False, deep=False
        )
        try:
            # Read back from the LCM, not the value just assigned to source.
            assert duplicate.OcmCodes == test_value, (
                f"Expected duplicate to carry {test_value!r}, got "
                f"{duplicate.OcmCodes!r}"
            )
        finally:
            target_sandbox.SemanticDomains.Delete(duplicate)


class TestOcmCodesLiveRoundTrip:
    """
    PROBE 4: GetSyncableProperties -> ApplySyncableProperties round-trip
    onto a second item, reading the post-state back from the LCM.
    """

    @pytest.mark.live_phase("SemanticDomainOperations", "modify")
    def test_apply_then_get_round_trip_on_a_second_item(self, target_sandbox):
        domains = list(target_sandbox.SemanticDomains.GetAll())
        assert len(domains) >= 2, (
            "Round-trip probe needs at least two distinct semantic "
            "domains in the sandbox project (a source and a target)."
        )

        source, target = domains[0], domains[1]
        test_value = f"{TEST_PREFIX}648"
        source.OcmCodes = test_value

        props = target_sandbox.SemanticDomains.GetSyncableProperties(source)
        assert props["OcmCodes"] == test_value

        target_sandbox.SemanticDomains.ApplySyncableProperties(target, props)

        # Re-query rather than trusting the dict we just applied.
        post_props = target_sandbox.SemanticDomains.GetSyncableProperties(
            target
        )
        assert post_props["OcmCodes"] == test_value, (
            f"Round-trip mismatch: applied {test_value!r} to target, "
            f"but re-reading target.OcmCodes from the LCM via "
            f"GetSyncableProperties gave {post_props['OcmCodes']!r}"
        )
        assert target.OcmCodes == test_value, (
            f"Round-trip mismatch reading the raw LCM attribute: "
            f"expected {test_value!r}, got {target.OcmCodes!r}"
        )
