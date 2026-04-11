"""Shared subprocess helpers."""

import subprocess

from services.errors import ToolError


def run_tool(tool_name: str, cmd: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc)).strip()
        raise ToolError(tool_name=tool_name, message=err) from exc


def run_tool_stdin(
    tool_name: str,
    cmd: list[str],
    input_text: str,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            input=input_text,
        )
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc)).strip()
        raise ToolError(tool_name=tool_name, message=err) from exc
