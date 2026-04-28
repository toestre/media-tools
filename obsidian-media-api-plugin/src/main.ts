import { Notice, Plugin, TFile, normalizePath } from "obsidian";

import {
  MediaApiPdfError,
  buildPdfRenderBody,
  buildPdfRenderUrl,
  fetchPdfRender,
  isValidApiBaseUrl,
} from "./media-api-client";
import type { MediaApiPdfPluginSettingsHost } from "./plugin-contract";
import { MediaApiPdfSettingTab } from "./settings-tab";
import {
  createDefaultMediaApiPdfSettings,
  mergeMediaApiPdfSettings,
  type MediaApiPdfSettings,
} from "./settings";

export default class MediaApiPdfPlugin
  extends Plugin
  implements MediaApiPdfPluginSettingsHost
{
  settings: MediaApiPdfSettings = createDefaultMediaApiPdfSettings();

  async onload(): Promise<void> {
    await this.loadSettings();

    this.addSettingTab(new MediaApiPdfSettingTab(this.app, this));

    this.addCommand({
      id: "compile-current-note-to-pdf",
      name: "Compile current note to PDF (media-api)",
      callback: () => {
        void this.compileActiveNoteToPdf();
      },
    });
  }

  async loadSettings(): Promise<void> {
    const stored = await this.loadData();
    const defaults = createDefaultMediaApiPdfSettings();
    this.settings = mergeMediaApiPdfSettings(stored, defaults);
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }

  async compileActiveNoteToPdf(): Promise<void> {
    const file = this.app.workspace.getActiveFile();
    if (file === null) {
      new Notice("No active file.");
      return;
    }
    if (file.extension !== "md") {
      new Notice("Active file must be Markdown (.md).");
      return;
    }

    const markdown = await this.app.vault.read(file);
    if (markdown.trim() === "") {
      new Notice("Note is empty; media-api rejects empty markdown.");
      return;
    }

    const baseUrl = this.settings.apiBaseUrl.trim();
    if (!isValidApiBaseUrl(baseUrl)) {
      new Notice(
        "Invalid API base URL. Use http:// or https:// (e.g. http://localhost:3000).",
      );
      return;
    }

    const renderUrl = buildPdfRenderUrl(baseUrl);
    const body = buildPdfRenderBody({
      markdown,
      template: this.settings.template.trim() === "" ? "default" : this.settings.template.trim(),
      paper: this.settings.paper,
      marginMm: this.settings.marginMm,
      font: this.settings.font,
      toc: this.settings.toc,
      metadataTitle: this.settings.metadataTitle,
      metadataAuthor: this.settings.metadataAuthor,
      metadataDate: this.settings.metadataDate,
    });

    const apiKeyTrimmed = this.settings.apiKey.trim();
    const apiKey: string | undefined =
      apiKeyTrimmed === "" ? undefined : apiKeyTrimmed;

    try {
      new Notice("Compiling PDF…");
      const pdfBuffer = await fetchPdfRender({
        url: renderUrl,
        apiKey,
        body,
      });
      const outPath = this.resolveOutputPath({
        file,
        basename: file.basename,
      });
      await this.writePdfToVault({
        path: outPath,
        data: pdfBuffer,
      });
      new Notice(`Saved PDF: ${outPath}`);
    } catch (error) {
      const message =
        error instanceof MediaApiPdfError
          ? error.message
          : error instanceof Error
            ? error.message
            : String(error);
      console.error("Media API PDF compile failed:", error);
      new Notice(`PDF compile failed: ${message}`, 10000);
    }
  }

  resolveOutputPath(args: { file: TFile; basename: string }): string {
    if (this.settings.outputLocation === "vault-root") {
      return normalizePath(`${args.basename}.pdf`);
    }
    const parent = args.file.parent;
    if (parent === null) {
      return normalizePath(`${args.basename}.pdf`);
    }
    const dir = parent.path;
    if (dir === "" || dir === "/") {
      return normalizePath(`${args.basename}.pdf`);
    }
    return normalizePath(`${dir}/${args.basename}.pdf`);
  }

  async writePdfToVault(args: { path: string; data: ArrayBuffer }): Promise<void> {
    const existing = this.app.vault.getAbstractFileByPath(args.path);
    if (existing instanceof TFile) {
      await this.app.vault.modifyBinary(existing, args.data);
      return;
    }
    await this.app.vault.create(args.path, args.data);
  }
}

