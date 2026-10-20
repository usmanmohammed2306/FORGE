"""Measurement-backed diagnostic rules for the first CPU data experiment."""

from typing import Any


def diagnose(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("workload") != "packing":
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "reason": "No diagnostic rule exists for this workload yet.",
            "next_experiment": "Collect a phase and memory breakdown.",
        }
    rows = {row["method"]: row for row in report["layouts"]}
    naive = rows["naive_padding"]
    grouped = rows["length_grouping"]
    packed = rows["first_fit_packing"]
    if naive["efficiency"] >= 0.85:
        return {
            "status": "NO_DOMINANT_PADDING_BOTTLENECK",
            "evidence": {"naive_real_token_utilization": naive["efficiency"]},
            "next_experiment": "Measure actual accelerator step time before changing layout.",
        }
    best = max((grouped, packed), key=lambda row: row["efficiency"])
    return {
        "status": "PADDING_PRESSURE",
        "confidence": "analytical token-count evidence; no accelerator speed claim",
        "evidence": {
            "naive_real_token_utilization": naive["efficiency"],
            "best_layout": best["method"],
            "best_real_token_utilization": best["efficiency"],
        },
        "next_experiment": (
            f"Test {best['method']} on the same model, dataset, token budget, and hardware; "
            "measure throughput, peak memory, and held-out quality."
        ),
    }
