"""Truthful local accelerator inventory with optional backend imports."""

import importlib
import platform


def probe() -> dict:
    inventory: dict = {
        "host": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "torch": {"available": False},
        "cuda": {"available": False, "devices": []},
        "hpu": {"available": False, "devices": []},
    }
    try:
        torch = importlib.import_module("torch")
    except ImportError as error:
        inventory["torch"]["reason"] = f"PyTorch is not installed: {error.name}"
        return inventory
    inventory["torch"] = {"available": True, "version": torch.__version__}
    try:
        cuda = getattr(torch, "cuda", None)
        if cuda is not None and cuda.is_available():
            inventory["cuda"] = {
                "available": True,
                "devices": [
                    {
                        "index": index,
                        "name": cuda.get_device_name(index),
                        "total_memory_bytes": cuda.get_device_properties(index).total_memory,
                    }
                    for index in range(cuda.device_count())
                ],
            }
    except Exception as error:
        inventory["cuda"]["probe_error"] = f"{type(error).__name__}: {error}"
    try:
        hpu = getattr(torch, "hpu", None)
        if hpu is None:
            inventory["hpu"]["reason"] = "PyTorch has no HPU namespace"
        elif hpu.is_available():
            inventory["hpu"] = {
                "available": True,
                "devices": [{"index": index} for index in range(hpu.device_count())],
                "note": "Exact Gaudi SKU and runtime are recorded by the HPU backend slice.",
            }
    except Exception as error:
        inventory["hpu"]["probe_error"] = f"{type(error).__name__}: {error}"
    return inventory
