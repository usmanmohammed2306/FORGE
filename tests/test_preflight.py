import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.cli import app
from forge.preflight import _small_matmul_smoke, preflight


class FakeCuda:
    def is_available(self):
        return True

    def device_count(self):
        return 1

    def get_device_name(self, index):
        return "Test CUDA device"

    def get_device_properties(self, index):
        return SimpleNamespace(total_memory=40_000_000_000, major=8, minor=0)


def fake_torch(cuda):
    return SimpleNamespace(
        __version__="test-torch", version=SimpleNamespace(cuda="test"), cuda=cuda
    )


def test_preflight_refuses_missing_or_wrong_device_without_claiming_readiness():
    absent = SimpleNamespace(is_available=lambda: False, device_count=lambda: 0)
    report = preflight("cuda", torch_module=fake_torch(absent))
    assert report["status"] == "UNAVAILABLE"
    assert "detected 0" in report["reason"]
    wrong_index = preflight("cuda", torch_module=fake_torch(FakeCuda()), device_index=1)
    assert wrong_index["status"] == "UNAVAILABLE"
    with pytest.raises(ValueError, match="backend"):
        preflight("cpu")
    with pytest.raises(ValueError, match="nonnegative"):
        preflight("cuda", device_index=-1)


def test_inventory_without_smoke_is_not_ready():
    report = preflight("cuda", torch_module=fake_torch(FakeCuda()), smoke=False)
    assert report["status"] == "DETECTED_UNTESTED"
    assert report["device"]["name"] == "Test CUDA device"
    assert report["device"]["total_memory_bytes"] == 40_000_000_000


def test_failed_numerical_smoke_cannot_pass(monkeypatch):
    monkeypatch.setattr(
        "forge.preflight._small_matmul_smoke",
        lambda *args: {"float32": {"status": "PASS"}, "bfloat16": {"status": "FAIL"}},
    )
    report = preflight("cuda", torch_module=fake_torch(FakeCuda()))
    assert report["status"] == "SMOKE_FAILED"


def test_cpu_math_core_exercises_both_dtypes_without_accelerator_claim():
    torch = pytest.importorskip("torch")
    sync = SimpleNamespace(synchronize=lambda index: None)
    observed = _small_matmul_smoke(torch, "cpu", sync, 0)
    assert observed["float32"]["status"] == "PASS"
    assert observed["bfloat16"]["status"] == "PASS"


def test_cli_saves_unavailable_report_and_exits_nonzero(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "forge.cli.preflight",
        lambda *args, **kwargs: {"schema_version": 1, "status": "UNAVAILABLE", "backend": "hpu"},
    )
    result = CliRunner().invoke(
        app, ["accelerator", "preflight", "hpu", "--workspace", str(tmp_path)]
    )
    assert result.exit_code == 1
    output = json.loads(result.stdout)
    stored = ArtifactStore(tmp_path / ".forge" / "artifacts").get(output["report_ref"])
    assert json.loads(stored)["status"] == "UNAVAILABLE"
