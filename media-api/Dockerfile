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
COPY filters/   /app/filters/

# App (Paketstruktur unter /app beibehalten)
COPY app.py /app/app.py
COPY routes/ /app/routes/
COPY services/ /app/services/
COPY core/ /app/core/

WORKDIR /app

EXPOSE 3000
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "app:app"]
