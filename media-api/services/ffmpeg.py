"""ffmpeg audio conversion."""

import os
import uuid
from pathlib import Path

from services.runner import run_tool

_ALLOWED_FORMATS = frozenset({"mp3", "wav", "ogg", "m4a"})
_ALLOWED_BITRATES = frozenset({"32k", "64k", "128k", "192k"})


def convert_audio(
    *,
    input_path: str,
    output_format: str,
    bitrate: str,
    sample_rate: int,
    channels: int,
    tmp_dir: str,
) -> str:
    if output_format not in _ALLOWED_FORMATS:
        raise ValueError(
            f"format must be one of {sorted(_ALLOWED_FORMATS)}, got {output_format!r}"
        )
    if bitrate not in _ALLOWED_BITRATES:
        raise ValueError(
            f"bitrate must be one of {sorted(_ALLOWED_BITRATES)}, got {bitrate!r}"
        )
    if channels not in (1, 2):
        raise ValueError("channels must be 1 or 2")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    uid = str(uuid.uuid4())
    out_path = str(Path(tmp_dir) / f"{uid}.{output_format}")

    cmd: list[str] = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        input_path,
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
    ]

    if output_format == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
    elif output_format == "wav":
        cmd.extend(["-c:a", "pcm_s16le"])
    elif output_format == "ogg":
        cmd.extend(["-c:a", "libvorbis", "-b:a", bitrate])
    elif output_format == "m4a":
        cmd.extend(["-c:a", "aac", "-b:a", bitrate])

    cmd.append(out_path)

    run_tool(tool_name="ffmpeg", cmd=cmd)

    if not os.path.isfile(out_path):
        raise FileNotFoundError(f"ffmpeg did not produce output file: {out_path}")
    return out_path


def mimetype_for_format(output_format: str) -> str:
    mapping = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
    }
    return mapping[output_format]
