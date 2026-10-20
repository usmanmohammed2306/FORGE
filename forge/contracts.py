"""Small experiment contract. Later accelerators extend the workload union."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from forge.canonical import digest


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ModelRef(StrictModel):
    id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    level: Literal["L0", "L1", "L2", "L3"] = "L0"


class DatasetRef(StrictModel):
    id: str = Field(min_length=1)
    revision: str = Field(min_length=1)


class HardwareRequest(StrictModel):
    backend: Literal["cpu", "cuda", "hpu"] = "cpu"
    world_size: int = Field(default=1, ge=1, le=64)

    @model_validator(mode="after")
    def cpu_is_single_process(self) -> "HardwareRequest":
        if self.backend == "cpu" and self.world_size != 1:
            raise ValueError("the local CPU runner supports world_size=1 only")
        return self


class PackingWorkload(StrictModel):
    kind: Literal["packing"] = "packing"
    sequence_lengths: list[int] = Field(min_length=2)
    batch_size: int = Field(default=4, ge=1)
    max_sequence_length: int = Field(default=2048, ge=2)

    @model_validator(mode="after")
    def lengths_fit(self) -> "PackingWorkload":
        if any(length < 1 or length > self.max_sequence_length for length in self.sequence_lengths):
            raise ValueError("every sequence length must be within 1..max_sequence_length")
        return self


class TinyLMWorkload(StrictModel):
    kind: Literal["tiny_lm"] = "tiny_lm"
    corpus: str = Field(min_length=32)
    sequence_length: int = Field(default=12, ge=4, le=128)
    steps: int = Field(default=12, ge=2, le=100)
    hidden_size: int = Field(default=32, ge=8, le=256)
    attention_heads: int = Field(default=4, ge=1, le=16)
    layers: int = Field(default=2, ge=1, le=4)
    learning_rate: float = Field(default=0.01, gt=0, le=0.1)

    @model_validator(mode="after")
    def valid_shape(self) -> "TinyLMWorkload":
        if self.hidden_size % self.attention_heads:
            raise ValueError("hidden_size must be divisible by attention_heads")
        if len(self.corpus) < self.sequence_length + 2:
            raise ValueError("corpus must exceed sequence_length by at least two characters")
        return self


class Experiment(StrictModel):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=3, pattern=r"^[a-z][a-z0-9_-]+$")
    model: ModelRef
    dataset: DatasetRef
    hardware: HardwareRequest = HardwareRequest()
    workload: PackingWorkload | TinyLMWorkload = Field(discriminator="kind")
    seed: int = Field(default=0, ge=0)

    @property
    def config_digest(self) -> str:
        return digest(self.model_dump(mode="json"), domain="forge.experiment.v1")
