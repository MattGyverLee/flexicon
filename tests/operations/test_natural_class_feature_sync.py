#
#   test_natural_class_feature_sync.py
#
#   Class: TestNaturalClassSyncStatic
#          Static source-pattern locks for the FeaturesOA cross-project
#          sync fix in NaturalClassOperations (the natural-class sibling
#          of PhonemeOperations issue #222). Mirrors
#          TestSyncTypeCorrectionsStatic in test_apply_syncable_properties.py:
#          these tests import the real module and inspect method source via
#          `inspect.getsource`, but never open a FieldWorks project, so they
#          run on any machine with FieldWorks/SIL.LCModel installed
#          (no `requires_live_project` marker, no live .fwdata needed).
#
#   Context: NaturalClassOperations.GetSyncableProperties previously
#   returned only Name/Abbreviation/Description/PhonemeGuids for every
#   natural class -- for a feature-based IPhNCFeatures item, its owned
#   FeaturesOA (the whole point of the object) was never captured, and
#   ApplySyncableProperties purely delegated to BaseOperations with no
#   Features handling whatsoever. Every feature-based natural class
#   therefore synced across with a correct Name/GUID but a null
#   FeaturesOA -- rules referencing the class silently matched nothing.
#   These tests lock:
#     (1) GetSyncableProperties surfaces FeaturesGuid + Features for
#         IPhNCFeatures, via FeatureSpecsOC (not just the old four keys).
#     (2) ApplySyncableProperties/​__ApplyFeatures RAISE (FP_ParameterError)
#         on an unresolved feature/value GUID rather than silently
#         `continue`-ing past it (which is the exact silence being fixed).
#     (3) The segment-based (PhonemeGuids) path is untouched.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect

import pytest


@pytest.fixture(autouse=True)
def _require_lcmodel():
    """
    NaturalClassOperations has module-level `from SIL.LCModel import ...`
    statements. On a machine without FieldWorks installed, that import
    ERRORs rather than skipping cleanly -- so skip explicitly instead.
    Importing the module (and even calling FLExInitialize elsewhere) does
    NOT open any .fwdata project; these tests never touch a live project.
    """
    pytest.importorskip("SIL.LCModel")


def _method_source(method_name):
    from flexicon.code.Grammar.NaturalClassOperations import (
        NaturalClassOperations,
    )

    obj = NaturalClassOperations.__dict__[method_name]

    seen = set()
    while True:
        oid = id(obj)
        if oid in seen:
            break
        seen.add(oid)
        if hasattr(obj, "func") and not inspect.isfunction(obj):
            obj = obj.func
            continue
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        break

    return inspect.getsource(obj)


class TestNaturalClassSyncStatic:
    """Locks the shape of the FeaturesOA sync fix without a live project."""

    def test_getsyncable_properties_emits_features_guid_and_specs(self):
        src = _method_source("GetSyncableProperties")

        assert 'props["FeaturesGuid"] = str(features.Guid)' in src, (
            "GetSyncableProperties must capture the owned IFsFeatStruc's "
            "GUID under 'FeaturesGuid' for feature-based (IPhNCFeatures) "
            "natural classes, mirroring PhonemeOperations issue #222."
        )
        assert '"FeatureGuid"' in src and '"ValueGuid"' in src, (
            "GetSyncableProperties must emit {'FeatureGuid', 'ValueGuid'} "
            "spec dicts -- without this, a synced feature-based natural "
            "class carries no feature-value constraints at all."
        )
        assert "FeatureSpecsOC" in src, (
            "GetSyncableProperties must walk FeaturesOA.FeatureSpecsOC to "
            "build the Features list."
        )

    def test_getsyncable_properties_still_emits_phoneme_guids(self):
        """
        The PhNCSegments / PhonemeGuids path must be untouched by the
        FeaturesOA fix -- segment-based classes already synced correctly.
        """
        src = _method_source("GetSyncableProperties")
        assert '"PhonemeGuids"' in src
        assert "SegmentsRC" in src

    def test_apply_syncable_properties_delegates_features_to_helper(self):
        src = _method_source("ApplySyncableProperties")
        assert "__ApplyFeatures" in src, (
            "ApplySyncableProperties must no longer be a pure "
            "super().ApplySyncableProperties(...) delegation -- it must "
            "dispatch Features/FeaturesGuid to a dedicated handler, the "
            "same shape as PhonemeOperations.ApplySyncableProperties."
        )

    def test_apply_features_raises_on_unresolved_feature_guid(self):
        """
        Pins the core behavioral requirement: an unresolved feature GUID
        must raise FP_ParameterError, not `continue`/`pass` past it. This
        is the opposite of PhonemeOperations.__ApplyFeatures, which skips
        silently -- silence is exactly the natural-class bug being fixed,
        so the two must NOT share that behavior.
        """
        src = _method_source("_NaturalClassOperations__ApplyFeatures")

        assert "raise FP_ParameterError" in src, (
            "__ApplyFeatures must raise FP_ParameterError when a feature "
            "or value GUID does not resolve in the target project."
        )
        assert "feat_obj is None" in src and "raise" in src, (
            "A None feat_obj (unresolved FeatureGuid) must be checked "
            "and raised on, not silently skipped."
        )
        assert "val_obj is None" in src, (
            "A None val_obj (unresolved ValueGuid) must be checked and "
            "raised on, not silently skipped."
        )

        # Negative check: guard against reintroducing the phoneme-style
        # silent-skip idiom for the "not found" branches specifically.
        # (A bare `continue` still legitimately appears for the
        # already-applied/idempotency branch a few lines earlier -- this
        # only pins that the *unresolved-GUID* branches raise.)
        unresolved_section = src[src.index("feat_obj = self.__ResolveByGuid") :]
        assert "continue" not in unresolved_section.split("val_obj = self.__ResolveByGuid")[0], (
            "The unresolved-FeatureGuid branch must raise, not `continue`."
        )

    def test_apply_features_error_message_names_guid_and_class(self):
        src = _method_source("_NaturalClassOperations__ApplyFeatures")
        assert "{feat_guid}" in src or "feat_guid}" in src, (
            "The raised exception message must name the missing "
            "FeatureGuid so the failure is actionable."
        )
        assert "{nc_name}" in src or "nc_name}" in src, (
            "The raised exception message must name the natural class "
            "so the failure is actionable."
        )

    def test_apply_syncable_properties_raises_on_type_mismatch(self):
        src = _method_source("ApplySyncableProperties")
        assert "not hasattr(nc, \"FeaturesOA\")" in src, (
            "ApplySyncableProperties must detect a Features/segments "
            "type mismatch (source carries Features, target item isn't "
            "feature-based) and raise rather than silently drop the data."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
