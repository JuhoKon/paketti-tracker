import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { NotificationConfig, Settings } from "../types";
import {
  getSettings,
  updateSettings,
  getNotifications,
  updateNotifications,
  getEmailConfig,
  updateEmailConfig,
  testEmailConnection,
} from "../api";
import type { EmailConfig } from "../types";

export function SettingsPage() {
  const navigate = useNavigate();

  return (
    <div className="paketti-settings">
      <div className="paketti-settings__header">
        <button className="paketti-btn paketti-btn--ghost" onClick={() => navigate("/")}>
          &larr; Back
        </button>
        <h2>Settings</h2>
      </div>
      <GeneralSettings />
      <NotificationSettings />
      <EmailSettings />
    </div>
  );
}

function GeneralSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void getSettings().then(setSettings);
  }, []);

  const handleChange = async (field: keyof Settings, value: number) => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateSettings({ [field]: value });
      setSettings(updated);
    } finally {
      setSaving(false);
    }
  };

  if (!settings) return <div className="paketti-section">Loading...</div>;

  return (
    <div className="paketti-section">
      <h3>General</h3>
      <div className="paketti-field">
        <label>Poll interval (minutes)</label>
        <input
          type="number"
          min="5"
          max="1440"
          value={settings.poll_interval_minutes}
          onChange={(e) => void handleChange("poll_interval_minutes", Number(e.target.value))}
          disabled={saving}
        />
      </div>
      <div className="paketti-field">
        <label>Email poll interval (minutes)</label>
        <input
          type="number"
          min="5"
          max="1440"
          value={settings.email_poll_interval_minutes}
          onChange={(e) => void handleChange("email_poll_interval_minutes", Number(e.target.value))}
          disabled={saving}
        />
      </div>
    </div>
  );
}

function NotificationSettings() {
  const [config, setConfig] = useState<NotificationConfig | null>(null);

  useEffect(() => {
    void getNotifications().then(setConfig);
  }, []);

  const toggleEnabled = async () => {
    if (!config) return;
    const updated = await updateNotifications({ enabled: !config.enabled });
    setConfig(updated);
  };

  if (!config) return null;

  return (
    <div className="paketti-section">
      <h3>Notifications</h3>
      <div className="paketti-field paketti-field--row">
        <label>Enabled</label>
        <input type="checkbox" checked={config.enabled} onChange={toggleEnabled} />
      </div>
      {config.enabled && (
        <>
          <div className="paketti-field">
            <label>Devices (comma-separated)</label>
            <input
              type="text"
              value={config.devices.join(", ")}
              onChange={async (e) => {
                const devices = e.target.value.split(",").map((d) => d.trim()).filter(Boolean);
                const updated = await updateNotifications({ devices });
                setConfig(updated);
              }}
              placeholder="e.g. phone, tablet"
            />
          </div>
          <div className="paketti-field">
            <label>Triggers</label>
            {config.triggers.map((t, i) => (
              <div key={t.event_type} className="paketti-field paketti-field--row">
                <input
                  type="checkbox"
                  checked={t.enabled}
                  onChange={async () => {
                    const triggers = [...config.triggers];
                    triggers[i] = { ...t, enabled: !t.enabled };
                    const updated = await updateNotifications({ triggers });
                    setConfig(updated);
                  }}
                />
                <span>{t.event_type}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function EmailSettings() {
  const [config, setConfig] = useState<EmailConfig | null>(null);
  const [password, setPassword] = useState("");
  const [testResult, setTestResult] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void getEmailConfig().then(setConfig);
  }, []);

  const handleSave = async (updates: Partial<EmailConfig & { password?: string }>) => {
    setSaving(true);
    try {
      const updated = await updateEmailConfig(updates);
      setConfig(updated);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTestResult("Testing...");
    const result = await testEmailConnection();
    setTestResult(result.success ? "Connection successful!" : `Failed: ${result.message}`);
  };

  if (!config) return null;

  return (
    <div className="paketti-section">
      <h3>Email Parsing</h3>
      <div className="paketti-field paketti-field--row">
        <label>Enabled</label>
        <input
          type="checkbox"
          checked={config.enabled}
          onChange={() => void handleSave({ enabled: !config.enabled })}
        />
      </div>
      {config.enabled && (
        <>
          <div className="paketti-field">
            <label>IMAP Server</label>
            <input
              type="text"
              value={config.host}
              onBlur={(e) => void handleSave({ host: e.target.value })}
              onChange={(e) => setConfig({ ...config, host: e.target.value })}
            />
          </div>
          <div className="paketti-field">
            <label>Port</label>
            <input
              type="number"
              value={config.port}
              onBlur={(e) => void handleSave({ port: Number(e.target.value) })}
              onChange={(e) => setConfig({ ...config, port: Number(e.target.value) })}
            />
          </div>
          <div className="paketti-field">
            <label>Username</label>
            <input
              type="text"
              value={config.username}
              onBlur={(e) => void handleSave({ username: e.target.value })}
              onChange={(e) => setConfig({ ...config, username: e.target.value })}
            />
          </div>
          <div className="paketti-field">
            <label>Password {config.password_set && "(set)"}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => { if (password) void handleSave({ password }); }}
              placeholder={config.password_set ? "Enter to change" : "Enter password"}
            />
          </div>
          <div className="paketti-field">
            <label>Folder</label>
            <input
              type="text"
              value={config.folder}
              onBlur={(e) => void handleSave({ folder: e.target.value })}
              onChange={(e) => setConfig({ ...config, folder: e.target.value })}
            />
          </div>
          <div className="paketti-field paketti-field--row">
            <label>Auto-add discovered packages</label>
            <input
              type="checkbox"
              checked={config.auto_add}
              onChange={() => void handleSave({ auto_add: !config.auto_add })}
            />
          </div>
          <div className="paketti-field">
            <button className="paketti-btn" onClick={handleTest} disabled={saving}>
              Test Connection
            </button>
            {testResult && <p className="paketti-field__hint">{testResult}</p>}
          </div>
        </>
      )}
    </div>
  );
}
