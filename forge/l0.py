"""A tiny causal transformer for CPU correctness and training-loop smoke tests."""

import pickle
from dataclasses import asdict, dataclass
from io import BytesIO

from forge.canonical import digest
from forge.contracts import TinyLMWorkload


@dataclass(frozen=True)
class TinyTrainingResult:
    losses: list[float]
    parameter_count: int
    vocabulary_size: int
    training_tokens: int
    completed_steps: int
    checkpoint_bytes: bytes

    def report_fields(self) -> dict:
        fields = asdict(self)
        fields.pop("checkpoint_bytes")
        return fields


def train_tiny_transformer(
    workload: TinyLMWorkload,
    *,
    seed: int,
    resume_checkpoint: bytes | None = None,
    stop_after: int | None = None,
) -> TinyTrainingResult:
    try:
        import torch
        from torch import nn
    except ImportError as error:
        raise RuntimeError(
            "L0 training requires the optional torch extra: pip install -e '.[l0]'"
        ) from error

    end_step = workload.steps if stop_after is None else stop_after
    if not 1 <= end_step <= workload.steps:
        raise ValueError("stop_after must be within 1..workload.steps")
    workload_digest = digest(workload.model_dump(mode="json"), domain="forge.l0.workload.v1")
    torch.manual_seed(seed)
    vocabulary = sorted(set(workload.corpus))
    token_to_id = {char: index for index, char in enumerate(vocabulary)}
    token_ids = torch.tensor([token_to_id[char] for char in workload.corpus], dtype=torch.long)
    length = workload.sequence_length
    count = min(8, len(token_ids) - length - 1)
    inputs = torch.stack([token_ids[start : start + length] for start in range(count)])
    labels = torch.stack([token_ids[start + 1 : start + length + 1] for start in range(count)])

    class TinyDecoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.token = nn.Embedding(len(vocabulary), workload.hidden_size)
            self.position = nn.Embedding(length, workload.hidden_size)
            layer = nn.TransformerEncoderLayer(
                d_model=workload.hidden_size,
                nhead=workload.attention_heads,
                dim_feedforward=workload.hidden_size * 2,
                dropout=0.0,
                batch_first=True,
                norm_first=False,
            )
            self.blocks = nn.TransformerEncoder(layer, num_layers=workload.layers)
            self.output = nn.Linear(workload.hidden_size, len(vocabulary))

        def forward(self, tokens: "torch.Tensor") -> "torch.Tensor":
            positions = torch.arange(tokens.shape[1], device=tokens.device)
            hidden = self.token(tokens) + self.position(positions)
            causal_mask = torch.triu(
                torch.ones(tokens.shape[1], tokens.shape[1], dtype=torch.bool), diagonal=1
            )
            hidden = self.blocks(hidden, mask=causal_mask)
            return self.output(hidden)

    model = TinyDecoder()
    optimizer = torch.optim.AdamW(model.parameters(), lr=workload.learning_rate)
    losses = []
    start_step = 0
    if resume_checkpoint is not None:
        try:
            saved = torch.load(BytesIO(resume_checkpoint), map_location="cpu", weights_only=True)
            if (
                not isinstance(saved, dict)
                or saved.get("schema_version") != 2
                or saved.get("workload_digest") != workload_digest
                or saved.get("seed") != seed
                or saved.get("vocabulary") != vocabulary
                or saved.get("sequence_length") != length
            ):
                raise ValueError("checkpoint is incompatible with this L0 workload or seed")
            start_step = saved["completed_steps"]
            losses = saved["losses"]
            if (
                type(start_step) is not int
                or not 0 < start_step < workload.steps
                or start_step >= end_step
                or not isinstance(losses, list)
                or len(losses) != start_step
                or any(type(loss) is not float for loss in losses)
            ):
                raise ValueError("checkpoint step or loss history is invalid")
            model.load_state_dict(saved["model_state"])
            optimizer.load_state_dict(saved["optimizer_state"])
            torch.set_rng_state(saved["rng_state"])
        except (
            RuntimeError,
            KeyError,
            TypeError,
            ValueError,
            EOFError,
            pickle.UnpicklingError,
        ) as error:
            raise ValueError(f"L0 checkpoint cannot be resumed: {error}") from error
    for _ in range(start_step, end_step):
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = nn.functional.cross_entropy(logits.reshape(-1, len(vocabulary)), labels.reshape(-1))
        if not torch.isfinite(loss):
            raise RuntimeError("L0 loss became non-finite")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    stream = BytesIO()
    torch.save(
        {
            "schema_version": 2,
            "workload_digest": workload_digest,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "rng_state": torch.get_rng_state(),
            "completed_steps": end_step,
            "losses": losses,
            "vocabulary": vocabulary,
            "sequence_length": length,
            "seed": seed,
        },
        stream,
    )
    return TinyTrainingResult(
        losses=losses,
        parameter_count=sum(parameter.numel() for parameter in model.parameters()),
        vocabulary_size=len(vocabulary),
        training_tokens=int(inputs.numel()) * end_step,
        completed_steps=end_step,
        checkpoint_bytes=stream.getvalue(),
    )
