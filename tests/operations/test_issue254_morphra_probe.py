#
#   test_issue254_morphra_probe.py part1
#
import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


@pytest.mark.live_phase("WfiMorphBundleOperations", "read")
def test_probe_morphra_actual_type_and_failure_modes(sena3_sandbox, capsys):
    from SIL.LCModel import (
        IMoForm,
        IMoStemAllomorph,
        IMoAffixAllomorph,
        ICmPossibility,
        IWfiWordformRepository,
    )
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    project = sena3_sandbox
    anal_ws = project.project.DefaultAnalWs

    wordforms = list(project.ObjectsIn(IWfiWordformRepository))
    print(f"[PROBE] total wordforms in Sena 3 sandbox: {len(wordforms)}")

    sampled = 0
    none_morphra = 0
    class_name_counts = {}
    type_name_counts = {}
    stem_example = None
    prefix_example = None
    suffix_example = None
    cmpossibility_error_text = None

    for wf in wordforms:
        for analysis in wf.AnalysesOC:
            for bundle in analysis.MorphBundlesOS:
                sampled += 1
                morph_ra = bundle.MorphRA
                if morph_ra is None:
                    none_morphra += 1
                    continue

                cn = morph_ra.ClassName
                class_name_counts[cn] = class_name_counts.get(cn, 0) + 1

                try:
                    moform = IMoForm(morph_ra)
                    morph_type = moform.MorphTypeRA
                    type_name = (
                        morph_type.Name.BestAnalysisAlternative.Text
                        if morph_type is not None else None
                    )
                except Exception as exc:
                    type_name = "EXC:" + str(exc)

                key = (cn, type_name)
                type_name_counts[key] = type_name_counts.get(key, 0) + 1

                if type_name:
                    low = str(type_name).lower()
                    if cn == "MoStemAllomorph" and stem_example is None:
                        stem_example = (cn, type_name)
                    if cn == "MoAffixAllomorph" and "prefix" in low and prefix_example is None:
                        prefix_example = (cn, type_name)
                    if cn == "MoAffixAllomorph" and "suffix" in low and suffix_example is None:
                        suffix_example = (cn, type_name)

                if cmpossibility_error_text is None:
                    try:
                        _ = ICmPossibility(morph_ra).Name
                        cmpossibility_error_text = "NO ERROR RAISED"
                    except Exception as exc:
                        cmpossibility_error_text = type(exc).__name__ + ": " + str(exc)

                if sampled >= 3000:
                    break
            if sampled >= 3000:
                break
        if sampled >= 3000:
            break

    print(f"[PROBE] sampled bundles: {sampled}")
    print(f"[PROBE] bundles with MorphRA=None: {none_morphra}")
    print(f"[PROBE] MorphRA ClassName distribution: {class_name_counts}")
    print(f"[PROBE] (ClassName, MorphType.Name) distribution: {type_name_counts}")
    print(f"[PROBE] stem example (ClassName, MorphType.Name): {stem_example}")
    print(f"[PROBE] prefix example (ClassName, MorphType.Name): {prefix_example}")
    print(f"[PROBE] suffix example (ClassName, MorphType.Name): {suffix_example}")
    print(f"[PROBE] ICmPossibility(bundle.MorphRA).Name result: {cmpossibility_error_text}")

    assert sampled > 0, "No morph bundles found in Sena 3 sandbox -- cannot probe live data"

    for cn in class_name_counts:
        assert cn in ("MoStemAllomorph", "MoAffixAllomorph"), (
            "Unexpected MorphRA ClassName observed live: " + cn
        )


@pytest.mark.live_phase("WfiMorphBundleOperations", "modify")
def test_probe_setmorphtype_writes_wrong_reference_type(sena3_sandbox):
    from SIL.LCModel import (
        IMoForm,
        IWfiWordformRepository,
    )

    project = sena3_sandbox
    ops = project.WfiMorphBundles

    wordforms = list(project.ObjectsIn(IWfiWordformRepository))
    target_bundle = None
    for wf in wordforms:
        for analysis in wf.AnalysesOC:
            for bundle in analysis.MorphBundlesOS:
                if bundle.MorphRA is not None:
                    target_bundle = bundle
                    break
            if target_bundle is not None:
                break
        if target_bundle is not None:
            break

    assert target_bundle is not None, "No bundle with a set MorphRA found to probe"

    pre_morph_ra = target_bundle.MorphRA
    pre_class_name = pre_morph_ra.ClassName
    print(f"[PROBE] pre-state bundle.MorphRA ClassName: {pre_class_name}")

    morph_types = list(project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS)
    assert morph_types, "No IMoMorphType possibilities found in Sena 3 sandbox"
    bogus_morph_type = morph_types[0]
    print(f"[PROBE] IMoMorphType to assign: ClassName={bogus_morph_type.ClassName}, Name={bogus_morph_type.Name.BestAnalysisAlternative.Text}")

    raised = None
    try:
        ops.SetMorphType(target_bundle, bogus_morph_type)
    except Exception as exc:
        raised = type(exc).__name__ + ": " + str(exc)

    print(f"[PROBE] SetMorphType(bundle, IMoMorphType) raised: {raised}")

    if raised is None:
        post_morph_ra = target_bundle.MorphRA
        post_class_name = post_morph_ra.ClassName if post_morph_ra is not None else None
        print(f"[PROBE] post-state bundle.MorphRA ClassName (re-read from LCM): {post_class_name}")

        get_morph_type_result = ops.GetMorphType(target_bundle)
        gmt_cn = get_morph_type_result.ClassName if get_morph_type_result is not None else None
        print(f"[PROBE] GetMorphType() after corruption returns ClassName: {gmt_cn}")

        syncable_error = None
        syncable_props = None
        try:
            syncable_props = ops.GetSyncableProperties(target_bundle)
        except Exception as exc:
            syncable_error = type(exc).__name__ + ": " + str(exc)
        print(f"[PROBE] GetSyncableProperties() after corruption: props={syncable_props} error={syncable_error}")

        duplicate_error = None
        try:
            dup = ops.Duplicate(target_bundle, insert_after=True)
            dup_cn = dup.MorphRA.ClassName if dup.MorphRA else None
            print(f"[PROBE] Duplicate() after corruption succeeded, dup.MorphRA ClassName={dup_cn}")
        except Exception as exc:
            duplicate_error = type(exc).__name__ + ": " + str(exc)
            print(f"[PROBE] Duplicate() after corruption raised: {duplicate_error}")

        cast_error = None
        try:
            _ = IMoForm(post_morph_ra)
        except Exception as exc:
            cast_error = type(exc).__name__ + ": " + str(exc)
        print(f"[PROBE] IMoForm(corrupted MorphRA) raised: {cast_error}")

        assert post_class_name != pre_class_name, (
            "Expected the corrupted MorphRA to now report the IMoMorphType ClassName, "
            "not the original allomorph's ClassName"
        )
    else:
        print("[PROBE] Setter raised -- this is a CRASH, not silent corruption.")

    assert True
