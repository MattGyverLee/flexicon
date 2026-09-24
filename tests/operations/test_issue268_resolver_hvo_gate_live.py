#
#   test_issue268_resolver_hvo_gate_live.py
#
#   Issue #268 narrow slice: HVO-entry live gates at two read-only public
#   methods that previously had no automated coverage --
#   POSOperations.GetCatalogSourceId and AllomorphOperations.GetPhoneEnv.
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
