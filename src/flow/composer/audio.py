"""Dependency-free reference audio renderer for composition demos.

This deliberately small synthesizer makes recipes audible without a MIDI device,
SoundFont, or third-party package. Its sounds are for validating arrangement and
role handoffs, not for production-quality playback.
"""

from __future__ import annotations

import math
from pathlib import Path
import random
import struct
import wave

from flow.knowledge.models import KnowledgeEntry

from .midi import PPQ, ScheduledNote, realize_midi_notes


def _frequency(midi_note: int) -> float:
    return 440.0 * 2.0 ** ((midi_note - 69) / 12.0)


def _envelope(time: float, duration: float, attack: float, release: float) -> float:
    if time < 0 or time >= duration:
        return 0.0
    fade_in = min(1.0, time / attack) if attack else 1.0
    fade_out = min(1.0, (duration - time) / release) if release else 1.0
    return max(0.0, min(fade_in, fade_out))


def _render_tone(
    buffer: list[float], note: ScheduledNote, start: int, end: int, sample_rate: int
) -> None:
    frequency = _frequency(note.midi_note)
    duration = (end - start) / sample_rate
    level = note.velocity / 127.0
    if note.role == "bass":
        harmonics = ((1, 0.78), (2, 0.18), (3, 0.04))
        amplitude, attack, release = 0.34, 0.008, 0.08
    else:
        harmonics = ((1, 0.58), (2, 0.27), (3, 0.15))
        amplitude, attack, release = 0.24, 0.012, 0.06

    for index in range(start, end):
        elapsed = (index - start) / sample_rate
        phase = 2.0 * math.pi * frequency * elapsed
        tone = sum(weight * math.sin(harmonic * phase) for harmonic, weight in harmonics)
        buffer[index] += amplitude * level * _envelope(elapsed, duration, attack, release) * tone


def _render_drum(
    buffer: list[float], note: ScheduledNote, start: int, end: int, sample_rate: int
) -> None:
    duration = (end - start) / sample_rate
    level = note.velocity / 127.0
    rng = random.Random((note.start_tick << 8) ^ note.midi_note)
    previous_noise = 0.0

    if note.midi_note == 36:  # kick: short downward pitch sweep
        for index in range(start, end):
            elapsed = (index - start) / sample_rate
            phase = 2.0 * math.pi * (
                43.0 * elapsed + 87.0 * (1.0 - math.exp(-22.0 * elapsed)) / 22.0
            )
            buffer[index] += 0.62 * level * math.exp(-15.0 * elapsed) * math.sin(phase)
        return

    decay = 34.0 if note.midi_note == 42 else 12.0
    amplitude = 0.16 if note.midi_note == 42 else 0.34
    tone_frequency = 180.0
    for index in range(start, end):
        elapsed = (index - start) / sample_rate
        noise = rng.uniform(-1.0, 1.0)
        # Difference the noise to make the subdivision hat brighter.
        noise_component = noise - previous_noise if note.midi_note == 42 else noise
        previous_noise = noise
        tonal_component = (
            0.22 * math.sin(2.0 * math.pi * tone_frequency * elapsed)
            if note.midi_note != 42
            else 0.0
        )
        envelope = math.exp(-decay * elapsed)
        buffer[index] += amplitude * level * envelope * (noise_component + tonal_component)


def _render_note(buffer: list[float], note: ScheduledNote, tempo_bpm: float, sample_rate: int) -> None:
    seconds_per_tick = 60.0 / tempo_bpm / PPQ
    start = max(0, round(note.start_tick * seconds_per_tick * sample_rate))
    end = max(start + 1, round(note.end_tick * seconds_per_tick * sample_rate))
    end = min(end, len(buffer))
    if note.role == "percussion":
        _render_drum(buffer, note, start, end, sample_rate)
    else:
        _render_tone(buffer, note, start, end, sample_rate)


def render_wav(
    entry: KnowledgeEntry,
    output_path: Path,
    *,
    tonic_midi: int = 60,
    tempo_bpm: float = 120.0,
    sample_rate: int = 44100,
) -> tuple[ScheduledNote, ...]:
    """Render a recipe to a mono PCM WAV and return its realized notes."""
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("sample_rate must be between 8000 and 192000 Hz")
    if tempo_bpm <= 0:
        raise ValueError("tempo_bpm must be positive")
    notes = realize_midi_notes(entry, tonic_midi=tonic_midi, tempo_bpm=tempo_bpm)
    if not notes:
        raise ValueError("cannot render a recipe with no note events")

    seconds_per_tick = 60.0 / tempo_bpm / PPQ
    final_note_tick = max(note.end_tick for note in notes)
    frame_count = round((final_note_tick * seconds_per_tick + 0.25) * sample_rate)
    mix = [0.0] * frame_count
    for note in notes:
        _render_note(mix, note, tempo_bpm, sample_rate)

    # Fixed gain and a soft limiter keep overlapping roles from clipping.
    pcm = bytearray()
    for value in mix:
        limited = math.tanh(value * 1.35)
        pcm.extend(struct.pack("<h", round(limited * 32767)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(pcm)
    return notes
