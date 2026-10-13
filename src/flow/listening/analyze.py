"""Passage-aware local audio measurements.

The analyzer reports signal evidence, not musical intent. In particular, an
onset cluster is not a note transcription, and a low-energy interval is not
proof of notated silence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True, slots=True)
class OnsetCluster:
    start_seconds: float
    end_seconds: float
    center_seconds: float
    event_count: int


@dataclass(frozen=True, slots=True)
class TimeWindow:
    start_seconds: float
    end_seconds: float
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class PitchCandidate:
    midi_note: int
    note_name: str
    relative_strength: float


@dataclass(frozen=True, slots=True)
class PitchEvidenceWindow:
    start_seconds: float
    end_seconds: float
    candidates: tuple[PitchCandidate, ...]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    source_path: str
    sample_rate: int
    duration_seconds: float
    tempo_bpm: float
    beat_seconds: tuple[float, ...]
    onset_seconds: tuple[float, ...]
    mean_rms: float
    peak_rms: float
    mean_spectral_centroid_hz: float
    mean_chroma: tuple[float, ...]
    analyzed_start_seconds: float
    analyzed_end_seconds: float
    onset_clusters: tuple[OnsetCluster, ...]
    onset_gaps: tuple[dict[str, float], ...]
    beat_interval_windows: tuple[dict[str, float | int], ...]
    chroma_windows: tuple[TimeWindow, ...]
    pitch_evidence_windows: tuple[PitchEvidenceWindow, ...]
    low_energy_intervals: tuple[dict[str, float], ...]
    analyzer: str = "flow-listening-passage/0.3"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def cluster_onsets(onsets: Iterable[float], merge_within_seconds: float = 0.09) -> tuple[OnsetCluster, ...]:
    """Group near-simultaneous attacks without deleting raw onset evidence."""
    if merge_within_seconds < 0:
        raise ValueError("merge_within_seconds cannot be negative")
    ordered = sorted(float(value) for value in onsets)
    if not ordered:
        return ()

    groups: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] <= merge_within_seconds:
            groups[-1].append(value)
        else:
            groups.append([value])

    return tuple(
        OnsetCluster(
            start_seconds=group[0],
            end_seconds=group[-1],
            center_seconds=sum(group) / len(group),
            event_count=len(group),
        )
        for group in groups
    )


def candidate_onset_gaps(
    clusters: Sequence[OnsetCluster], *, minimum_seconds: float = 0.5, ratio: float = 1.8
) -> tuple[dict[str, float], ...]:
    """Return unusually long inter-onset gaps as candidates, not phrase labels."""
    if len(clusters) < 3:
        return ()
    spacings = [b.center_seconds - a.center_seconds for a, b in zip(clusters, clusters[1:])]
    baseline = sorted(spacings)[len(spacings) // 2]
    threshold = max(minimum_seconds, baseline * ratio)
    return tuple(
        {
            "start_seconds": left.center_seconds,
            "end_seconds": right.center_seconds,
            "duration_seconds": gap,
        }
        for left, right, gap in zip(clusters, clusters[1:], spacings)
        if gap >= threshold
    )


def beat_interval_windows(
    beat_seconds: Sequence[float], *, beats_per_window: int = 8, absolute_offset: float = 0.0
) -> tuple[dict[str, float | int], ...]:
    """Summarize local pulse rates from detected beat intervals.

    Long intervals are deliberately retained: a fermata or missed beat should
    appear as uncertainty/tempo drift rather than being silently normalized.
    """
    if beats_per_window < 2:
        raise ValueError("beats_per_window must be at least 2")
    result: list[dict[str, float | int]] = []
    for start in range(0, len(beat_seconds) - 1, beats_per_window):
        part = beat_seconds[start : start + beats_per_window + 1]
        if len(part) < 3:
            continue
        intervals = sorted(b - a for a, b in zip(part, part[1:]) if b > a)
        if not intervals:
            continue
        middle = len(intervals) // 2
        median = intervals[middle] if len(intervals) % 2 else (intervals[middle - 1] + intervals[middle]) / 2
        result.append(
            {
                "start_seconds": absolute_offset + part[0],
                "end_seconds": absolute_offset + part[-1],
                "beat_count": len(part) - 1,
                "median_interval_seconds": median,
                "median_bpm": 60.0 / median,
                "interval_spread_seconds": intervals[-1] - intervals[0],
            }
        )
    return tuple(result)


def _low_energy_intervals(
    rms_values: Sequence[float],
    frame_times: Sequence[float],
    *,
    threshold: float,
    minimum_seconds: float,
) -> tuple[dict[str, float], ...]:
    low_energy = [float(value) <= threshold for value in rms_values]
    intervals: list[dict[str, float]] = []
    start: int | None = None
    for index, is_low_energy in enumerate(low_energy + [False]):
        if is_low_energy and start is None:
            start = index
        elif not is_low_energy and start is not None:
            end = min(index, len(frame_times) - 1)
            t0, t1 = float(frame_times[start]), float(frame_times[end])
            if t1 - t0 >= minimum_seconds:
                intervals.append({"start_seconds": t0, "end_seconds": t1, "duration_seconds": t1 - t0})
            start = None
    return tuple(intervals)


_PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def strongest_pitch_candidates(
    salience: Sequence[float], midi_start: int = 36, *, count: int = 5
) -> tuple[PitchCandidate, ...]:
    """Return local CQT peaks as relative pitch evidence, not note transcription."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if len(salience) == 0:
        return ()

    peak_indices = [
        index
        for index, value in enumerate(salience)
        if value > 0
        and (index == 0 or value > salience[index - 1])
        and (index == len(salience) - 1 or value >= salience[index + 1])
    ]
    if not peak_indices:
        return ()

    maximum = max(float(salience[index]) for index in peak_indices)
    if maximum <= 0:
        return ()
    peak_indices.sort(key=lambda index: float(salience[index]), reverse=True)
    result = []
    for index in peak_indices[:count]:
        midi_note = midi_start + index
        note_name = f"{_PITCH_NAMES[midi_note % 12]}{midi_note // 12 - 1}"
        result.append(
            PitchCandidate(
                midi_note=midi_note,
                note_name=note_name,
                relative_strength=float(salience[index]) / maximum,
            )
        )
    return tuple(result)


def analyze_audio(
    path: Path,
    *,
    start_seconds: float = 0.0,
    duration_seconds: float | None = None,
    onset_merge_seconds: float = 0.09,
    chroma_window_seconds: float = 2.0,
    pitch_window_seconds: float = 0.25,
) -> AnalysisResult:
    """Measure a local audio file or a bounded passage using librosa."""
    try:
        import librosa
        import numpy as np
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError('Audio analysis requires: pip install -e ".[audio]"') from exc

    if not path.is_file():
        raise FileNotFoundError(path)
    if start_seconds < 0:
        raise ValueError("start_seconds cannot be negative")
    if duration_seconds is not None and duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if onset_merge_seconds < 0:
        raise ValueError("onset_merge_seconds cannot be negative")
    if chroma_window_seconds <= 0:
        raise ValueError("chroma_window_seconds must be positive")
    if pitch_window_seconds <= 0:
        raise ValueError("pitch_window_seconds must be positive")

    full_duration = float(librosa.get_duration(path=path))
    if start_seconds >= full_duration:
        raise ValueError("start_seconds is past the end of the recording")
    available = full_duration - start_seconds
    read_duration = min(duration_seconds, available) if duration_seconds is not None else available

    signal, sample_rate = librosa.load(
        path, sr=None, mono=True, offset=start_seconds, duration=read_duration
    )
    if signal.size == 0:
        raise ValueError("audio file contains no samples")

    hop_length = 512
    onset_envelope = librosa.onset.onset_strength(y=signal, sr=sample_rate, hop_length=hop_length)
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_envelope, sr=sample_rate, hop_length=hop_length
    )
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_envelope, sr=sample_rate, hop_length=hop_length
    )
    rms = librosa.feature.rms(y=signal, hop_length=hop_length)[0]
    centroid = librosa.feature.spectral_centroid(y=signal, sr=sample_rate, hop_length=hop_length)[0]
    chroma = librosa.feature.chroma_cqt(y=signal, sr=sample_rate, hop_length=hop_length)
    pitch_cqt = librosa.cqt(
        y=signal,
        sr=sample_rate,
        hop_length=hop_length,
        fmin=librosa.note_to_hz("C2"),
        n_bins=60,
        bins_per_octave=12,
    )

    local_onsets = tuple(float(v) for v in librosa.frames_to_time(onset_frames, sr=sample_rate, hop_length=hop_length))
    local_beats = tuple(float(v) for v in librosa.frames_to_time(beat_frames, sr=sample_rate, hop_length=hop_length))
    absolute_onsets = tuple(start_seconds + value for value in local_onsets)
    absolute_beats = tuple(start_seconds + value for value in local_beats)
    clusters = cluster_onsets(absolute_onsets, onset_merge_seconds)

    frames_per_window = max(1, round(chroma_window_seconds * sample_rate / hop_length))
    chroma_windows = tuple(
        TimeWindow(
            start_seconds=start_seconds + frame * hop_length / sample_rate,
            end_seconds=min(
                start_seconds + len(signal) / sample_rate,
                start_seconds + (frame + frames_per_window) * hop_length / sample_rate,
            ),
            values=tuple(float(value) for value in np.mean(chroma[:, frame : frame + frames_per_window], axis=1)),
        )
        for frame in range(0, chroma.shape[1], frames_per_window)
    )
    pitch_frames_per_window = max(1, round(pitch_window_seconds * sample_rate / hop_length))
    pitch_evidence_windows = tuple(
        PitchEvidenceWindow(
            start_seconds=start_seconds + frame * hop_length / sample_rate,
            end_seconds=min(
                start_seconds + len(signal) / sample_rate,
                start_seconds + (frame + pitch_frames_per_window) * hop_length / sample_rate,
            ),
            candidates=strongest_pitch_candidates(
                np.mean(
                    np.abs(pitch_cqt[:, frame : frame + pitch_frames_per_window]), axis=1
                ).tolist()
            ),
        )
        for frame in range(0, pitch_cqt.shape[1], pitch_frames_per_window)
    )
    frame_times = tuple(start_seconds + i * hop_length / sample_rate for i in range(len(rms) + 1))
    low_energy = _low_energy_intervals(
        rms,
        frame_times,
        threshold=float(np.max(rms)) * 0.08,
        minimum_seconds=0.2,
    )

    return AnalysisResult(
        source_path=str(path.resolve()),
        sample_rate=int(sample_rate),
        duration_seconds=full_duration,
        tempo_bpm=float(np.asarray(tempo).reshape(-1)[0]),
        beat_seconds=absolute_beats,
        onset_seconds=absolute_onsets,
        mean_rms=float(np.mean(rms)),
        peak_rms=float(np.max(rms)),
        mean_spectral_centroid_hz=float(np.mean(centroid)),
        mean_chroma=tuple(float(v) for v in np.mean(chroma, axis=1)),
        analyzed_start_seconds=start_seconds,
        analyzed_end_seconds=start_seconds + len(signal) / sample_rate,
        onset_clusters=clusters,
        onset_gaps=candidate_onset_gaps(clusters),
        beat_interval_windows=beat_interval_windows(absolute_beats, absolute_offset=0.0),
        chroma_windows=chroma_windows,
        pitch_evidence_windows=pitch_evidence_windows,
        low_energy_intervals=low_energy,
    )

