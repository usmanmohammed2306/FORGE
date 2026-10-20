"""Multi-objective comparison core for evidence-backed optimization campaigns."""

from pydantic import BaseModel, ConfigDict, Field


class CampaignPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    run_id: str = Field(min_length=1)
    context_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    report_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    real_tokens_per_second: float = Field(gt=0)
    peak_device_memory_gb: float = Field(gt=0)
    held_out_solve_rate: float = Field(ge=0, le=1)


def _dominates(left: CampaignPoint, right: CampaignPoint) -> bool:
    no_worse = (
        left.real_tokens_per_second >= right.real_tokens_per_second
        and left.peak_device_memory_gb <= right.peak_device_memory_gb
        and left.held_out_solve_rate >= right.held_out_solve_rate
    )
    strictly_better = (
        left.real_tokens_per_second > right.real_tokens_per_second
        or left.peak_device_memory_gb < right.peak_device_memory_gb
        or left.held_out_solve_rate > right.held_out_solve_rate
    )
    return no_worse and strictly_better


def pareto_frontier(points: list[CampaignPoint]) -> list[CampaignPoint]:
    """Return nondominated measured candidates in stable run-ID order.

    The caller must first verify report bytes and construct a context digest from
    the controls held constant. This core refuses mixed contexts.
    """
    if not points:
        raise ValueError("campaign needs at least one measured point")
    contexts = {point.context_digest for point in points}
    if len(contexts) != 1:
        raise ValueError("campaign contains incomparable experiment contexts")
    ids = [point.run_id for point in points]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate run IDs would double-count evidence")
    return sorted(
        (point for point in points if not any(_dominates(other, point) for other in points)),
        key=lambda point: point.run_id,
    )
