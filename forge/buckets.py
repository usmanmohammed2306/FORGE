"""Exact bounded optimizer for padding waste versus compiled shape count."""

from collections import Counter
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BucketRecommendation:
    buckets: list[int]
    padding_tokens: int
    shape_classes: int
    objective: float
    total_real_tokens: int

    def as_dict(self) -> dict:
        return asdict(self)


def recommend_buckets(
    lengths: list[int], *, max_buckets: int, compile_penalty_tokens: float
) -> BucketRecommendation:
    """Pick endpoints from observed lengths with O(K n^2) dynamic programming.

    The penalty is expressed in equivalent padded tokens per distinct compiled shape.
    This is a prediction, not a measured compile-time result.
    """
    if not lengths or any(length < 1 for length in lengths):
        raise ValueError("lengths must contain positive integers")
    if max_buckets < 1 or compile_penalty_tokens < 0:
        raise ValueError("max_buckets must be positive and penalty nonnegative")
    counts = Counter(lengths)
    values = sorted(counts)
    n = len(values)
    k_max = min(max_buckets, n)
    prefix_count = [0]
    prefix_tokens = [0]
    for length in values:
        prefix_count.append(prefix_count[-1] + counts[length])
        prefix_tokens.append(prefix_tokens[-1] + length * counts[length])

    def waste(start: int, end: int) -> int:
        quantity = prefix_count[end + 1] - prefix_count[start]
        real = prefix_tokens[end + 1] - prefix_tokens[start]
        return values[end] * quantity - real

    infinity = float("inf")
    costs = [[infinity] * (n + 1) for _ in range(k_max + 1)]
    previous = [[-1] * (n + 1) for _ in range(k_max + 1)]
    costs[0][0] = 0.0
    for k in range(1, k_max + 1):
        for end in range(k, n + 1):
            for start in range(k - 1, end):
                candidate = costs[k - 1][start] + waste(start, end - 1)
                if candidate < costs[k][end]:
                    costs[k][end] = candidate
                    previous[k][end] = start

    best_k = min(
        range(1, k_max + 1),
        key=lambda k: (costs[k][n] + compile_penalty_tokens * k, k),
    )
    endpoints = []
    end = n
    for k in range(best_k, 0, -1):
        endpoints.append(values[end - 1])
        end = previous[k][end]
    endpoints.reverse()
    padding = int(costs[best_k][n])
    return BucketRecommendation(
        buckets=endpoints,
        padding_tokens=padding,
        shape_classes=best_k,
        objective=padding + compile_penalty_tokens * best_k,
        total_real_tokens=sum(lengths),
    )
