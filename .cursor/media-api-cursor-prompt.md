# Cursor Prompt: Media Tools API – Docker Image

## Kontext

Baue eine schlanke REST-API in Python (Flask + Gunicorn), die als Docker-Container läuft und folgende CLI-Tools kapselt:

- **yt-dlp** – Audio aus YouTube- und anderen Medien-URLs extrahieren
- **ffmpeg** – Audiodateien konvertieren und downsamplen
- **Pandoc + Typst** – Markdown-Dokumente zu PDF rendern

Die API wird von einem n8n-Container im selben Docker-Netzwerk über HTTP aufgerufen. Sie ist **nicht** direkt aus dem Internet erreichbar.

---

## Projektstruktur

Erstelle folgende Dateistruktur:

```
media-api/
├── Dockerfile
├── docker-compose.yml        # Nur für lokales Testing
├── requirements.txt
├── app.py                    # Flask-App, Blueprints registrieren
├── routes/
│   ├── __init__.py
│   ├── media.py              # /media/extract
│   ├── audio.py              # /audio/convert
│   └── pdf.py                # /pdf/render
├── services/
│   ├── __init__.py
│   ├── ytdlp.py
│   ├── ffmpeg.py
│   └── pandoc.py
├── core/
│   ├── __init__.py
│   ├── config.py             # Einstellungen via Umgebungsvariablen
│   └── auth.py               # API-Key-Prüfung
├── fonts/                    # Werden ins Image eingebettet → /fonts/
│   └── (Schriftdateien .ttf/.otf)
└── templates/                # Werden ins Image eingebettet → /templates/
    └── default.typ           # Standard-Typst-Template
```

---

## Dockerfile

Orientiere dich am folgenden Aufbau – er entspricht dem bereits vorhandenen PDF-Image und soll konsistent bleiben:

```dockerfile
FROM python:3.13-alpine AS base

# System-Tools
RUN apk add --no-cache ffmpeg pandoc curl

# Typst installieren (musl-Binary für Alpine)
ARG TYPST_VERSION=0.13.1
RUN curl -fsSL "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" \
    | tar -xJ --strip-components=1 -C /usr/local/bin/ "typst-x86_64-unknown-linux-musl/typst" \
    && chmod +x /usr/local/bin/typst \
    && apk del curl

# yt-dlp installieren
RUN pip install --no-cache-dir yt-dlp

# Python-Dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Verzeichnisse anlegen
ENV TYPST_FONT_PATHS=/fonts
ENV PYTHONUNBUFFERED=1
RUN mkdir -p /fonts /templates /app

# Fonts und Templates ins Image einbetten
COPY fonts/     /fonts/
COPY templates/ /templates/

# App
COPY app.py routes/ services/ core/ /app/
WORKDIR /app

EXPOSE 3000
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "app:app"]
```

**Hinweise zum Dockerfile:**
- `curl` wird nach der Typst-Installation wieder entfernt (`apk del curl`), um die Image-Größe zu reduzieren
- yt-dlp wird als normales pip-Package installiert (kein `--break-system-packages` nötig bei Alpine + python-Image)
- `TYPST_FONT_PATHS=/fonts` sorgt dafür, dass Typst die eingebetteten Fonts findet, ohne dass Pandoc den Pfad explizit übergeben muss
- Das `fonts/`-Verzeichnis im Repo enthält die gewünschten `.ttf`/`.otf`-Dateien; das `templates/`-Verzeichnis enthält mindestens `default.typ`
- Gunicorn `--timeout 120` ist wichtig: yt-dlp-Downloads können bei längeren Videos mehrere Sekunden dauern – der Default von 30s kann zu früh abbrechen

---

## requirements.txt

```
flask
gunicorn
```

---

## API Endpoints

### GET /health

Gibt den Status, die Versionen aller Tools und die verfügbaren Templates zurück.

**Response (JSON):**
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

Versionen per `subprocess.run(["tool", "--version"], ...)` ermitteln. Templates durch Auflisten von `*.typ`-Dateien in `TEMPLATES_DIR`.

---

### POST /media/extract

Extrahiert die Audiospur einer Medien-URL via yt-dlp.

**Request (JSON):**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "format": "mp3",
  "quality": 5,
  "clip_start": "00:01:30",
  "clip_end": "00:03:00"
}
```

**Parameter:**
| Feld | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `url` | string | ja | – | Medien-URL (YouTube etc.) |
| `format` | string | nein | `mp3` | Zielformat: `mp3`, `wav`, `m4a`, `ogg` |
| `quality` | int | nein | `5` | yt-dlp Qualität 0 (best) – 9 (worst) |
| `clip_start` | string | nein | – | Startzeit `hh:mm:ss` |
| `clip_end` | string | nein | – | Endzeit `hh:mm:ss` |

**Response:** Audiodatei via `send_file()` mit passendem `mimetype`.

**Implementierungshinweise:**
- Ausgabedatei in `/tmp/` mit UUID als Dateinamen anlegen
- yt-dlp-Argumente: `-x`, `--audio-format`, `--audio-quality`, ggf. `--postprocessor-args` für Clip via ffmpeg
- Datei nach dem Senden mit `@after_this_request` löschen

---

### POST /audio/convert

Konvertiert oder downsampled eine Audiodatei via ffmpeg.

**Request:** `multipart/form-data`

| Feld | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `file` | UploadFile | ja | – | Audiodatei |
| `format` | string | nein | `mp3` | Zielformat: `mp3`, `wav`, `ogg`, `m4a` |
| `bitrate` | string | nein | `64k` | Bitrate: `32k`, `64k`, `128k`, `192k` |
| `sample_rate` | int | nein | `16000` | Sample-Rate in Hz (z.B. 16000 für Whisper) |
| `channels` | int | nein | `1` | `1` (Mono) oder `2` (Stereo) |

**Response:** Konvertierte Audiodatei via `send_file()`.

**Implementierungshinweise:**
- Upload via `request.files` in `/tmp/` speichern, konvertierte Datei ebenfalls in `/tmp/`
- ffmpeg-Argumente: `-i`, `-ab`, `-ar`, `-ac`
- Beide temporäre Dateien mit `@after_this_request` löschen

---

### POST /pdf/render

Rendert ein Markdown-Dokument zu PDF via Pandoc und Typst.

**Request (JSON):**
```json
{
  "markdown": "# Titel\n\nInhalt...",
  "template": "default",
  "paper": "a4",
  "margin_mm": 25,
  "font": "libertinus",
  "toc": false,
  "metadata": {
    "title": "Dokumenttitel",
    "author": "Max Mustermann",
    "date": "2025-01-01"
  }
}
```

**Parameter:**
| Feld | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `markdown` | string | ja | – | Markdown-Inhalt |
| `template` | string | nein | `default` | Typst-Template-Name |
| `paper` | string | nein | `a4` | `a4`, `a5`, `letter` |
| `margin_mm` | int | nein | `25` | Seitenrand in mm |
| `font` | string | nein | `libertinus` | Typst-Fontname |
| `toc` | bool | nein | `false` | Inhaltsverzeichnis generieren |
| `metadata` | object | nein | `{}` | `title`, `author`, `date` |

**Response:** PDF-Datei via `send_file()` mit `mimetype='application/pdf'`.

**Implementierungshinweise:**
- Templates liegen in `/templates/`, der `template`-Parameter ist der Dateiname ohne `.typ`-Extension (z.B. `default` → `/templates/default.typ`)
- Pandoc-Argumente: `--pdf-engine=typst`, `--template=/templates/{template}.typ`, `-V papersize=`, `-V margin-left=`, `-V mainfont=`
- Die Umgebungsvariable `TYPST_FONT_PATHS=/fonts` ist bereits gesetzt – Typst findet die eingebetteten Fonts automatisch; `mainfont` muss nur übergeben werden, wenn vom Default abgewichen wird
- Markdown als stdin übergeben (`input=markdown.encode()`)
- Metadaten als YAML-Frontmatter dem Markdown voranstellen
- Ist der angegebene Template-Name nicht vorhanden, mit HTTP 400 und klarer Fehlermeldung antworten

---

## Authentifizierung (`core/auth.py`)

- API-Key via Header `X-API-Key`
- Key wird aus Umgebungsvariable `API_KEY` gelesen
- Ist `API_KEY` nicht gesetzt, wird die Prüfung übersprungen (Dev-Modus)
- Bei ungültigem Key: HTTP 401

```python
# auth.py – als Decorator implementieren:
from functools import wraps
from flask import request, abort
from core.config import API_KEY

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if API_KEY and request.headers.get("X-API-Key") != API_KEY:
            abort(401, "Invalid or missing API key")
        return f(*args, **kwargs)
    return decorated

# Verwendung in den Routen:
from core.auth import require_api_key

@bp.route("/extract", methods=["POST"])
@require_api_key
def extract():
    ...
```

---

## Konfiguration (`core/config.py`)

Alle Einstellungen via Umgebungsvariablen mit Defaults:

| Variable | Default | Beschreibung |
|---|---|---|
| `API_KEY` | `""` | Leerer String = kein Auth |
| `TMP_DIR` | `/tmp` | Verzeichnis für temporäre Dateien |
| `TEMPLATES_DIR` | `/templates` | Verzeichnis der Typst-Templates |
| `FONTS_DIR` | `/fonts` | Wird als `TYPST_FONT_PATHS` gesetzt |
| `MAX_UPLOAD_MB` | `100` | Maximale Upload-Größe |
| `WORKERS` | `2` | Anzahl Gunicorn-Worker |

---

## Fehlerbehandlung

- Alle Service-Funktionen sollen `subprocess.CalledProcessError` abfangen und als HTTP 500 mit der stderr-Ausgabe zurückgeben
- Ungültige oder fehlende Parameter: HTTP 400 via `abort(400, "...")`
- Datei nicht gefunden nach Verarbeitung: HTTP 500
- Globaler Error-Handler in `app.py` registrieren, der alle `abort()`-Aufrufe als JSON zurückgibt:

```python
@app.errorhandler(Exception)
def handle_error(e):
    code = e.code if hasattr(e, "code") else 500
    return jsonify({"error": str(e)}), code
```

**Beispiel-Fehlerresponse:**
```json
{
  "detail": "yt-dlp failed: ERROR: Unable to extract uploader id"
}
```

---

## docker-compose.yml (nur für lokales Testing)

```yaml
services:
  media-api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - API_KEY=dev-secret
    volumes:
      - /tmp/media-api:/tmp
```

---

## Wichtige Hinweise

- Alle subprocess-Aufrufe mit `check=True` und `capture_output=True`
- Keine Shell-Strings (`shell=True`) verwenden – immer Listen übergeben
- Temporäre Dateien immer mit `@after_this_request` bereinigen – auch im Fehlerfall via `try/finally` im Service
- `app.config["MAX_CONTENT_LENGTH"]` auf `MAX_UPLOAD_MB * 1024 * 1024` setzen, damit Flask große Uploads frühzeitig ablehnt
- Jede Route als Flask-Blueprint implementieren und in `app.py` mit `app.register_blueprint()` einbinden
- yt-dlp sollte regelmäßig aktualisiert werden (`pip install -U yt-dlp`); das kann als separates Update-Script oder Cron-Job gelöst werden
