"""Pandoc + Typst PDF rendering."""

import os
import uuid
from pathlib import Path

from services.runner import run_tool_stdin

_ALLOWED_PAPER = frozenset({"a4", "a5", "letter"})


def _resolve_table_filter_path() -> Path:
    env_path = os.getenv("PANDOC_TABLE_FILTER")
    if env_path:
        candidate = Path(env_path)
    else:
        candidate = Path(__file__).resolve().parent.parent / "filters" / "table-widths.lua"

    if not candidate.is_file():
        raise FileNotFoundError(f"pandoc table filter not found: {candidate}")
    return candidate


def _resolve_typst_font_name(requested: str) -> str:
    aliases = {
        "libertinus": "Libertinus Serif",
        "source": "Source Serif Pro",
        "source-serif": "Source Serif Pro",
    }
    key = requested.strip().lower()
    if key in aliases:
        return aliases[key]
    return requested


def _yaml_escape_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _build_frontmatter_lines(
    *,
    metadata: dict[str, str],
    toc: bool,
    papersize: str,
    mainfont: str,
    margin_mm: int,
) -> list[str]:
    lines: list[str] = ["---"]
    title = metadata.get("title")
    if title is not None:
        lines.append(f"title: {_yaml_escape_scalar(title)}")
    author = metadata.get("author")
    if author is not None:
        lines.append(f"author: {_yaml_escape_scalar(author)}")
    date = metadata.get("date")
    if date is not None:
        lines.append(f"date: {_yaml_escape_scalar(date)}")
    lines.append(f"toc: {str(toc).lower()}")
    lines.append(f"papersize: {_yaml_escape_scalar(papersize)}")
    lines.append(f"mainfont: {_yaml_escape_scalar(mainfont)}")
    lines.append("margin:")
    for side in ("left", "right", "top", "bottom"):
        lines.append(f"  {side}: {margin_mm}mm")
    lines.append("---")
    return lines


def render_markdown_to_pdf(
    *,
    markdown_body: str,
    template_name: str,
    papersize: str,
    margin_mm: int,
    font: str,
    toc: bool,
    metadata: dict[str, str],
    templates_dir: str,
    tmp_dir: str,
) -> str:
    if papersize not in _ALLOWED_PAPER:
        raise ValueError(
            f"paper must be one of {sorted(_ALLOWED_PAPER)}, got {papersize!r}"
        )
    if margin_mm <= 0:
        raise ValueError("margin_mm must be positive")

    template_path = Path(templates_dir) / f"{template_name}.typ"
    if not template_path.is_file():
        raise FileNotFoundError(f"template not found: {template_name}")

    mainfont = _resolve_typst_font_name(font)
    fm = "\n".join(
        _build_frontmatter_lines(
            metadata=metadata,
            toc=toc,
            papersize=papersize,
            mainfont=mainfont,
            margin_mm=margin_mm,
        )
    )
    full_markdown = fm + "\n\n" + markdown_body

    uid = str(uuid.uuid4())
    pdf_path = str(Path(tmp_dir) / f"{uid}.pdf")

    cmd: list[str] = [
        "pandoc",
        "-f",
        "markdown",
        "-t",
        "typst",
        "--pdf-engine=typst",
        f"--template={template_path}",
        f"--lua-filter={_resolve_table_filter_path()}",
        "-o",
        pdf_path,
        "-",
    ]

    run_tool_stdin(
        tool_name="pandoc",
        cmd=cmd,
        input_text=full_markdown,
    )

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"pandoc did not produce PDF: {pdf_path}")
    return pdf_path
