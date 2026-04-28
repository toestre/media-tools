# Media API PDF Compile (Obsidian plugin)

Compile the active Markdown note to PDF using your [media-api](../media-api) service (`POST /pdf/render`). Works with **local** Docker (`http://localhost:3000`) or a **remote** host (`https://your-server:3000`).

## Setup

1. Run media-api (see repo [README](../README.md)): e.g. `cd media-api && docker compose up --build`.
2. Install dependencies and build this plugin:

   ```bash
   cd obsidian-media-api-plugin
   npm install
   npm run build
   ```

3. Copy the plugin folder into your vault’s `.obsidian/plugins/media-api-pdf-compile/` (create the folder if needed). Required files at minimum:
   - `manifest.json`
   - `main.js`
4. Enable **Media API PDF Compile** under Settings → Community plugins (or **Settings → Third-party plugin** depending on Obsidian version).

## Settings

| Setting | Description |
|--------|-------------|
| **API base URL** | e.g. `http://localhost:3000` or `https://homelab.example:3000` (no path; `/pdf/render` is appended). |
| **API key** | Optional. Sent as `X-API-Key`. Required when `API_KEY` is set on the server (compose default is often `dev-secret`). |
| **Typst template** | Name without `.typ` (e.g. `default`). Must exist on the server. |
| **Paper / margin / font / TOC** | Same semantics as [README `POST /pdf/render`](../README.md). |
| **Metadata** | Optional title, author, date merged into the render request. |
| **Output location** | Same folder as the note, or vault root. PDF name: `<note basename>.pdf`. |

## Usage

- Command palette: **Compile current note to PDF (media-api)**.
- Active file must be `.md` and non-empty (the API rejects empty markdown).

## Remote server notes

- Use `http://` or `https://` and ensure the host/port is reachable from the machine running Obsidian (firewall, VPN, etc.).
- If you use HTTPS with a private CA, the Obsidian/Electron trust store must validate the certificate.
- **CORS** does not apply to Obsidian desktop the same way as a browser; mobile Obsidian may differ—test on your platform.

## Manual test checklist

- [ ] With API running and no `API_KEY`: compile succeeds; PDF appears next to note (or vault root if configured).
- [ ] With `API_KEY` set: compile **without** key → notice shows HTTP 401; with correct key → success.
- [ ] Stop Docker / wrong port → notice shows network or HTTP error.
- [ ] Empty note → notice explains empty markdown.
- [ ] Non-markdown active file → notice asks for `.md`.

## Development

- `npm run dev` — watch rebuild to `main.js`.
- `npm run build` — production bundle to `main.js`.
