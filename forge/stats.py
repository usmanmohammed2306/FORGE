"""Paired, deterministic uncertainty calculations for preregistered comparisons."""

import random
from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True)
class Interval:
    estimate: float
    low: float
    high: float
    confidence: float
    samples: int

    def as_dict(self) -> dict:
        return asdict(self)


def paired_bootstrap(
    baseline: list[float],
    candidate: list[float],
    statistic: Callable[[list[float], list[float]], float],
    *,
    repeats: int = 10_000,
    seed: int = 0,
    confidence: float = 0.95,
) -> Interval:
    if len(baseline) != len(candidate) or len(baseline) < 2:
        raise ValueError("paired samples must have equal length of at least two")
    if repeats < 100 or not 0 < confidence < 1:
        raise ValueError("need at least 100 repeats and confidence in (0, 1)")
    n = len(baseline)
    rng = random.Random(seed)
    draws = []
    for _ in range(repeats):
        indices = [rng.randrange(n) for _ in range(n)]
        draws.append(statistic([baseline[i] for i in indices], [candidate[i] for i in indices]))
    draws.sort()
    tail = (1 - confidence) / 2
    low_index = max(0, int(tail * repeats))
    high_index = min(repeats - 1, int((1 - tail) * repeats))
    return Interval(
        statistic(baseline, candidate), draws[low_index], draws[high_index], confidence, n
    )


def paired_rate_delta(
    baseline: list[bool], candidate: list[bool], *, repeats: int = 10_000, seed: int = 0
) -> Interval:
    if any(type(x) is not bool for x in baseline + candidate):
        raise ValueError("solve outcomes must be booleans")
    return paired_bootstrap(
        [float(x) for x in baseline],
        [float(x) for x in candidate],
        lambda a, b: sum(y - x for x, y in zip(a, b)) / len(a),
        repeats=repeats,
        seed=seed,
    )


def paired_relative_change(
    baseline: list[float],
    candidate: list[float],
    *,
    lower_is_better: bool,
    repeats: int = 10_000,
    seed: int = 0,
) -> Interval:
    if any(x <= 0 for x in baseline + candidate):
        raise ValueError("performance samples must be positive")

    def improvement(a: list[float], b: list[float]) -> float:
        a_mean = sum(a) / len(a)
        b_mean = sum(b) / len(b)
        if lower_is_better:
            return 1 - b_mean / a_mean
        return b_mean / a_mean - 1

    return paired_bootstrap(baseline, candidate, improvement, repeats=repeats, seed=seed)


def judge_centerpiece_target(throughput: Interval, memory: Interval, quality: Interval) -> dict:
    """All three bounds must support the target; point estimates are insufficient."""
    checks = {
        "throughput_at_least_15_percent": throughput.low >= 0.15,
        "memory_reduction_at_least_25_percent": memory.low >= 0.25,
        "quality_noninferior_within_1_percentage_point": quality.low >= -0.01,
    }
    return {
        "target_met": all(checks.values()),
        "checks": checks,
        "rule": "Require the lower 95% paired bound for every target; missing evidence cannot pass.",
    }
