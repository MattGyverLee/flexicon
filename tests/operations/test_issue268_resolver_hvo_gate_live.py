#
#   test_issue268_resolver_hvo_gate_live.py
#
#   Issue #268 narrow slices: HVO-entry live gates at read-only public
#   methods that previously had no automated coverage. Slice 1:
#   GetCatalogSourceId, GetPhoneEnv. Slice 2 (cron): GetInflectionClasses,
#   GetAffixSlots, GetFormAudio.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_268_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


@pytest.mark.requires_live_project
class TestIssue268PosGetCatalogSourceIdHvoGate:
    """
    GetCatalogSourceId (:754) is one of the seven POS __ResolveObject call
    sites with no prior automated coverage. It reads CatalogSourceId, a
    subtype-only IPartOfSpeech member.
    """

    @pytest.mark.live_phase("POSOperations", "read")
    def test_get_catalog_source_id_via_genuine_hvo_int(self, target_sandbox):
        sandbox = target_sandbox
        pos_obj = sandbox.POS.Create(f"{TEST_PREFIX}pos_cat", "t268c")
        try:
            hvo = pos_obj.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "CatalogSourceId"), (
                "precondition failed: CatalogSourceId reachable on bare "
                "ICmObject view -- re-derive the gate site"
            )

            catalog_id = sandbox.POS.GetCatalogSourceId(hvo)
            assert catalog_id == "" or isinstance(catalog_id, str)
        finally:
            sandbox.POS.Delete(pos_obj)


@pytest.mark.requires_live_project
class TestIssue268AllomorphGetPhoneEnvHvoGate:
    """
    GetPhoneEnv (:1174) is one of the seven AllomorphOperations
    __GetAllomorphObject call sites with no prior automated coverage.
    It reads PhoneEnvRC, subtype-only on MoAffixAllomorph.
    """

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_get_phone_env_via_genuine_hvo_int(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "allo_env")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}env", morphType="suffix"
            )
            hvo = allo.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "PhoneEnvRC"), (
                "precondition failed: PhoneEnvRC reachable on bare ICmObject "
                "view -- re-derive the gate site"
            )

            envs = sandbox.Allomorphs.GetPhoneEnv(hvo)
            assert isinstance(envs, list)
            assert envs == []
        finally:
            sandbox.LexEntry.Delete(entry)


@pytest.mark.requires_live_project
class TestIssue268PosGetInflectionClassesHvoGate:
    """
    GetInflectionClasses is one of the POS __ResolveObject call sites with
    no prior automated coverage. It reads InflectionClassesOC.
    """

    @pytest.mark.live_phase("POSOperations", "read")
    def test_get_inflection_classes_via_genuine_hvo_int(self, target_sandbox):
        sandbox = target_sandbox
        pos_obj = sandbox.POS.Create(f"{TEST_PREFIX}pos_infl", "t268i")
        try:
            hvo = pos_obj.Hvo
            assert isinstance(hvo, int)
            assert not hasattr(sandbox.Object(hvo), "InflectionClassesOC"), (
                "precondition failed: InflectionClassesOC reachable on bare "
                "ICmObject view -- re-derive the gate site"
            )

            classes = sandbox.POS.GetInflectionClasses(hvo)
            assert isinstance(classes, list)
            assert classes == []
        finally:
            sandbox.POS.Delete(pos_obj)


@pytest.mark.requires_live_project
class TestIssue268PosGetAffixSlotsHvoGate:
    """
    GetAffixSlots is one of the POS __ResolveObject call sites with no prior
    automated coverage. It reads AffixSlotsOC.
    """

    @pytest.mark.live_phase("POSOperations", "read")
    def test_get_affix_slots_via_genuine_hvo_int(self, target_sandbox):
        sandbox = target_sandbox
        pos_obj = sandbox.POS.Create(f"{TEST_PREFIX}pos_slot", "t268s")
        try:
            hvo = pos_obj.Hvo
            assert isinstance(hvo, int)
            assert not hasattr(sandbox.Object(hvo), "AffixSlotsOC"), (
                "precondition failed: AffixSlotsOC reachable on bare "
                "ICmObject view -- re-derive the gate site"
            )

            slots = sandbox.POS.GetAffixSlots(hvo)
            assert isinstance(slots, list)
            assert slots == []
        finally:
            sandbox.POS.Delete(pos_obj)


@pytest.mark.requires_live_project
class TestIssue268AllomorphGetFormAudioHvoGate:
    """
    GetFormAudio is one of the AllomorphOperations __GetAllomorphObject call
    sites with no prior automated coverage. It reads Form for audio paths.
    """

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_get_form_audio_via_genuine_hvo_int(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "allo_audio")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}aud", morphType="suffix"
            )
            hvo = allo.Hvo
            assert isinstance(hvo, int)
            assert not hasattr(sandbox.Object(hvo), "Form"), (
                "precondition failed: Form reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            audio_path = sandbox.Allomorphs.GetFormAudio(hvo)
            assert audio_path is None or isinstance(audio_path, str)
        finally:
            sandbox.LexEntry.Delete(entry)
