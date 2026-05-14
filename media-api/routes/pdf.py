"""PDF rendering routes."""

import os
from pathlib import Path

from flask import Blueprint, after_this_request, jsonify, request, send_file
from pydantic import ValidationError

from core.auth import require_api_key
from core.config import TEMPLATES_DIR, TMP_DIR
from routes.schemas import PdfRenderBody
from services import pandoc
from services.ytdlp import sanitize_download_stem

bp = Blueprint("pdf", __name__, url_prefix="/pdf")


def _schedule_delete(path: str) -> None:
    @after_this_request
    def _cleanup(response):
        if os.path.isfile(path):
            os.remove(path)
        return response


def _pdf_attachment_name(explicit_basename: str | None) -> str:
    if explicit_basename is None:
        return "document.pdf"
    base = Path(explicit_basename).name
    stem_part = Path(base).stem if base else ""
    stem = sanitize_download_stem(stem_part, max_length=180)
    return f"{stem}.pdf"


def _list_template_names() -> list[str]:
    base = Path(TEMPLATES_DIR)
    if not base.is_dir():
        return []
    return sorted(p.stem for p in base.glob("*.typ"))


@bp.route("/render", methods=["POST"])
@require_api_key
def render():
    if not request.is_json:
        return jsonify({"detail": "Expected JSON body"}), 400

    try:
        body = PdfRenderBody.model_validate(request.get_json(silent=False))
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 400

    template_path = Path(TEMPLATES_DIR) / f"{body.template}.typ"
    if not template_path.is_file():
        return jsonify(
            {
                "detail": (
                    f"Unknown template {body.template!r}; "
                    f"available: {_list_template_names()}"
                ),
            },
        ), 400

    meta = body.metadata
    metadata_dict: dict[str, str] = {}
    if meta.title is not None:
        metadata_dict["title"] = meta.title
    if meta.author is not None:
        metadata_dict["author"] = meta.author
    if meta.date is not None:
        metadata_dict["date"] = meta.date

    out_path = pandoc.render_markdown_to_pdf(
        markdown_body=body.markdown,
        template_name=body.template,
        papersize=body.paper,
        margin_mm=body.margin_mm,
        font=body.font,
        toc=body.toc,
        metadata=metadata_dict,
        templates_dir=TEMPLATES_DIR,
        tmp_dir=TMP_DIR,
    )

    download_name = _pdf_attachment_name(body.filename)

    try:
        _schedule_delete(out_path)
        return send_file(
            out_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name,
        )
    except Exception:
        if os.path.isfile(out_path):
            os.remove(out_path)
        raise
