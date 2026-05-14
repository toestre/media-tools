"""yt-dlp audio extraction."""

import glob
import json
import os
import uuid
from pathlib import Path

from services.runner import run_tool

_ALLOWED_FORMATS = frozenset({"mp3", "wav", "m4a", "ogg"})


def sanitize_download_stem(raw: str, *, max_length: int) -> str:
    """Turn arbitrary text into a single path segment (no slashes)."""
    s = raw.strip()
    for char in '<>:"/\\|?*\x00':
        s = s.replace(char, "_")
    s = s.strip(" ._")
    if not s:
        return "extract"
    if len(s) > max_length:
        s = s[:max_length].rstrip(" ._")
    if not s:
        return "extract"
    return s


def fetch_video_title(*, url: str) -> str:
    """Return the video title from yt-dlp metadata (no download)."""
    cmd = ["yt-dlp", "-j", "--skip-download", "--no-playlist", url]
    result = run_tool(tool_name="yt-dlp", cmd=cmd)
    raw = (result.stdout or "").strip()
    if not raw:
        raise ValueError("yt-dlp returned empty metadata for title resolution")
    first_line = raw.splitlines()[0]
    try:
        data = json.loads(first_line)
    except json.JSONDecodeError as exc:
        raise ValueError("yt-dlp metadata was not valid JSON") from exc
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("video metadata contained no title")
    return title


def resolve_extract_download_name(
    *,
    explicit_filename: str | None,
    url: str,
    audio_format: str,
) -> str:
    """Attachment filename for /media/extract (stem sanitized, extension from format)."""
    max_stem_length = 180
    if explicit_filename is not None:
        base = Path(explicit_filename).name
        stem_part = Path(base).stem if base else ""
        stem = sanitize_download_stem(stem_part, max_length=max_stem_length)
        return f"{stem}.{audio_format}"
    title = fetch_video_title(url=url)
    stem = sanitize_download_stem(title, max_length=max_stem_length)
    return f"{stem}.{audio_format}"


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
