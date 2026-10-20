"""Three honest layout baselines on the same logical token stream."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LayoutResult:
    method: str
    real_tokens: int
    physical_tokens: int
    padding_tokens: int
    efficiency: float
    sequences: int

    def as_dict(self) -> dict:
        return asdict(self)


def _result(method: str, lengths: list[int], physical: int, sequences: int) -> LayoutResult:
    real = sum(lengths)
    if physical < real:
        raise AssertionError("physical tokens cannot be fewer than real tokens")
    return LayoutResult(method, real, physical, physical - real, real / physical, sequences)


def naive_padding(lengths: list[int], batch_size: int) -> LayoutResult:
    physical = 0
    for start in range(0, len(lengths), batch_size):
        batch = lengths[start : start + batch_size]
        physical += max(batch) * len(batch)
    return _result("naive_padding", lengths, physical, len(lengths))


def length_grouping(lengths: list[int], batch_size: int) -> LayoutResult:
    ordered = sorted(lengths)
    physical = 0
    for start in range(0, len(ordered), batch_size):
        batch = ordered[start : start + batch_size]
        physical += max(batch) * len(batch)
    return _result("length_grouping", lengths, physical, len(lengths))


def first_fit_packing(lengths: list[int], max_sequence_length: int) -> LayoutResult:
    """First-fit decreasing token lengths; model masking is a later data-plane slice."""
    bins: list[int] = []
    for length in sorted(lengths, reverse=True):
        for index, occupied in enumerate(bins):
            if occupied + length <= max_sequence_length:
                bins[index] += length
                break
        else:
            bins.append(length)
    return _result("first_fit_packing", lengths, len(bins) * max_sequence_length, len(bins))


def compare_layouts(lengths: list[int], batch_size: int, max_sequence_length: int) -> list[dict]:
    if len(lengths) < 2 or any(length < 1 or length > max_sequence_length for length in lengths):
        raise ValueError("need at least two lengths in 1..max_sequence_length")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    return [
        naive_padding(lengths, batch_size).as_dict(),
        length_grouping(lengths, batch_size).as_dict(),
        first_fit_packing(lengths, max_sequence_length).as_dict(),
    ]
