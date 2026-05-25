import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./components/App";
import type { HomeAssistant } from "./types";

/**
 * Home Assistant custom panel entry point.
 * HA calls `setProperties({ hass, narrow, route, panel })` on the panel element.
 */
class PakettiTrackerPanel extends HTMLElement {
  private _root: ReturnType<typeof createRoot> | null = null;
  private _hass: HomeAssistant | null = null;

  set hass(hass: HomeAssistant) {
    this._hass = hass;
    this._render();
  }

  connectedCallback() {
    if (!this._root) {
      const mountPoint = document.createElement("div");
      mountPoint.style.height = "100%";
      this.appendChild(mountPoint);
      this._root = createRoot(mountPoint);
    }
    this._render();
  }

  disconnectedCallback() {
    if (this._root) {
      this._root.unmount();
      this._root = null;
    }
  }

  private _render() {
    if (this._root && this._hass) {
      this._root.render(
        <React.StrictMode>
          <App hass={this._hass} />
        </React.StrictMode>
      );
    }
  }
}

customElements.define("paketti-tracker-panel", PakettiTrackerPanel);
