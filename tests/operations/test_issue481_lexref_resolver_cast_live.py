#
#   test_issue481_lexref_resolver_cast_live.py
#
#   Live gate for issue #481 LexReferenceOperations HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


@pytest.mark.requires_live_project
class TestIssue481LexRefTypeMappingHvoGate:
    """
    GetMappingType resolves the ref type via __ResolveRefType and reads
    MappingType -- subtype-only on ILexRefType.
    """

    @pytest.mark.live_phase("LexReferenceOperations", "read")
    def test_get_mapping_type_via_genuine_ref_type_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        ref_types = list(sandbox.LexReferences.GetAllTypes())
        if not ref_types:
            pytest.skip("No LexRefType instances in Sena 3 sandbox")
        ref_type = ref_types[0]
        hvo = ref_type.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        bare = sandbox.Object(hvo)
        assert not hasattr(bare, "MappingType"), (
            "precondition failed: MappingType reachable on bare ICmObject view "
            "-- re-derive the gate site"
        )

        mapping = sandbox.LexReferences.GetMappingType(hvo)
        assert mapping in (
            "Symmetric",
            "Asymmetric",
            "Tree",
            "Sequence",
            "Unknown",
        )
