#
#   test_issue470_reorder_clear_offline.py
#
#   Offline coverage for issue #470: Reorder() must not Clear() owning
#   sequences (Clear deletes children). Uses MoveTo via _ApplySequenceOrder.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

import ast
from pathlib import Path

import pytest


def _apply_sequence_order(sequence, desired_order):
    """Mirror of BaseOperations._ApplySequenceOrder (no flexicon import)."""

    class FP_ParameterError(Exception):
        pass

    count = sequence.Count
    if len(desired_order) != count:
        raise FP_ParameterError("length mismatch")

    current = [sequence[i] for i in range(count)]
    if set(current) != set(desired_order):
        raise FP_ParameterError("membership mismatch")

    for target_index in range(count):
        current_index = target_index
        target_item = desired_order[target_index]
        for j in range(target_index, count):
            if sequence[j] == target_item:
                current_index = j
                break

        if current_index != target_index:
            sequence.MoveTo(
                current_index, current_index, sequence, target_index
            )


class _MockSequence:
    """Owning-sequence stand-in: Clear() marks destructive delete."""

    def __init__(self, items):
        self._items = list(items)
        self.clear_called = False
        self.move_calls = []

    @property
    def Count(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def Clear(self):
        self.clear_called = True
        self._items = []

    def MoveTo(self, from_idx, from_idx2, seq, to_idx):
        self.move_calls.append((from_idx, to_idx))
        item = self._items.pop(from_idx)
        self._items.insert(to_idx, item)


class TestApplySequenceOrderAlgorithm:
    def test_reorders_without_clear(self):
        a, b, c = object(), object(), object()
        seq = _MockSequence([a, b, c])
        _apply_sequence_order(seq, [c, a, b])
        assert seq.clear_called is False
        assert list(seq._items) == [c, a, b]
        assert len(seq.move_calls) >= 1


_REORDER_FILES = (
    "flexicon/code/Lexicon/LexSenseOperations.py",
    "flexicon/code/Lexicon/ExampleOperations.py",
    "flexicon/code/Lexicon/EtymologyOperations.py",
    "flexicon/code/Lexicon/PronunciationOperations.py",
    "flexicon/code/TextsWords/WfiMorphBundleOperations.py",
)


def _reorder_function_nodes(source_path: Path):
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "Reorder":
            yield node


class TestReorderClearRatchet:
    @pytest.mark.parametrize("rel_path", _REORDER_FILES)
    def test_reorder_does_not_call_clear(self, rel_path):
        root = Path(__file__).resolve().parents[2]
        path = root / rel_path
        for func in _reorder_function_nodes(path):
            for sub in ast.walk(func):
                if isinstance(sub, ast.Call):
                    func_node = sub.func
                    if isinstance(func_node, ast.Attribute) and func_node.attr == "Clear":
                        pytest.fail(
                            f"{rel_path}: Reorder() must not call Clear() (issue #470)"
                        )

    @pytest.mark.parametrize("rel_path", _REORDER_FILES)
    def test_reorder_calls_apply_sequence_order(self, rel_path):
        root = Path(__file__).resolve().parents[2]
        source = (root / rel_path).read_text(encoding="utf-8")
        assert "_ApplySequenceOrder" in source, (
            f"{rel_path}: Reorder() should delegate to _ApplySequenceOrder"
        )


def test_apply_sequence_order_helper_has_no_clear():
    root = Path(__file__).resolve().parents[2]
    source = (root / "flexicon/code/BaseOperations.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_ApplySequenceOrder":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    fn = sub.func
                    if isinstance(fn, ast.Attribute) and fn.attr == "Clear":
                        pytest.fail("_ApplySequenceOrder must not call Clear()")
            return
    pytest.fail("_ApplySequenceOrder not found in BaseOperations.py")
