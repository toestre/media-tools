"""yt-dlp audio extraction."""

import glob
import os
import uuid
from pathlib import Path

from services.runner import run_tool

_ALLOWED_FORMATS = frozenset({"mp3", "wav", "m4a", "ogg"})


def extract_audio(
    *,
    url: str,
    audio_format: str,
    quality: int,
    clip_start: str | None,
    clip_end: str | None,
    tmp_dir: str,
) -> str:
    if audio_format not in _ALLOWED_FORMATS:
        raise ValueError(
            f"format must be one of {sorted(_ALLOWED_FORMATS)}, got {audio_format!r}"
        )
    if quality < 0 or quality > 9:
        raise ValueError("quality must be between 0 and 9")

    uid = str(uuid.uuid4())
    out_pattern = str(Path(tmp_dir) / f"{uid}.%(ext)s")

    cmd: list[str] = [
        "yt-dlp",
        "-x",
        "--audio-format",
        audio_format,
        "--audio-quality",
        str(quality),
        "-o",
        out_pattern,
        "--no-playlist",
        url,
    ]

    if clip_start is not None and clip_end is not None:
        cmd.extend(
            [
                "--postprocessor-args",
                f"ffmpeg:-ss {clip_start} -to {clip_end}",
            ]
        )
    elif clip_start is not None or clip_end is not None:
        raise ValueError("clip_start and clip_end must both be set or both omitted")

    run_tool(tool_name="yt-dlp", cmd=cmd)

    matches = sorted(glob.glob(str(Path(tmp_dir) / f"{uid}.*")))
    if not matches:
        raise FileNotFoundError(f"yt-dlp produced no output file for prefix {uid}")
    path = matches[0]
    if not os.path.isfile(path):
        raise FileNotFoundError(f"expected file missing after yt-dlp: {path}")
    return path


def mimetype_for_format(audio_format: str) -> str:
    mapping = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
    }
    return mapping[audio_format]
