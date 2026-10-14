"""Dependency-free domain models for executable musical knowledge."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import Any


class Status(StrEnum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    DEMONSTRATED = "demonstrated"
    VALIDATED = "validated"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EventType(StrEnum):
    NOTE = "note"
    REST = "rest"
    SILENCE = "silence"
    CONTROL = "control"


class MelodyPresence(StrEnum):
    FOREGROUND = "foreground"
    BACKGROUND = "background"
    ABSENT = "absent"
    INTERMITTENT = "intermittent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MusicalEvent:
    role: str
    beat: float
    duration_beats: float
    event_type: EventType = EventType.NOTE
    scale_degree: float | None = None
    interval_semitones: float | None = None
    velocity: float = 0.8
    timing_offset_ms: float = 0.0
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if not 0 <= self.velocity <= 1:
            raise ValueError("velocity must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class FocusSpan:
    """A bounded period describing which musical roles hold foreground focus."""

    start_beat: float
    duration_beats: float
    foreground_roles: tuple[str, ...]
    melody_presence: MelodyPresence = MelodyPresence.UNKNOWN

    def __post_init__(self) -> None:
        if self.start_beat < 0:
            raise ValueError("start_beat cannot be negative")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if len(set(self.foreground_roles)) != len(self.foreground_roles):
            raise ValueError("foreground_roles must be unique")


@dataclass(frozen=True, slots=True)
class Evidence:
    source_id: str
    start_seconds: float
    end_seconds: float
    claim: str
    confidence: float

    def __post_init__(self) -> None:
        if self.start_seconds < 0 or self.end_seconds < self.start_seconds:
            raise ValueError("evidence timestamps are invalid")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Recipe:
    roles: tuple[str, ...]
    events: tuple[MusicalEvent, ...]
    invariants: tuple[str, ...]
    transformations: tuple[str, ...]
    focus_plan: tuple[FocusSpan, ...] = ()

    def __post_init__(self) -> None:
        unknown = {event.role for event in self.events} - set(self.roles)
        if unknown:
            raise ValueError(f"events reference unknown roles: {sorted(unknown)}")
        unknown_focus_roles = {
            role for span in self.focus_plan for role in span.foreground_roles
        } - set(self.roles)
        if unknown_focus_roles:
            raise ValueError(
                f"focus plan references unknown roles: {sorted(unknown_focus_roles)}"
            )
        previous_end = 0.0
        for span in self.focus_plan:
            if span.start_beat < previous_end:
                raise ValueError("focus plan spans cannot overlap and must be ordered")
            previous_end = span.start_beat + span.duration_beats


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    id: str
    title: str
    intent_description: str
    recipe: Recipe
    status: Status = Status.PROPOSED
    effects: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    avoid_when: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    alternatives: tuple[str, ...] = ()
    confidence: float = 0.0
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.id or not self.title:
            raise ValueError("id and title are required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["intent"] = {
            "description": data.pop("intent_description"),
            "effects": data.pop("effects"),
        }
        data["context"] = {
            "requires": data.pop("requires"),
            "avoid_when": data.pop("avoid_when"),
        }
        return data

    def write_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeEntry:
        """Build a validated knowledge entry from the versioned JSON shape."""
        intent = data["intent"]
        context = data.get("context", {})
        recipe_data = data["recipe"]
        events = tuple(
            MusicalEvent(
                role=event["role"],
                beat=event["beat"],
                duration_beats=event["duration_beats"],
                event_type=EventType(event.get("event_type", EventType.NOTE)),
                scale_degree=event.get("scale_degree"),
                interval_semitones=event.get("interval_semitones"),
                velocity=event.get("velocity", 0.8),
                timing_offset_ms=event.get("timing_offset_ms", 0.0),
                tags=tuple(event.get("tags", ())),
            )
            for event in recipe_data["events"]
        )
        focus_plan = tuple(
            FocusSpan(
                start_beat=span["start_beat"],
                duration_beats=span["duration_beats"],
                foreground_roles=tuple(span["foreground_roles"]),
                melody_presence=MelodyPresence(span.get("melody_presence", "unknown")),
            )
            for span in recipe_data.get("focus_plan", ())
        )
        evidence = tuple(
            Evidence(
                source_id=item["source_id"],
                start_seconds=item["start_seconds"],
                end_seconds=item["end_seconds"],
                claim=item["claim"],
                confidence=item.get("confidence", 0.0),
            )
            for item in data.get("evidence", ())
        )
        return cls(
            id=data["id"],
            title=data["title"],
            intent_description=intent["description"],
            recipe=Recipe(
                roles=tuple(recipe_data["roles"]),
                events=events,
                invariants=tuple(recipe_data["invariants"]),
                transformations=tuple(recipe_data["transformations"]),
                focus_plan=focus_plan,
            ),
            status=Status(data.get("status", Status.PROPOSED)),
            effects=tuple(intent.get("effects", ())),
            requires=tuple(context.get("requires", ())),
            avoid_when=tuple(context.get("avoid_when", ())),
            evidence=evidence,
            alternatives=tuple(data.get("alternatives", ())),
            confidence=data.get("confidence", 0.0),
            schema_version=data.get("schema_version", "1.0"),
        )

    @classmethod
    def read_json(cls, path: Path) -> KnowledgeEntry:
        """Read and parse a knowledge entry from a UTF-8 JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("knowledge entry JSON must contain an object")
        return cls.from_dict(data)

