"""Errors from CLI tool invocations."""


class ToolError(Exception):
    """Raised when a subprocess tool exits with a non-zero status."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"{tool_name} failed: {message}")
