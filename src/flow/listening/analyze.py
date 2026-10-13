"""First-pass local audio measurement.

This module intentionally reports measurements, not musical intent. Later
stages may cite these timestamped values when proposing interpretations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


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
    analyzer: str = "flow-listening-baseline/0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def analyze_audio(path: Path) -> AnalysisResult:
    """Measure one local audio file using librosa.

    `librosa` is imported lazily so knowledge-model work and tests do not need
    the heavier audio dependency set.
    """

    try:
        import librosa
        import numpy as np
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError('Audio analysis requires: pip install -e ".[audio]"') from exc

    if not path.is_file():
        raise FileNotFoundError(path)

    signal, sample_rate = librosa.load(path, sr=None, mono=True)
    if signal.size == 0:
        raise ValueError("audio file contains no samples")

    onset_envelope = librosa.onset.onset_strength(y=signal, sr=sample_rate)
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_envelope, sr=sample_rate
    )
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_envelope, sr=sample_rate
    )
    rms = librosa.feature.rms(y=signal)[0]
    centroid = librosa.feature.spectral_centroid(y=signal, sr=sample_rate)[0]
    chroma = librosa.feature.chroma_cqt(y=signal, sr=sample_rate)

    return AnalysisResult(
        source_path=str(path.resolve()),
        sample_rate=int(sample_rate),
        duration_seconds=float(librosa.get_duration(y=signal, sr=sample_rate)),
        tempo_bpm=float(np.asarray(tempo).reshape(-1)[0]),
        beat_seconds=tuple(float(v) for v in librosa.frames_to_time(beat_frames, sr=sample_rate)),
        onset_seconds=tuple(
            float(v) for v in librosa.frames_to_time(onset_frames, sr=sample_rate)
        ),
        mean_rms=float(np.mean(rms)),
        peak_rms=float(np.max(rms)),
        mean_spectral_centroid_hz=float(np.mean(centroid)),
        mean_chroma=tuple(float(v) for v in np.mean(chroma, axis=1)),
    )

