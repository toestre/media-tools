# media-tools

A lightweight REST API (Flask + Gunicorn) that wraps CLI media tools in a Docker container. Designed to be called from an [n8n](https://n8n.io/) container over an internal Docker network.

**Wrapped tools:** yt-dlp · ffmpeg · Pandoc · Typst

Docker image: `ghcr.io/toestre/media-tools`

## Endpoints

### `GET /health`

Returns service status, tool versions, and available Typst templates.

```json
{
  "status": "ok",
  "tools": {
    "yt-dlp": "2024.x.x",
    "ffmpeg": "6.x",
    "pandoc": "3.x",
    "typst": "0.x"
  },
  "templates": ["default"]
}
```

---

### `POST /media/extract`

Extracts the audio track from a media URL via yt-dlp.

**Request (JSON):**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string | yes | – | Media URL (YouTube etc.) |
| `format` | string | no | `mp3` | Output format: `mp3`, `wav`, `m4a`, `ogg` |
| `quality` | int | no | `5` | yt-dlp quality 0 (best) – 9 (worst) |
| `clip_start` | string | no | – | Start time `hh:mm:ss` |
| `clip_end` | string | no | – | End time `hh:mm:ss` |

**Response:** Audio file download.

---

### `POST /audio/convert`

Converts or downsamples an audio file via ffmpeg.

**Request:** `multipart/form-data`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `file` | file | yes | – | Audio file upload |
| `format` | string | no | `mp3` | Output format: `mp3`, `wav`, `ogg`, `m4a` |
| `bitrate` | string | no | `64k` | Bitrate: `32k`, `64k`, `128k`, `192k` |
| `sample_rate` | int | no | `16000` | Sample rate in Hz (e.g. `16000` for Whisper) |
| `channels` | int | no | `1` | `1` (mono) or `2` (stereo) |

**Response:** Converted audio file download.

---

### `POST /pdf/render`

Renders a Markdown document to PDF via Pandoc and Typst.

**Request (JSON):**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `markdown` | string | yes | – | Markdown content |
| `template` | string | no | `default` | Typst template name |
| `paper` | string | no | `a4` | Paper size: `a4`, `a5`, `letter` |
| `margin_mm` | int | no | `25` | Page margin in mm |
| `font` | string | no | `Source Serif Pro` | Typst font name |
| `toc` | bool | no | `false` | Generate table of contents |
| `metadata` | object | no | `{}` | `title`, `author`, `date` |

**Response:** PDF file download.

## Authentication

All endpoints are protected by an optional API key. Set the `API_KEY` environment variable and pass the key via the `X-API-Key` request header. If `API_KEY` is not set, authentication is skipped (useful for local development).

## Configuration

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | `""` | Empty string disables auth |
| `TMP_DIR` | `/tmp` | Temporary file directory |
| `TEMPLATES_DIR` | `/templates` | Typst template directory |
| `FONTS_DIR` | `/fonts` | Font directory (`TYPST_FONT_PATHS`) |
| `MAX_UPLOAD_MB` | `100` | Maximum upload size |
| `WORKERS` | `2` | Gunicorn worker count |

## Local Development

```bash
cd media-api
docker compose up --build
```

The API will be available at `http://localhost:3000`. The compose file sets `API_KEY=dev-secret`.

## CI / Docker Image

The image is built and pushed to the GitHub Container Registry on every push to `main` and on version tags (`v*.*.*`):

```
ghcr.io/toestre/media-tools:latest
ghcr.io/toestre/media-tools:v1.0.0
```
