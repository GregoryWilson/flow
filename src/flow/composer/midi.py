"""Dependency-free Standard MIDI File export for simple recipe demonstrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct

from flow.knowledge.models import EventType, KnowledgeEntry


PPQ = 480
MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)
PERCUSSION_NOTES = {"kick": 36, "backbeat": 38, "subdivision": 42}
GM_PROGRAMS = {"melody": 81, "bass": 38}
GM_CHANNELS = {"melody": 0, "bass": 1, "percussion": 9}


@dataclass(frozen=True, slots=True)
class ScheduledNote:
    role: str
    start_tick: int
    end_tick: int
    midi_note: int
    velocity: int
    channel: int
    program: int


def _scale_note(degree: float, tonic_midi: int, octave_offset: int) -> int:
    degree = float(degree)
    if not degree.is_integer():
        raise ValueError("MIDI demo export currently requires whole-number scale degrees")
    zero_based_degree = int(degree) - 1
    octave, scale_index = divmod(zero_based_degree, len(MINOR_SCALE))
    midi_note = tonic_midi + octave_offset + octave * 12 + MINOR_SCALE[scale_index]
    if not 0 <= midi_note <= 127:
        raise ValueError(f"realized MIDI note is outside the supported range: {midi_note}")
    return midi_note


def _focus_span_at(entry: KnowledgeEntry, beat: float):
    return next(
        (
            span
            for span in entry.recipe.focus_plan
            if span.start_beat <= beat < span.start_beat + span.duration_beats
        ),
        None,
    )


def realize_midi_notes(
    entry: KnowledgeEntry,
    *,
    tonic_midi: int = 60,
    tempo_bpm: float = 120.0,
) -> tuple[ScheduledNote, ...]:
    """Map relative recipe events to a fixed MIDI register and tempo."""
    if not 24 <= tonic_midi <= 108:
        raise ValueError("tonic_midi must be between 24 and 108 for the demo role ranges")
    if tempo_bpm <= 0:
        raise ValueError("tempo_bpm must be positive")

    notes: list[ScheduledNote] = []
    for event in entry.recipe.events:
        if event.event_type != EventType.NOTE:
            continue
        channel = GM_CHANNELS.get(event.role, 2)
        if event.role == "percussion":
            percussion_tag = next(
                (tag for tag in event.tags if tag in PERCUSSION_NOTES), "subdivision"
            )
            midi_note = PERCUSSION_NOTES[percussion_tag]
            program = 0
        else:
            octave_offset = -24 if event.role == "bass" else 0
            midi_note = _scale_note(event.scale_degree or 1, tonic_midi, octave_offset)
            program = GM_PROGRAMS.get(event.role, 0)

        span = _focus_span_at(entry, event.beat)
        velocity = round(event.velocity * 127)
        if span is not None:
            velocity = (
                max(velocity, 114)
                if event.role in span.foreground_roles
                else min(velocity, 82)
            )
        start_tick = round(event.beat * PPQ)
        end_tick = round((event.beat + event.duration_beats) * PPQ)
        notes.append(
            ScheduledNote(
                role=event.role,
                start_tick=start_tick,
                end_tick=end_tick,
                midi_note=midi_note,
                velocity=velocity,
                channel=channel,
                program=program,
            )
        )
    unsupported_roles = {note.role for note in notes} - set(GM_CHANNELS)
    if unsupported_roles:
        raise ValueError(
            f"MIDI demo export does not yet support roles: {sorted(unsupported_roles)}"
        )
    return tuple(notes)


def _variable_length(value: int) -> bytes:
    if value < 0:
        raise ValueError("MIDI delta time cannot be negative")
    encoded = [value & 0x7F]
    value >>= 7
    while value:
        encoded.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(encoded)


def _track_chunk(events: list[tuple[int, int, bytes]]) -> bytes:
    events.sort(key=lambda event: (event[0], event[1]))
    payload = bytearray()
    previous_tick = 0
    for tick, _, message in events:
        payload.extend(_variable_length(tick - previous_tick))
        payload.extend(message)
        previous_tick = tick
    payload.extend(b"\x00\xff\x2f\x00")
    return b"MTrk" + struct.pack(">I", len(payload)) + payload


def write_midi(
    entry: KnowledgeEntry,
    output_path: Path,
    *,
    tonic_midi: int = 60,
    tempo_bpm: float = 120.0,
) -> tuple[ScheduledNote, ...]:
    """Write a format-1 MIDI file and return its scheduled note events."""
    if tempo_bpm <= 0:
        raise ValueError("tempo_bpm must be positive")
    notes = realize_midi_notes(entry, tonic_midi=tonic_midi, tempo_bpm=tempo_bpm)
    track_roles = tuple(dict.fromkeys(note.role for note in notes))
    tracks: list[bytes] = []

    microseconds_per_quarter = round(60_000_000 / tempo_bpm)
    if not 1 <= microseconds_per_quarter <= 0xFFFFFF:
        raise ValueError("tempo_bpm is outside the Standard MIDI File tempo range")
    tempo_event = b"\xff\x51\x03" + microseconds_per_quarter.to_bytes(3, "big")
    time_signature = b"\xff\x58\x04\x04\x02\x18\x08"
    tracks.append(_track_chunk([(0, 0, tempo_event), (0, 0, time_signature)]))

    for role in track_roles:
        role_notes = [note for note in notes if note.role == role]
        channel = role_notes[0].channel
        events: list[tuple[int, int, bytes]] = []
        if channel != 9:
            events.append((0, 0, bytes((0xC0 | channel, role_notes[0].program))))
        for note in role_notes:
            events.append(
                (note.start_tick, 2, bytes((0x90 | channel, note.midi_note, note.velocity)))
            )
            events.append((note.end_tick, 1, bytes((0x80 | channel, note.midi_note, 0))))
        tracks.append(_track_chunk(events))

    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(header + b"".join(tracks))
    return notes
