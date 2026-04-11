"""Audio conversion routes."""

import os
import uuid
from pathlib import Path

from flask import Blueprint, after_this_request, jsonify, request, send_file
from werkzeug.utils import secure_filename

from core.auth import require_api_key
from core.config import TMP_DIR
from services import ffmpeg

bp = Blueprint("audio", __name__, url_prefix="/audio")


def _schedule_delete(path: str) -> None:
    @after_this_request
    def _cleanup(response):
        if os.path.isfile(path):
            os.remove(path)
        return response


def _parse_form_int(name: str, raw: str | None) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer") from None


@bp.route("/convert", methods=["POST"])
@require_api_key
def convert():
    if "file" not in request.files:
        return jsonify({"detail": "Missing file field"}), 400

    upload = request.files["file"]
    if upload.filename is None or upload.filename == "":
        return jsonify({"detail": "Empty file name"}), 400

    fmt = request.form.get("format", "mp3")
    bitrate = request.form.get("bitrate", "64k")

    sample_rate_raw = _parse_form_int(
        "sample_rate",
        request.form.get("sample_rate"),
    )
    channels_raw = _parse_form_int("channels", request.form.get("channels"))

    sample_rate = sample_rate_raw if sample_rate_raw is not None else 16000
    channels = channels_raw if channels_raw is not None else 1

    safe_name = secure_filename(upload.filename)
    suffix = Path(safe_name).suffix if safe_name else ""
    if suffix == "":
        suffix = ".bin"

    in_path = str(Path(TMP_DIR) / f"{uuid.uuid4()}-in{suffix}")
    upload.save(in_path)

    try:
        out_path = ffmpeg.convert_audio(
            input_path=in_path,
            output_format=fmt,
            bitrate=bitrate,
            sample_rate=sample_rate,
            channels=channels,
            tmp_dir=TMP_DIR,
        )
    finally:
        if os.path.isfile(in_path):
            os.remove(in_path)

    try:
        _schedule_delete(out_path)
        return send_file(
            out_path,
            mimetype=ffmpeg.mimetype_for_format(fmt),
            as_attachment=True,
            download_name=f"converted.{fmt}",
        )
    except Exception:
        if os.path.isfile(out_path):
            os.remove(out_path)
        raise
