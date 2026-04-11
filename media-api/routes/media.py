"""Media extraction routes."""

import os

from flask import Blueprint, after_this_request, jsonify, request, send_file
from pydantic import ValidationError

from core.auth import require_api_key
from core.config import TMP_DIR
from routes.schemas import MediaExtractBody
from services import ytdlp

bp = Blueprint("media", __name__, url_prefix="/media")


def _schedule_delete(path: str) -> None:
    @after_this_request
    def _cleanup(response):
        if os.path.isfile(path):
            os.remove(path)
        return response


@bp.route("/extract", methods=["POST"])
@require_api_key
def extract():
    if not request.is_json:
        return jsonify({"detail": "Expected JSON body"}), 400

    try:
        body = MediaExtractBody.model_validate(request.get_json(silent=False))
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 400

    out_path = ytdlp.extract_audio(
        url=body.url,
        audio_format=body.format,
        quality=body.quality,
        clip_start=body.clip_start,
        clip_end=body.clip_end,
        tmp_dir=TMP_DIR,
    )

    try:
        _schedule_delete(out_path)
        return send_file(
            out_path,
            mimetype=ytdlp.mimetype_for_format(body.format),
            as_attachment=True,
            download_name=f"extract.{body.format}",
        )
    except Exception:
        if os.path.isfile(out_path):
            os.remove(out_path)
        raise
