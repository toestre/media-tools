"""Request body models."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MediaExtractBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    format: str = Field(default="mp3")
    quality: int = Field(default=5)
    clip_start: str | None = Field(default=None)
    clip_end: str | None = Field(default=None)

    @field_validator("url")
    @classmethod
    def url_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("url must not be empty")
        return value


class PdfMetadataBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None)
    author: str | None = Field(default=None)
    date: str | None = Field(default=None)


class PdfRenderBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str
    template: str = Field(default="default")
    paper: str = Field(default="a4")
    margin_mm: int = Field(default=25)
    font: str = Field(default="Source Serif Pro")
    toc: bool = Field(default=False)
    metadata: PdfMetadataBody = Field(default_factory=PdfMetadataBody)

    @field_validator("markdown")
    @classmethod
    def markdown_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("markdown must not be empty")
        return value
