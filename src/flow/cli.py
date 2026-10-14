"""Command-line entry point for the Flow Listening Lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flow.composer import beethoven_opening_recipe
from flow.listening.benchmark import compare_analysis_to_score
from flow.listening.onset_review import inspect_onset_pitch_evidence
from flow.listening import analyze_audio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flow")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="measure a local audio file")
    analyze.add_argument("audio", type=Path)
    analyze.add_argument("--out", type=Path, default=Path("analysis.json"))
    analyze.add_argument("--start", type=float, default=0.0, help="passage start in seconds")
    analyze.add_argument(
        "--duration", type=float, help="passage duration in seconds (default: remainder of file)"
    )
    analyze.add_argument(
        "--pitch-window",
        type=float,
        default=0.25,
        help="pitch-evidence window in seconds (relative candidates, not transcription)",
    )

    compare = commands.add_parser(
        "compare-score", help="compare saved audio evidence with a separate score reference"
    )
    compare.add_argument("analysis", type=Path, help="JSON output from flow analyze")
    compare.add_argument(
        "--reference",
        type=Path,
        default=Path("examples/beethoven5/score_reference.json"),
    )
    compare.add_argument("--out", type=Path, default=Path("score-comparison.json"))
    compare.add_argument("--minimum-strength", type=float, default=0.3)

    onset_review = commands.add_parser(
        "inspect-onsets", help="pair saved onset clusters with nearby pitch evidence"
    )
    onset_review.add_argument("analysis", type=Path, help="JSON output from flow analyze")
    onset_review.add_argument("--out", type=Path, default=Path("onset-pitch-review.json"))
    onset_review.add_argument("--before", type=float, default=0.1, help="seconds before each onset")
    onset_review.add_argument("--after", type=float, default=0.3, help="seconds after each onset")

    seed = commands.add_parser(
        "init-beethoven", help="write the score-informed opening motif recipe"
    )
    seed.add_argument(
        "--out", type=Path, default=Path("beethoven-opening.recipe.json")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        result = analyze_audio(
            args.audio,
            start_seconds=args.start,
            duration_seconds=args.duration,
            pitch_window_seconds=args.pitch_window,
        )
        result.write_json(args.out)
        print(f"Wrote measurements to {args.out}")
        return 0
    if args.command == "init-beethoven":
        beethoven_opening_recipe().write_json(args.out)
        print(f"Wrote benchmark recipe to {args.out}")
        return 0
    if args.command == "compare-score":
        analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        result = compare_analysis_to_score(
            analysis, reference, minimum_strength=args.minimum_strength
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        status = "found" if result["ordered_pitch_class_sequence_found"] else "not found"
        print(f"Ordered pitch-class sequence {status}; wrote comparison to {args.out}")
        return 0
    if args.command == "inspect-onsets":
        analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
        result = inspect_onset_pitch_evidence(
            analysis, before_seconds=args.before, after_seconds=args.after
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Reviewed {result['onset_count']} onset clusters; wrote {args.out}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

