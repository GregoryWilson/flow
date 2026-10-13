"""Command-line entry point for the Flow Listening Lab."""

from __future__ import annotations

import argparse
from pathlib import Path

from flow.composer import beethoven_opening_recipe
from flow.listening import analyze_audio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flow")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="measure a local audio file")
    analyze.add_argument("audio", type=Path)
    analyze.add_argument("--out", type=Path, default=Path("analysis.json"))

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
        result = analyze_audio(args.audio)
        result.write_json(args.out)
        print(f"Wrote measurements to {args.out}")
        return 0
    if args.command == "init-beethoven":
        beethoven_opening_recipe().write_json(args.out)
        print(f"Wrote benchmark recipe to {args.out}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

