"""Observed accelerator readiness report; never infer support from a product name."""

import importlib
import math
import platform
from importlib.metadata import PackageNotFoundError, version
from typing import Literal


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _small_matmul_smoke(torch, device: str, backend_module, index: int) -> dict:
    """Exercise actual device placement, BF16 matmul, sync, and CPU readback."""
    cpu = torch.arange(256, dtype=torch.float32).reshape(16, 16) / 100
    reference = float((cpu @ cpu.T).sum())
    observed = {}
    for dtype_name, tolerance in (("float32", 0.001), ("bfloat16", 0.03)):
        dtype = getattr(torch, dtype_name)
        try:
            tensor = cpu.to(device=device, dtype=dtype)
            result = tensor @ tensor.T
            backend_module.synchronize(index)
            value = float(result.float().sum().cpu())
            relative_error = abs(value - reference) / max(abs(reference), 1.0)
            if not math.isfinite(relative_error):
                raise ValueError("nonfinite matmul result")
            observed[dtype_name] = {
                "status": "PASS" if relative_error <= tolerance else "FAIL",
                "reference_sum": reference,
                "observed_sum": value,
                "relative_error": relative_error,
                "tolerance": tolerance,
            }
        except Exception as error:
            observed[dtype_name] = {
                "status": "FAIL",
                "error": f"{type(error).__name__}: {error}",
            }
    return observed


def preflight(
    backend: Literal["cuda", "hpu"],
    *,
    device_index: int = 0,
    smoke: bool = True,
    torch_module=None,
) -> dict:
    """Return measured local readiness only; unavailable devices never become simulated runs."""
    if backend not in ("cuda", "hpu"):
        raise ValueError("backend must be cuda or hpu")
    if device_index < 0:
        raise ValueError("device_index must be nonnegative")
    report = {
        "schema_version": 1,
        "kind": "accelerator_preflight",
        "backend": backend,
        "host": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "device_index": device_index,
        "status": "UNAVAILABLE",
        "claim_limit": (
            "Availability and tiny numerical placement smoke only. No training throughput, "
            "memory optimization, compile compatibility, or model quality is established."
        ),
    }
    try:
        torch = torch_module or importlib.import_module("torch")
    except ImportError as error:
        report["reason"] = f"PyTorch unavailable: {error}"
        return report
    report["torch_version"] = str(torch.__version__)
    if backend == "hpu":
        report["gaudi_plugin_version"] = _package_version("habana-torch-plugin")
    else:
        report["cuda_runtime_version"] = getattr(torch.version, "cuda", None)
    device_api = getattr(torch, backend, None)
    if device_api is None:
        report["reason"] = f"torch.{backend} namespace unavailable"
        return report
    try:
        available = bool(device_api.is_available())
        count = int(device_api.device_count()) if available else 0
        if not available or device_index >= count:
            report["reason"] = f"requested {backend}:{device_index} unavailable; detected {count}"
            return report
        device = {"index": device_index, "count": count}
        get_name = getattr(device_api, "get_device_name", None)
        if callable(get_name):
            device["name"] = str(get_name(device_index))
        if backend == "cuda":
            properties = device_api.get_device_properties(device_index)
            device["total_memory_bytes"] = int(properties.total_memory)
            device["compute_capability"] = [int(properties.major), int(properties.minor)]
        else:
            get_capability = getattr(device_api, "get_device_capability", None)
            if callable(get_capability):
                capability = get_capability(device_index)
                device["capability"] = [int(item) for item in capability]
        report["device"] = device
        if smoke:
            report["smoke"] = _small_matmul_smoke(
                torch, f"{backend}:{device_index}", device_api, device_index
            )
            report["status"] = (
                "READY"
                if all(item["status"] == "PASS" for item in report["smoke"].values())
                else "SMOKE_FAILED"
            )
        else:
            report["status"] = "DETECTED_UNTESTED"
    except Exception as error:
        report["status"] = "PROBE_FAILED"
        report["reason"] = f"{type(error).__name__}: {error}"
    return report
