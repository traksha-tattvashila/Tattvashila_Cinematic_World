"""
CLI entrypoint for the Tattvashila cinematic pipeline.

Usage:
    python -m pipeline render <config.json> [--output out.mp4]

The config file mirrors `RenderContext` but with string paths.
This makes the same engine usable from the web server or a shell.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .renderer import (
    AmbientSpec,
    GradingSpec,
    NarrationSpec,
    RenderContext,
    SegmentSpec,
    render_project,
)


def _load_context(config_path: Path) -> RenderContext:
    data = json.loads(config_path.read_text())
    segments = [
        SegmentSpec(
            kind=s.get("kind", "clip"),
            duration=float(s.get("duration", 6.0)),
            source_path=Path(s["source_path"]) if s.get("source_path") else None,
            start_offset=float(s.get("start_offset", 0.0)),
            transition_in=s.get("transition_in", "fade"),
            transition_in_duration=float(s.get("transition_in_duration", 1.5)),
        )
        for s in data.get("segments", [])
    ]
    grading = GradingSpec(**data.get("grading", {}))
    narration = NarrationSpec(
        path=Path(data["narration"]["path"]) if data.get("narration", {}).get("path") else None,
        offset_seconds=float(data.get("narration", {}).get("offset_seconds", 1.5)),
        volume=float(data.get("narration", {}).get("volume", 1.0)),
    )
    ambient = AmbientSpec(
        path=Path(data["ambient"]["path"]) if data.get("ambient", {}).get("path") else None,
        volume=float(data.get("ambient", {}).get("volume", 0.3)),
        fade_in=float(data.get("ambient", {}).get("fade_in", 3.0)),
        fade_out=float(data.get("ambient", {}).get("fade_out", 4.0)),
    )
    return RenderContext(
        segments=segments,
        grading=grading,
        narration=narration,
        ambient=ambient,
        width=int(data.get("width", 1920)),
        height=int(data.get("height", 1080)),
        fps=int(data.get("fps", 24)),
        video_bitrate=data.get("video_bitrate", "6000k"),
        audio_bitrate=data.get("audio_bitrate", "192k"),
        output_path=Path(data.get("output_path", "out.mp4")),
    )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s — %(message)s")

    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="Render a project from a JSON config")
    r.add_argument("config", type=Path)
    r.add_argument("--output", type=Path, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "render":
        ctx = _load_context(args.config)
        if args.output:
            ctx.output_path = args.output

        def _on_progress(pct: float, stage: str) -> None:
            print(f"[{int(pct * 100):>3}%] {stage}", flush=True)

        ctx.progress_cb = _on_progress
        out = render_project(ctx)
        print(f"Rendered → {out}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
