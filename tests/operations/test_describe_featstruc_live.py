#
#   test_describe_featstruc_live.py
#
#   Live, READ-ONLY verification for issue #557:
#   InflectionFeatureOperations.DescribeFeatStruc against real Sena 3
#   MSAs that carry feature structures.
#
#   No writes. Runs on sena3_sandbox (a fresh tempdir copy of the Sena 3
#   .fwbackup) so the real project is never opened for writing and a
#   locked FieldWorks cannot interfere.
#
#   For every MSA feature structure in the project, the expected string
#   is built by an independent oracle that walks IFsFeatStruc.FeatureSpecsOC
#   directly and reads each feature/value's Abbreviation -- it never goes
#   through the GUID spec. DescribeFeatStruc is then called three ways
#   (on the #544 getter's GUID spec, on the owning MSA, and on the
#   IFsFeatStruc itself) and must match the oracle each time.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

# (MSA ClassName, owning property, slot for DescribeFeatStruc / GetFeatures)
_MSA_SLOTS = (
    ("MoStemMsa", "MsFeaturesOA", None),
    ("MoInflAffMsa", "InflFeatsOA", None),
    ("MoDerivAffMsa", "FromMsFeaturesOA", "From"),
    ("MoDerivAffMsa", "ToMsFeaturesOA", "To"),
)


def _label(obj):
    from flexicon.code.Shared.string_utils import best_analysis_text

    return best_analysis_text(obj.Abbreviation) or best_analysis_text(obj.Name)


def _oracle(struct):
    """Render an IFsFeatStruc straight from the LCM, no GUID round-trip."""
    from SIL.LCModel import (
        IFsClosedValue,
        IFsComplexValue,
        IFsFeatDefn,
        IFsFeatStruc,
        IFsSymFeatVal,
    )

    parts = []
    for spec in IFsFeatStruc(struct).FeatureSpecsOC:
        if spec.ClassName == "FsClosedValue":
            cv = IFsClosedValue(spec)
            if cv.FeatureRA is None or cv.ValueRA is None:
                continue
            rendered = _label(IFsSymFeatVal(cv.ValueRA))
            feat = cv.FeatureRA
        elif spec.ClassName == "FsComplexValue":
            xv = IFsComplexValue(spec)
            if xv.FeatureRA is None or xv.ValueOA is None:
                continue
            rendered = _oracle(xv.ValueOA)
            feat = xv.FeatureRA
        else:
            continue
        parts.append(f"{_label(IFsFeatDefn(feat))}: {rendered}")
    return "[" + "; ".join(parts) + "]"


class TestDescribeFeatStrucRealSena3Live:
    @pytest.mark.live_phase("InflectionFeatureOperations", "read")
    def test_describe_matches_lcm_oracle_for_real_msa_features(
        self, sena3_sandbox
    ):
        import SIL.LCModel as lcm
        from SIL.LCModel import IMoMorphSynAnalysisRepository

        project = sena3_sandbox
        describe = project.InflectionFeatures.DescribeFeatStruc

        checked = []
        for raw in project.ObjectsIn(IMoMorphSynAnalysisRepository):
            for class_name, prop, slot in _MSA_SLOTS:
                if raw.ClassName != class_name:
                    continue
                msa = getattr(lcm, "I" + class_name)(raw)
                struct = getattr(msa, prop)
                if struct is None or struct.FeatureSpecsOC.Count == 0:
                    continue

                expected = _oracle(struct)
                spec = project.MSA.GetFeatures(msa, slot=slot)
                via_spec = describe(spec)
                via_owner = describe(msa, slot=slot)
                via_struct = describe(struct)

                assert via_spec == expected, (msa.Hvo, prop, spec, via_spec, expected)
                assert via_owner == expected, (msa.Hvo, prop, via_owner, expected)
                assert via_struct == expected, (msa.Hvo, prop, via_struct, expected)
                # Labels must be human-readable, never a leaked GUID.
                for guid in _all_guids(spec):
                    assert guid not in via_spec, (msa.Hvo, prop, via_spec)
                checked.append((int(msa.Hvo), prop, via_spec))

        print(f"\n[INFO] {len(checked)} real MSA feature structures described")
        for hvo, prop, text in checked[:15]:
            print(f"  hvo={hvo} {prop}: {text}")

        assert len(checked) >= 3, (
            f"Expected at least 3 Sena 3 MSA feature structures to check; "
            f"found {len(checked)}."
        )

    @pytest.mark.live_phase("InflectionFeatureOperations", "read")
    def test_msa_without_features_describes_as_empty_string(self, sena3_sandbox):
        from SIL.LCModel import IMoMorphSynAnalysisRepository, IMoStemMsa

        project = sena3_sandbox
        for raw in project.ObjectsIn(IMoMorphSynAnalysisRepository):
            if raw.ClassName == "MoStemMsa" and IMoStemMsa(raw).MsFeaturesOA is None:
                assert project.MSA.GetStemFeatures(raw) is None
                assert project.InflectionFeatures.DescribeFeatStruc(raw) == ""
                assert project.InflectionFeatures.DescribeFeatStruc(None) == ""
                return
        pytest.fail("Sena 3 has no stem MSA with a null MsFeaturesOA to check.")


def _all_guids(spec):
    for key, value in spec.items():
        yield key
        if isinstance(value, dict):
            yield from _all_guids(value)
        else:
            yield value
