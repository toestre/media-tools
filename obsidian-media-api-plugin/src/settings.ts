/** PDF paper sizes accepted by media-api. */
export type PaperSize = "a4" | "a5" | "letter";

/** Where to write the generated PDF relative to the vault. */
export type OutputLocation = "vault-root" | "note-folder";

/** Plugin settings persisted in Obsidian data. */
export interface MediaApiPdfSettings {
  apiBaseUrl: string;
  apiKey: string;
  template: string;
  paper: PaperSize;
  marginMm: number;
  font: string;
  toc: boolean;
  metadataTitle: string;
  metadataAuthor: string;
  metadataDate: string;
  outputLocation: OutputLocation;
}

/** Default settings for a new install. */
export function createDefaultMediaApiPdfSettings(): MediaApiPdfSettings {
  return {
    apiBaseUrl: "http://localhost:3000",
    apiKey: "",
    template: "default",
    paper: "a4",
    marginMm: 25,
    font: "",
    toc: false,
    metadataTitle: "",
    metadataAuthor: "",
    metadataDate: "",
    outputLocation: "note-folder",
  };
}

/** Merge stored partial data with defaults (no mutation of input). */
export function mergeMediaApiPdfSettings(
  stored: unknown,
  defaults: MediaApiPdfSettings,
): MediaApiPdfSettings {
  if (stored === null || typeof stored !== "object" || Array.isArray(stored)) {
    return { ...defaults };
  }
  const partial = stored as Record<string, unknown>;
  const paperRaw = partial.paper;
  const paper: PaperSize =
    paperRaw === "a4" || paperRaw === "a5" || paperRaw === "letter"
      ? paperRaw
      : defaults.paper;
  const locRaw = partial.outputLocation;
  const outputLocation: OutputLocation =
    locRaw === "vault-root" || locRaw === "note-folder"
      ? locRaw
      : defaults.outputLocation;
  const marginRaw = partial.marginMm;
  let marginMm: number = defaults.marginMm;
  if (typeof marginRaw === "number" && Number.isFinite(marginRaw) && marginRaw > 0) {
    marginMm = Math.floor(marginRaw);
  }

  return {
    apiBaseUrl:
      typeof partial.apiBaseUrl === "string"
        ? partial.apiBaseUrl
        : defaults.apiBaseUrl,
    apiKey:
      typeof partial.apiKey === "string" ? partial.apiKey : defaults.apiKey,
    template:
      typeof partial.template === "string" ? partial.template : defaults.template,
    paper,
    marginMm,
    font: typeof partial.font === "string" ? partial.font : defaults.font,
    toc:
      typeof partial.toc === "boolean" ? partial.toc : defaults.toc,
    metadataTitle:
      typeof partial.metadataTitle === "string"
        ? partial.metadataTitle
        : defaults.metadataTitle,
    metadataAuthor:
      typeof partial.metadataAuthor === "string"
        ? partial.metadataAuthor
        : defaults.metadataAuthor,
    metadataDate:
      typeof partial.metadataDate === "string"
        ? partial.metadataDate
        : defaults.metadataDate,
    outputLocation,
  };
}
