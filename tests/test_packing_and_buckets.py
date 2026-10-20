from itertools import combinations

from forge.buckets import recommend_buckets
from forge.packing import compare_layouts


def test_layouts_count_same_real_tokens_and_no_negative_padding():
    lengths = [3, 8, 4, 7, 2, 9]
    rows = compare_layouts(lengths, batch_size=3, max_sequence_length=10)
    assert {row["real_tokens"] for row in rows} == {sum(lengths)}
    assert all(row["physical_tokens"] >= row["real_tokens"] for row in rows)
    assert rows[1]["physical_tokens"] <= rows[0]["physical_tokens"]


def test_bucket_optimizer_matches_brute_force_small_space():
    lengths = [2, 2, 3, 6, 8, 8]
    penalty = 3.0
    result = recommend_buckets(lengths, max_buckets=3, compile_penalty_tokens=penalty)
    unique = sorted(set(lengths))
    brute = []
    for count in range(1, 4):
        for endpoints in combinations(unique[:-1], count - 1):
            buckets = (*endpoints, unique[-1])
            waste = sum(min(bucket for bucket in buckets if bucket >= x) - x for x in lengths)
            brute.append((waste + penalty * count, count, list(buckets), waste))
    best = min(brute)
    assert result.objective == best[0]
    assert result.shape_classes == best[1]
    assert result.padding_tokens == best[3]


def test_bucket_penalty_reduces_shape_classes():
    lengths = [10, 20, 30, 40]
    free = recommend_buckets(lengths, max_buckets=4, compile_penalty_tokens=0)
    costly = recommend_buckets(lengths, max_buckets=4, compile_penalty_tokens=100)
    assert free.shape_classes == 4
    assert costly.shape_classes == 1
