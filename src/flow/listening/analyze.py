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
class TimbreEvidenceWindow:
    start_seconds: float
    end_seconds: float
    spectral_centroid_hz: float
    spectral_bandwidth_hz: float
    spectral_flatness: float
    rolloff_85_hz: float
    relative_band_energy: dict[str, float]
    onset_strength_mean: float
    onset_strength_peak: float
    candidate_harmonic_profiles: tuple[dict[str, Any], ...]


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
    timbre_evidence_windows: tuple[TimbreEvidenceWindow, ...]
    low_energy_intervals: tuple[dict[str, float], ...]
    analyzer: str = "flow-listening-passage/0.5"

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


def spectral_timbre_features(
    magnitude: Any,
    sample_rate: int,
    midi_notes: Sequence[int] = (),
    onset_strength: Sequence[float] = (),
) -> dict[str, Any]:
    """Summarize mixture timbre and candidate-note harmonic shape for one window.

    These are acoustic descriptors, not instrument labels. Harmonic profiles
    can contain energy from other notes or instruments in the same mixture.
    """
    import numpy as np

    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    spectrum = np.asarray(magnitude, dtype=float)
    if spectrum.ndim == 2:
        spectrum = np.mean(spectrum, axis=1)
    if spectrum.ndim != 1 or spectrum.size == 0:
        raise ValueError("magnitude must be a non-empty 1D spectrum or 2D spectrogram")
    spectrum = np.maximum(spectrum, 0.0)
    epsilon = float(np.finfo(float).eps)
    onset_values = np.asarray(onset_strength, dtype=float)
    frequencies = np.linspace(0.0, sample_rate / 2.0, spectrum.size)
    total_magnitude = float(np.sum(spectrum))
    total_power = float(np.sum(spectrum**2))
    if total_magnitude <= epsilon:
        return {
            "spectral_centroid_hz": 0.0,
            "spectral_bandwidth_hz": 0.0,
            "spectral_flatness": 0.0,
            "rolloff_85_hz": 0.0,
            "relative_band_energy": {name: 0.0 for name, _, _ in _SPECTRAL_BANDS},
            "onset_strength_mean": float(np.mean(onset_values)) if onset_values.size else 0.0,
            "onset_strength_peak": float(np.max(onset_values)) if onset_values.size else 0.0,
            "candidate_harmonic_profiles": (),
        }

    centroid = float(np.sum(frequencies * spectrum) / total_magnitude)
    bandwidth = float(
        np.sqrt(np.sum(((frequencies - centroid) ** 2) * spectrum) / total_magnitude)
    )
    flatness = float(np.exp(np.mean(np.log(spectrum + epsilon))) / (np.mean(spectrum) + epsilon))
    cumulative_power = np.cumsum(spectrum**2)
    rolloff_index = int(np.searchsorted(cumulative_power, 0.85 * total_power, side="left"))
    rolloff = float(frequencies[min(rolloff_index, frequencies.size - 1)])

    relative_band_energy = {}
    for name, lower_hz, upper_hz in _SPECTRAL_BANDS:
        selected = (frequencies >= lower_hz) & (frequencies < upper_hz)
        relative_band_energy[name] = (
            float(np.sum(spectrum[selected] ** 2) / total_power) if total_power > epsilon else 0.0
        )

    bin_width = sample_rate / (2.0 * (spectrum.size - 1)) if spectrum.size > 1 else sample_rate
    harmonic_profiles = []
    for midi_note in midi_notes:
        fundamental_hz = 440.0 * 2.0 ** ((int(midi_note) - 69) / 12.0)
        harmonic_power = []
        for harmonic in range(1, 9):
            target_hz = fundamental_hz * harmonic
            if target_hz >= sample_rate / 2.0:
                break
            center = int(round(target_hz / bin_width))
            radius = max(1, int(round(target_hz * 0.01 / bin_width)))
            left = max(0, center - radius)
            right = min(spectrum.size, center + radius + 1)
            harmonic_power.append(float(np.max(spectrum[left:right]) ** 2))
        profile_total = sum(harmonic_power)
        odd_power = sum(harmonic_power[::2])
        even_power = sum(harmonic_power[1::2])
        harmonic_profiles.append(
            {
                "midi_note": int(midi_note),
                "fundamental_hz": fundamental_hz,
                "harmonic_energy_ratios": (
                    [value / profile_total for value in harmonic_power]
                    if profile_total > epsilon
                    else []
                ),
                "odd_to_even_harmonic_energy_ratio": (
                    odd_power / max(even_power, epsilon) if odd_power > 0 else 0.0
                ),
            }
        )

    return {
        "spectral_centroid_hz": centroid,
        "spectral_bandwidth_hz": bandwidth,
        "spectral_flatness": flatness,
        "rolloff_85_hz": rolloff,
        "relative_band_energy": relative_band_energy,
        "onset_strength_mean": float(np.mean(onset_values)) if onset_values.size else 0.0,
        "onset_strength_peak": float(np.max(onset_values)) if onset_values.size else 0.0,
        "candidate_harmonic_profiles": tuple(harmonic_profiles),
    }


_SPECTRAL_BANDS = (
    ("0_125_hz", 0.0, 125.0),
    ("125_250_hz", 125.0, 250.0),
    ("250_500_hz", 250.0, 500.0),
    ("500_1k_hz", 500.0, 1000.0),
    ("1k_2k_hz", 1000.0, 2000.0),
    ("2k_4k_hz", 2000.0, 4000.0),
    ("4k_8k_hz", 4000.0, 8000.0),
    ("above_8k_hz", 8000.0, float("inf")),
)


def _window_frame_ranges(
    frame_count: int, window_frames: int, hop_frames: int
) -> tuple[tuple[int, int], ...]:
    """Return overlapping analysis windows, retaining a final partial window."""
    if frame_count < 0:
        raise ValueError("frame_count cannot be negative")
    if window_frames < 1:
        raise ValueError("window_frames must be positive")
    if hop_frames < 1:
        raise ValueError("hop_frames must be positive")
    return tuple(
        (start, min(frame_count, start + window_frames))
        for start in range(0, frame_count, hop_frames)
    )


def analyze_audio(
    path: Path,
    *,
    start_seconds: float = 0.0,
    duration_seconds: float | None = None,
    onset_merge_seconds: float = 0.09,
    chroma_window_seconds: float = 2.0,
    pitch_window_seconds: float = 0.25,
    pitch_hop_seconds: float = 0.05,
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
    if pitch_hop_seconds <= 0:
        raise ValueError("pitch_hop_seconds must be positive")

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
    pitch_frames_per_hop = max(1, round(pitch_hop_seconds * sample_rate / hop_length))
    pitch_evidence_windows = tuple(
        PitchEvidenceWindow(
            start_seconds=start_seconds + frame_start * hop_length / sample_rate,
            end_seconds=min(
                start_seconds + len(signal) / sample_rate,
                start_seconds + frame_end * hop_length / sample_rate,
            ),
            candidates=strongest_pitch_candidates(
                np.mean(
                    np.abs(pitch_cqt[:, frame_start:frame_end]), axis=1
                ).tolist()
            ),
        )
        for frame_start, frame_end in _window_frame_ranges(
            pitch_cqt.shape[1], pitch_frames_per_window, pitch_frames_per_hop
        )
    )
    timbre_n_fft = 4096
    timbre_magnitude = np.abs(
        librosa.stft(signal, n_fft=timbre_n_fft, hop_length=hop_length)
    )
    timbre_evidence_windows = tuple(
        TimbreEvidenceWindow(
            start_seconds=start_seconds + frame_start * hop_length / sample_rate,
            end_seconds=min(
                start_seconds + len(signal) / sample_rate,
                start_seconds + frame_end * hop_length / sample_rate,
            ),
            **spectral_timbre_features(
                timbre_magnitude[:, frame_start:frame_end],
                int(sample_rate),
                [candidate.midi_note for candidate in pitch_evidence_windows[index].candidates],
                onset_envelope[frame_start : min(frame_end, len(onset_envelope))],
            ),
        )
        for index, (frame_start, frame_end) in enumerate(
            _window_frame_ranges(
                timbre_magnitude.shape[1], pitch_frames_per_window, pitch_frames_per_hop
            )
        )
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
        timbre_evidence_windows=timbre_evidence_windows,
        low_energy_intervals=low_energy,
    )

