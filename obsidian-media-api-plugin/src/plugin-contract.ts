import type { MediaApiPdfSettings } from "./settings";

/** Minimal surface the settings tab needs (avoids circular import with main). */
export interface MediaApiPdfPluginSettingsHost {
  settings: MediaApiPdfSettings;
  saveSettings(): Promise<void>;
}
