import pytest

from forge.stats import judge_centerpiece_target, paired_rate_delta, paired_relative_change


def test_identical_paired_outcomes_have_zero_delta_and_no_target_claim():
    outcomes = [True, False, True, False] * 20
    quality = paired_rate_delta(outcomes, outcomes, repeats=500, seed=7)
    throughput = paired_relative_change(
        [100.0] * 20, [120.0] * 20, lower_is_better=False, repeats=500, seed=7
    )
    memory = paired_relative_change(
        [80.0] * 20, [55.0] * 20, lower_is_better=True, repeats=500, seed=7
    )
    assert quality.estimate == quality.low == quality.high == 0
    assert judge_centerpiece_target(throughput, memory, quality)["target_met"]


def test_noisy_quality_drop_fails_noninferiority():
    base = [True] * 90 + [False] * 10
    tuned = [True] * 80 + [False] * 20
    quality = paired_rate_delta(base, tuned, repeats=500, seed=1)
    throughput = paired_relative_change(
        [100.0] * 20, [120.0] * 20, lower_is_better=False, repeats=500, seed=1
    )
    memory = paired_relative_change(
        [80.0] * 20, [55.0] * 20, lower_is_better=True, repeats=500, seed=1
    )
    verdict = judge_centerpiece_target(throughput, memory, quality)
    assert not verdict["target_met"]
    assert not verdict["checks"]["quality_noninferior_within_1_percentage_point"]


def test_unpaired_or_nonpositive_samples_are_refused():
    with pytest.raises(ValueError):
        paired_rate_delta([True], [True])
    with pytest.raises(ValueError):
        paired_relative_change([100.0, 100.0], [0.0, 1.0], lower_is_better=False)
