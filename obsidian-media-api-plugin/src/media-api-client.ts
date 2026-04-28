import type { PaperSize } from "./settings";

/** Request body for POST /pdf/render (matches media-api PdfRenderBody). */
export interface PdfRenderRequestBody {
  markdown: string;
  template: string;
  paper: PaperSize;
  margin_mm: number;
  font: string | undefined;
  toc: boolean;
  metadata: PdfRenderMetadataPayload;
}

export interface PdfRenderMetadataPayload {
  title?: string;
  author?: string;
  date?: string;
}

/** Error from media-api or network layer with actionable message. */
export class MediaApiPdfError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "MediaApiPdfError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Normalize base URL and return POST /pdf/render absolute URL. */
export function buildPdfRenderUrl(apiBaseUrl: string): string {
  const trimmed = apiBaseUrl.replace(/\/+$/, "");
  return `${trimmed}/pdf/render`;
}

/** Validate http(s) base URL for fetch. */
export function isValidApiBaseUrl(apiBaseUrl: string): boolean {
  const trimmed = apiBaseUrl.trim();
  if (trimmed === "") {
    return false;
  }
  try {
    const url = new URL(trimmed);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

export interface BuildPdfRenderBodyArgs {
  markdown: string;
  template: string;
  paper: PaperSize;
  marginMm: number;
  font: string;
  toc: boolean;
  metadataTitle: string;
  metadataAuthor: string;
  metadataDate: string;
}

/** Build JSON body for /pdf/render (pure: does not mutate args). */
export function buildPdfRenderBody(args: BuildPdfRenderBodyArgs): PdfRenderRequestBody {
  const metadata: PdfRenderMetadataPayload = {};
  const titleTrimmed = args.metadataTitle.trim();
  if (titleTrimmed !== "") {
    metadata.title = titleTrimmed;
  }
  const authorTrimmed = args.metadataAuthor.trim();
  if (authorTrimmed !== "") {
    metadata.author = authorTrimmed;
  }
  const dateTrimmed = args.metadataDate.trim();
  if (dateTrimmed !== "") {
    metadata.date = dateTrimmed;
  }
  const fontTrimmed = args.font.trim();
  const font: string | undefined = fontTrimmed === "" ? undefined : fontTrimmed;

  return {
    markdown: args.markdown,
    template: args.template,
    paper: args.paper,
    margin_mm: args.marginMm,
    font,
    toc: args.toc,
    metadata,
  };
}

export interface FetchPdfRenderArgs {
  url: string;
  apiKey: string | undefined;
  body: PdfRenderRequestBody;
}

/** POST /pdf/render and return PDF bytes. */
export async function fetchPdfRender(args: FetchPdfRenderArgs): Promise<ArrayBuffer> {
  const headers: Record<string, string> = {
    Accept: "application/pdf",
    "Content-Type": "application/json",
  };
  if (args.apiKey !== undefined) {
    headers["X-API-Key"] = args.apiKey;
  }

  let response: Response;
  try {
    response = await fetch(args.url, {
      method: "POST",
      headers,
      body: JSON.stringify(args.body),
    });
  } catch (cause) {
    const causeMsg = cause instanceof Error ? cause.message : String(cause);
    throw new MediaApiPdfError(`Network error: ${causeMsg}`);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new MediaApiPdfError(`HTTP ${String(response.status)}: ${detail}`);
  }

  return response.arrayBuffer();
}

async function readErrorDetail(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      const json: unknown = await response.json();
      if (
        json !== null &&
        typeof json === "object" &&
        !Array.isArray(json) &&
        "detail" in json
      ) {
        const detail = (json as { detail: unknown }).detail;
        return typeof detail === "string" ? detail : JSON.stringify(detail);
      }
      return JSON.stringify(json);
    } catch {
      return response.statusText || "Unknown error";
    }
  }
  const text = await response.text();
  const slice = text.slice(0, 500);
  if (slice.length > 0) {
    return slice;
  }
  return response.statusText || "Unknown error";
}
