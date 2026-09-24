#
#   test_issue294_pos_default_features.py
#
#   Offline source ratchets for issue #294: public accessors for
#   IPartOfSpeech.DefaultFeaturesOA / InherFeatValOA.
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
POS_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "POSOperations.py"


def _method_body(source: str, method_name: str) -> str:
    lines = source.splitlines()
    in_method = False
    body: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"def {method_name}("):
            in_method = True
            continue
        if in_method:
            if stripped.startswith("def ") and not stripped.startswith(f"def {method_name}("):
                break
            if stripped.startswith("@") and body:
                break
            body.append(line)
    return "\n".join(body)


class TestIssue294POSDefaultFeaturesSurface:
    def test_public_get_set_methods_exist(self):
        source = POS_OPS.read_text(encoding="utf-8")
        for name in (
            "GetDefaultFeatures",
            "SetDefaultFeatures",
            "GetInherFeatVal",
            "SetInherFeatVal",
        ):
            assert re.search(rf"def {name}\s*\(", source), f"missing {name}"

    def test_get_methods_use_resolve_and_read_helper(self):
        source = POS_OPS.read_text(encoding="utf-8")
        for method in ("GetDefaultFeatures", "GetInherFeatVal"):
            body = _method_body(source, method)
            assert "__ResolveObject" in body
            assert "__ReadPOSFeatureStrucSpec" in body
            assert "getattr" not in body
            assert "hasattr" not in body

    def test_set_methods_use_write_helper_and_transaction(self):
        source = POS_OPS.read_text(encoding="utf-8")
        for method in ("SetDefaultFeatures", "SetInherFeatVal"):
            body = _method_body(source, method)
            assert "_EnsureWriteEnabled" in body
            assert "_TransactionCM" in body
            assert "__WritePOSFeatureStrucSpec" in body

    def test_read_helper_delegates_to_c1_table(self):
        source = POS_OPS.read_text(encoding="utf-8")
        body = _method_body(source, "__ReadPOSFeatureStrucSpec")
        assert "_ResolveFeatureStrucOwner" in body
        assert "_GetFeatureStruc" in body
        assert "hasattr" not in body

    def test_write_helper_raises_on_bad_spec(self):
        source = POS_OPS.read_text(encoding="utf-8")
        body = _method_body(source, "__WritePOSFeatureStrucSpec")
        assert "_ApplyFeatureStruc" in body
        assert 'on_unresolved="raise"' in body
        assert "FP_ParameterError" in body
