import pytest

from forge.campaign import CampaignPoint, pareto_frontier

CONTEXT = "sha256:" + "a" * 64
REPORT = "sha256:" + "b" * 64


def point(run_id: str, speed: float, memory: float, quality: float) -> CampaignPoint:
    return CampaignPoint(
        run_id=run_id,
        context_digest=CONTEXT,
        report_ref=REPORT,
        real_tokens_per_second=speed,
        peak_device_memory_gb=memory,
        held_out_solve_rate=quality,
    )


def test_frontier_removes_dominated_run_but_keeps_real_tradeoff():
    fast = point("fast", 120, 70, 0.70)
    balanced = point("balanced", 110, 60, 0.72)
    dominated = point("dominated", 90, 80, 0.69)
    assert [x.run_id for x in pareto_frontier([dominated, fast, balanced])] == [
        "balanced",
        "fast",
    ]


def test_frontier_refuses_mixed_context_or_duplicate_run():
    first = point("a", 100, 60, 0.7)
    other_context = point("b", 110, 55, 0.7).model_copy(
        update={"context_digest": "sha256:" + "c" * 64}
    )
    with pytest.raises(ValueError, match="incomparable"):
        pareto_frontier([first, other_context])
    with pytest.raises(ValueError, match="duplicate"):
        pareto_frontier([first, first])
