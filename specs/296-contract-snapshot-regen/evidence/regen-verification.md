# Regen Verification -- #296

## Command

```
python tests/contract/extract_lcm_contract.py -o tests/contract/snapshots/expected_contract.json
```

## Determinism

Re-ran the extractor twice into scratch output files (not overwriting the
tracked snapshot) and hashed both:

```
dc5f2cb1cc20d1feb12b3c7d9188135b30752abd682038d686411b7b66a4df1e  regen1.json
dc5f2cb1cc20d1feb12b3c7d9188135b30752abd682038d686411b7b66a4df1e  regen2.json
```

Byte-identical across two independent runs. This matches the hash of the
already-regenerated (uncommitted) working-tree copy of
`tests/contract/snapshots/expected_contract.json`:

```
sha256sum tests/contract/snapshots/expected_contract.json
dc5f2cb1cc20d1feb12b3c7d9188135b30752abd682038d686411b7b66a4df1e
```

No drift from the value recorded before this session started, and
`tests/contract/pending_contract_seeds.py` shows no uncommitted changes
(`git status --porcelain` empty), so the second extractor input is also
unchanged.

## Gate

```
python -m pytest tests/contract/test_lcm_contract.py -m "not requires_liblcm" -q
```

Result: 22 passed.

## Live LCM verification

Not applicable. This is a pure test-baseline (contract snapshot)
regeneration produced by a static-analysis extractor script; it makes no
Operations/factory/property-setter/write-path edit, so the CLAUDE.md
live-LCM verification requirement does not apply.
