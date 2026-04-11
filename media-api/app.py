"""Flask application entrypoint."""

import subprocess
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from core.config import MAX_UPLOAD_MB, TEMPLATES_DIR
from routes.audio import bp as audio_bp
from routes.media import bp as media_bp
from routes.pdf import bp as pdf_bp
from services.errors import ToolError


def _first_line_version(cmd: list[str]) -> str:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    text = (proc.stdout or proc.stderr or "").strip()
    if not text:
        return "unknown"
    return text.splitlines()[0].strip()


def _yt_dlp_version() -> str:
    return _first_line_version(["yt-dlp", "--version"])


def _ffmpeg_version() -> str:
    return _first_line_version(["ffmpeg", "-version"])


def _pandoc_version() -> str:
    return _first_line_version(["pandoc", "--version"])


def _typst_version() -> str:
    return _first_line_version(["typst", "--version"])


def _template_names() -> list[str]:
    base = Path(TEMPLATES_DIR)
    if not base.is_dir():
        return []
    return sorted(p.stem for p in base.glob("*.typ"))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

    app.register_blueprint(media_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(pdf_bp)

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "tools": {
                    "yt-dlp": _yt_dlp_version(),
                    "ffmpeg": _ffmpeg_version(),
                    "pandoc": _pandoc_version(),
                    "typst": _typst_version(),
                },
                "templates": _template_names(),
            },
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({"detail": exc.description or str(exc)}), exc.code

    @app.errorhandler(ValueError)
    def handle_value_error(exc):
        return jsonify({"detail": str(exc)}), 400

    @app.errorhandler(ToolError)
    def handle_tool_error(exc):
        return jsonify({"detail": str(exc)}), 500

    @app.errorhandler(Exception)
    def handle_generic_error(exc):
        return jsonify({"detail": str(exc)}), 500

    return app


app = create_app()
