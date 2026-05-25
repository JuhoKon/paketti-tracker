import { useEffect, useState } from "react";
import { useAppContext } from "./App";
import { getSettings, updateSettings } from "../api";

export function SettingsDrawer() {
  const { hass, dispatch } = useAppContext();
  const [pollInterval, setPollInterval] = useState(60);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void getSettings(hass).then((settings) => {
      setPollInterval(settings.poll_interval_minutes);
    });
  }, [hass]);

  const handleClose = () => dispatch({ type: "TOGGLE_SETTINGS" });

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const result = await updateSettings(hass, {
        poll_interval_minutes: pollInterval,
      });
      dispatch({ type: "SET_SETTINGS", settings: result });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="paketti-overlay" onClick={handleClose}>
      <div
        className="paketti-drawer"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="settings-title"
      >
        <div className="paketti-drawer__header">
          <h2 id="settings-title" className="paketti-drawer__title">
            Settings
          </h2>
          <button
            className="paketti-btn paketti-btn--icon"
            onClick={handleClose}
            title="Close"
          >
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path
                fill="currentColor"
                d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"
              />
            </svg>
          </button>
        </div>

        <div className="paketti-drawer__body">
          <div className="paketti-field">
            <label htmlFor="poll-interval">
              Poll Interval: {pollInterval} minutes
            </label>
            <input
              id="poll-interval"
              type="range"
              min={5}
              max={240}
              step={5}
              value={pollInterval}
              onChange={(e) => setPollInterval(Number(e.target.value))}
            />
            <div className="paketti-field__hint">
              How often to check for tracking updates (5-240 minutes)
            </div>
          </div>
        </div>

        <div className="paketti-drawer__footer">
          {saved && <span className="paketti-saved-msg">Saved!</span>}
          <button
            className="paketti-btn paketti-btn--primary"
            onClick={() => void handleSave()}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
