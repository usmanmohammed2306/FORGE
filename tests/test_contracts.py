import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from forge.canonical import CanonicalizationError, canonical_bytes, digest
from forge.contracts import Experiment


def test_digest_ignores_object_key_order_but_not_list_order():
    left = {"model": {"id": "m", "revision": "r"}, "lengths": [64, 128]}
    right = {"lengths": [64, 128], "model": {"revision": "r", "id": "m"}}
    assert digest(left, domain="config") == digest(right, domain="config")
    assert digest(left, domain="config") != digest(left, domain="artifact")
    assert digest(left, domain="config") != digest({**left, "lengths": [128, 64]}, domain="config")


def test_nonfinite_float_and_nonstr_key_rejected():
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"x": float("nan")})
    with pytest.raises(CanonicalizationError):
        canonical_bytes({1: "value"})


def test_experiment_rejects_unknown_and_invalid_shape():
    valid = json.loads(Path("configs/l0_packing.json").read_text(encoding="utf-8"))
    valid["extra"] = "silent typo"
    with pytest.raises(ValidationError):
        Experiment.model_validate(valid)
    valid.pop("extra")
    valid["workload"]["sequence_lengths"] = [1, 9999]
    with pytest.raises(ValidationError):
        Experiment.model_validate(valid)
