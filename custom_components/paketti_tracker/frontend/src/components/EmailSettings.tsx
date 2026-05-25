import { useEffect, useState } from "react";
import type { EmailConfig } from "../types";
import { useAppContext } from "./App";
import { getEmailConfig, updateEmailConfig, testEmailConnection } from "../api";

export function EmailSettings() {
  const { hass } = useAppContext();
  const [config, setConfig] = useState<EmailConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<boolean | null>(null);
  const [password, setPassword] = useState("");

  useEffect(() => {
    void getEmailConfig(hass).then(setConfig);
  }, [hass]);

  if (!config) return null;

  const handleToggle = async (enabled: boolean) => {
    setSaving(true);
    const result = await updateEmailConfig(hass, { enabled });
    setConfig(result);
    setSaving(false);
  };

  const handleSave = async () => {
    setSaving(true);
    const updates: Partial<EmailConfig> = {
      imap_server: config.imap_server,
      imap_port: config.imap_port,
      username: config.username,
      folder: config.folder,
      poll_interval_minutes: config.poll_interval_minutes,
      auto_add: config.auto_add,
      search_days: config.search_days,
    };
    if (password) {
      updates.password = password;
    }
    const result = await updateEmailConfig(hass, updates);
    setConfig(result);
    setPassword("");
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    const pwd = password || config.password;
    const success = await testEmailConnection(
      hass,
      config.imap_server,
      config.imap_port,
      config.username,
      pwd === "***" ? "" : pwd
    );
    setTestResult(success);
    setTesting(false);
  };

  return (
    <div className="paketti-settings-section">
      <h3 className="paketti-settings-section__title">Email Tracking</h3>

      <div className="paketti-field paketti-field--row">
        <label htmlFor="email-enabled">Enable email scanning</label>
        <input
          id="email-enabled"
          type="checkbox"
          checked={config.enabled}
          onChange={(e) => void handleToggle(e.target.checked)}
          disabled={saving}
        />
      </div>

      {config.enabled && (
        <>
          <div className="paketti-field">
            <label htmlFor="imap-server">IMAP Server</label>
            <input
              id="imap-server"
              type="text"
              value={config.imap_server}
              onChange={(e) => setConfig({ ...config, imap_server: e.target.value })}
              placeholder="imap.gmail.com"
              disabled={saving}
            />
          </div>

          <div className="paketti-field">
            <label htmlFor="imap-port">Port</label>
            <input
              id="imap-port"
              type="number"
              value={config.imap_port}
              onChange={(e) => setConfig({ ...config, imap_port: Number(e.target.value) })}
              disabled={saving}
            />
          </div>

          <div className="paketti-field">
            <label htmlFor="email-username">Username</label>
            <input
              id="email-username"
              type="text"
              value={config.username}
              onChange={(e) => setConfig({ ...config, username: e.target.value })}
              placeholder="your@email.com"
              disabled={saving}
            />
          </div>

          <div className="paketti-field">
            <label htmlFor="email-password">Password</label>
            <input
              id="email-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={config.password === "***" ? "(unchanged)" : "App password"}
              disabled={saving}
            />
          </div>

          <div className="paketti-field">
            <label htmlFor="email-folder">Folder</label>
            <input
              id="email-folder"
              type="text"
              value={config.folder}
              onChange={(e) => setConfig({ ...config, folder: e.target.value })}
              disabled={saving}
            />
          </div>

          <div className="paketti-field">
            <label htmlFor="email-poll">
              Poll interval: {config.poll_interval_minutes} min
            </label>
            <input
              id="email-poll"
              type="range"
              min={5}
              max={120}
              step={5}
              value={config.poll_interval_minutes}
              onChange={(e) =>
                setConfig({ ...config, poll_interval_minutes: Number(e.target.value) })
              }
              disabled={saving}
            />
          </div>

          <div className="paketti-field">
            <label htmlFor="email-search-days">
              Search last {config.search_days} days
            </label>
            <input
              id="email-search-days"
              type="range"
              min={1}
              max={30}
              step={1}
              value={config.search_days}
              onChange={(e) =>
                setConfig({ ...config, search_days: Number(e.target.value) })
              }
              disabled={saving}
            />
          </div>

          <div className="paketti-field paketti-field--row">
            <label htmlFor="email-auto-add">Auto-add discovered packages</label>
            <input
              id="email-auto-add"
              type="checkbox"
              checked={config.auto_add}
              onChange={(e) => setConfig({ ...config, auto_add: e.target.checked })}
              disabled={saving}
            />
          </div>

          <div className="paketti-dialog__actions">
            <button
              className="paketti-btn paketti-btn--outline paketti-btn--small"
              onClick={() => void handleTest()}
              disabled={testing || saving}
            >
              {testing ? "Testing..." : "Test Connection"}
            </button>
            <button
              className="paketti-btn paketti-btn--primary paketti-btn--small"
              onClick={() => void handleSave()}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>

          {testResult !== null && (
            <div
              className={`paketti-field__hint ${
                testResult ? "paketti-field__hint--success" : "paketti-field__hint--error"
              }`}
            >
              {testResult ? "Connection successful!" : "Connection failed. Check credentials."}
            </div>
          )}
        </>
      )}
    </div>
  );
}
