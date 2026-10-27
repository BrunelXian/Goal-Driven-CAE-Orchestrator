"""Read DTOs only; neither AF execution permission nor research verdicts."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceIdentity:
    project_id: str
    project_instance_id: str
    context_digest: str
    owner_id: str


@dataclass(frozen=True)
class ProjectBinding:
    root: str = field(repr=False)
    project_id: str
    project_instance_id: str
    context_digest: str
    owner_id: str


@dataclass(frozen=True)
class ReadCursor:
    source: SourceIdentity
    operation: str
    position: int


@dataclass(frozen=True)
class ReadError:
    code: str
    stage: str


@dataclass(frozen=True)
class ReadEnvelope:
    operation: str
    source: SourceIdentity | None
    read_at: int
    completeness: str
    consistency: str
    data: Any = None
    source_read_at: int | None = None
    next_cursor: ReadCursor | None = None
    more_possible: bool | None = None
    error: ReadError | None = None
    schema_version: str = "gd-af-read-v1"
