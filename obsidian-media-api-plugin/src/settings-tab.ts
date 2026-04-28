import { App, PluginSettingTab, Setting } from "obsidian";

import type { MediaApiPdfPluginSettingsHost } from "./plugin-contract";
import type { OutputLocation, PaperSize } from "./settings";

export class MediaApiPdfSettingTab extends PluginSettingTab {
  constructor(
    app: App,
    private readonly plugin: MediaApiPdfPluginSettingsHost,
  ) {
    super(app, plugin);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Media API PDF Compile" });

    new Setting(containerEl)
      .setName("API base URL")
      .setDesc(
        "Base URL of media-api (e.g. http://localhost:3000 or https://homelab.example:3000). No trailing slash required.",
      )
      .addText((text) =>
        text
          .setPlaceholder("http://localhost:3000")
          .setValue(this.plugin.settings.apiBaseUrl)
          .onChange(async (value) => {
            this.plugin.settings.apiBaseUrl = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("API key")
      .setDesc(
        "Optional. Sent as X-API-Key. Leave empty if the server has no API_KEY set.",
      )
      .addText((text) => {
        text.inputEl.type = "password";
        text
          .setPlaceholder("e.g. dev-secret")
          .setValue(this.plugin.settings.apiKey)
          .onChange(async (value) => {
            this.plugin.settings.apiKey = value;
            await this.plugin.saveSettings();
          });
      });

    new Setting(containerEl)
      .setName("Typst template")
      .setDesc("Template name without .typ (must exist on the server).")
      .addText((text) =>
        text
          .setPlaceholder("default")
          .setValue(this.plugin.settings.template)
          .onChange(async (value) => {
            this.plugin.settings.template = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Paper size")
      .setDesc("a4, a5, or letter.")
      .addDropdown((dropdown) => {
        dropdown
          .addOption("a4", "A4")
          .addOption("a5", "A5")
          .addOption("letter", "Letter")
          .setValue(this.plugin.settings.paper)
          .onChange(async (value) => {
            this.plugin.settings.paper = value as PaperSize;
            await this.plugin.saveSettings();
          });
      });

    new Setting(containerEl)
      .setName("Margin (mm)")
      .setDesc("Page margin in millimeters (must be positive).")
      .addText((text) =>
        text
          .setPlaceholder("25")
          .setValue(String(this.plugin.settings.marginMm))
          .onChange(async (value) => {
            const n = Number.parseInt(value, 10);
            if (!Number.isFinite(n) || n <= 0) {
              return;
            }
            this.plugin.settings.marginMm = n;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Font")
      .setDesc(
        "Optional Typst font name. Empty uses template default. Aliases: libertinus, source.",
      )
      .addText((text) =>
        text
          .setPlaceholder("")
          .setValue(this.plugin.settings.font)
          .onChange(async (value) => {
            this.plugin.settings.font = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Table of contents")
      .setDesc("Enable Pandoc/Typst TOC.")
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.toc).onChange(async (value) => {
          this.plugin.settings.toc = value;
          await this.plugin.saveSettings();
        }),
      );

    containerEl.createEl("h3", { text: "Document metadata (optional)" });
    containerEl.createEl("p", {
      text: "If set, these are merged into YAML metadata for the render request. Empty fields are omitted.",
      cls: "setting-item-description",
    });

    new Setting(containerEl)
      .setName("Title")
      .addText((text) =>
        text
          .setValue(this.plugin.settings.metadataTitle)
          .onChange(async (value) => {
            this.plugin.settings.metadataTitle = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Author")
      .addText((text) =>
        text
          .setValue(this.plugin.settings.metadataAuthor)
          .onChange(async (value) => {
            this.plugin.settings.metadataAuthor = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Date")
      .addText((text) =>
        text
          .setValue(this.plugin.settings.metadataDate)
          .onChange(async (value) => {
            this.plugin.settings.metadataDate = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Output location")
      .setDesc("Save PDF next to the note or in the vault root.")
      .addDropdown((dropdown) => {
        dropdown
          .addOption("note-folder", "Same folder as note")
          .addOption("vault-root", "Vault root")
          .setValue(this.plugin.settings.outputLocation)
          .onChange(async (value) => {
            this.plugin.settings.outputLocation = value as OutputLocation;
            await this.plugin.saveSettings();
          });
      });
  }
}
