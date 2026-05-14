"""
Curated built-in ambient sound library.

Each preset is a short, looped texture synthesized with FFmpeg's
`anoisesrc` / `sine` generators. They are intentionally subtle —
grounded, lived-in textures meant to sit far beneath the narration.

The clips are generated once on application startup and cached on
local disk. They are intentionally not stored in object storage
because they are stateless, deterministic, and shipped with the app.
"""
from __future__ import annotations

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

AMBIENT_DIR = Path(__file__).parent / "static" / "ambient"

# Each entry: ffmpeg lavfi description for a 60-second seamless loop.
# Volumes are kept low (0.04–0.12) because ambient should never assert
# itself over narration.
PRESETS: List[Dict] = [
    {
        "key": "room_tone",
        "label": "Room tone — interior stillness",
        "description": "The quiet hum of an empty room. Barely there.",
        "filter": "anoisesrc=d=60:c=brown:a=0.05,lowpass=f=240",
    },
    {
        "key": "wind",
        "label": "Wind — distant, open",
        "description": "Sparse air movement across an open landscape.",
        "filter": "anoisesrc=d=60:c=pink:a=0.10,bandpass=f=320:w=240",
    },
    {
        "key": "rain",
        "label": "Rain — steady, soft",
        "description": "A consistent, unhurried rainfall.",
        "filter": "anoisesrc=d=60:c=white:a=0.10,highpass=f=1800",
    },
    {
        "key": "forest",
        "label": "Forest — sparse foliage",
        "description": "A breathing forest, no distractions.",
        "filter": "anoisesrc=d=60:c=pink:a=0.07,highpass=f=420,lowpass=f=4200",
    },
    {
        "key": "drone",
        "label": "Drone — subterranean tone",
        "description": "A slow, low harmonic bed.",
        "filter": "sine=f=72:d=60,volume=0.10",
    },
    {
        "key": "paper",
        "label": "Paper — handled archive",
        "description": "Soft, dry textures. Pages, fabric, breath.",
        "filter": "anoisesrc=d=60:c=white:a=0.04,lowpass=f=3000",
    },
]


def _generate(preset: Dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-f", "lavfi",
        "-i", preset["filter"],
        "-ac", "2",
        "-ar", "44100",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(target),
    ]
    subprocess.run(cmd, check=True)


def ensure_ambient_assets() -> None:
    """Generate every preset on disk if it does not yet exist."""
    AMBIENT_DIR.mkdir(parents=True, exist_ok=True)
    for preset in PRESETS:
        target = AMBIENT_DIR / f"{preset['key']}.mp3"
        if not target.exists():
            try:
                _generate(preset, target)
                logger.info("Generated ambient preset: %s", preset["key"])
            except Exception as e:  # noqa: BLE001
                logger.warning("Could not generate %s: %s", preset["key"], e)


def list_presets() -> List[Dict]:
    return [
        {
            "key": p["key"],
            "label": p["label"],
            "description": p["description"],
        }
        for p in PRESETS
    ]


def preset_path(key: str) -> Path | None:
    target = AMBIENT_DIR / f"{key}.mp3"
    return target if target.exists() else None
