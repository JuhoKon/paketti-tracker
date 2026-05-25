import { useEffect, useState } from "react";
import type { NotificationConfig, PackageStatus } from "../types";
import { useAppContext } from "./App";
import { getNotifications, updateNotifications } from "../api";

const ALL_TRIGGERS: { value: PackageStatus; label: string }[] = [
  { value: "in_transit", label: "In Transit" },
  { value: "out_for_delivery", label: "Out for Delivery" },
  { value: "delivered", label: "Delivered" },
  { value: "exception", label: "Exception" },
];

export function NotificationSettings() {
  const { hass } = useAppContext();
  const [config, setConfig] = useState<NotificationConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void getNotifications(hass).then(setConfig);
  }, [hass]);

  if (!config) return null;

  const handleToggle = async (enabled: boolean) => {
    setSaving(true);
    const result = await updateNotifications(hass, { enabled });
    setConfig(result);
    setSaving(false);
  };

  const handleTriggerToggle = async (trigger: PackageStatus) => {
    const current = config.triggers || [];
    const newTriggers = current.includes(trigger)
      ? current.filter((t) => t !== trigger)
      : [...current, trigger];
    setSaving(true);
    const result = await updateNotifications(hass, { triggers: newTriggers });
    setConfig(result);
    setSaving(false);
  };

  const handleDevicesChange = async (devicesStr: string) => {
    const devices = devicesStr
      .split(",")
      .map((d) => d.trim())
      .filter(Boolean);
    setSaving(true);
    const result = await updateNotifications(hass, { devices });
    setConfig(result);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="paketti-settings-section">
      <h3 className="paketti-settings-section__title">Notifications</h3>

      <div className="paketti-field paketti-field--row">
        <label htmlFor="notif-enabled">Enable notifications</label>
        <input
          id="notif-enabled"
          type="checkbox"
          checked={config.enabled}
          onChange={(e) => void handleToggle(e.target.checked)}
          disabled={saving}
        />
      </div>

      {config.enabled && (
        <>
          <div className="paketti-field">
            <label>Triggers</label>
            <div className="paketti-checkbox-group">
              {ALL_TRIGGERS.map((t) => (
                <label key={t.value} className="paketti-checkbox-label">
                  <input
                    type="checkbox"
                    checked={config.triggers.includes(t.value)}
                    onChange={() => void handleTriggerToggle(t.value)}
                    disabled={saving}
                  />
                  {t.label}
                </label>
              ))}
            </div>
          </div>

          <div className="paketti-field">
            <label htmlFor="notif-devices">
              Devices (comma-separated service names)
            </label>
            <input
              id="notif-devices"
              type="text"
              defaultValue={config.devices.join(", ")}
              onBlur={(e) => void handleDevicesChange(e.target.value)}
              placeholder="e.g. mobile_app_phone"
              disabled={saving}
            />
            <div className="paketti-field__hint">
              HA notify service targets (e.g. mobile_app_your_phone)
            </div>
          </div>

          {saved && <span className="paketti-saved-msg">Saved!</span>}
        </>
      )}
    </div>
  );
}
