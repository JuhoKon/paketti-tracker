/** REST API client — replaces WebSocket calls from the HA integration version. */

import type {
  DiscoveredPackage,
  EmailConfig,
  NotificationConfig,
  Package,
  Settings,
} from "./types";

// Base path for API calls (handles ingress prefix)
function getBasePath(): string {
  // In HA ingress, the path is passed via a meta tag or we detect it from the URL
  const meta = document.querySelector('meta[name="ingress-path"]');
  if (meta) return meta.getAttribute("content") || "";
  return "";
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const base = getBasePath();
  const resp = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`API error ${resp.status}: ${body}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

// --- Packages ---

export async function fetchPackages(): Promise<Package[]> {
  return api<Package[]>("/api/packages");
}

export async function addPackage(
  tracking_id: string,
  vendor: string,
  name: string
): Promise<Package> {
  return api<Package>("/api/packages", {
    method: "POST",
    body: JSON.stringify({ tracking_id, vendor, name }),
  });
}

export async function editPackage(
  tracking_id: string,
  updates: { name?: string; vendor?: string }
): Promise<Package> {
  return api<Package>(`/api/packages/${encodeURIComponent(tracking_id)}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export async function removePackage(tracking_id: string): Promise<void> {
  return api<void>(`/api/packages/${encodeURIComponent(tracking_id)}`, {
    method: "DELETE",
  });
}

export async function refreshPackages(): Promise<void> {
  return api<void>("/api/packages/refresh", { method: "POST" });
}

// --- Settings ---

export async function getSettings(): Promise<Settings> {
  return api<Settings>("/api/settings");
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  return api<Settings>("/api/settings", {
    method: "PATCH",
    body: JSON.stringify(settings),
  });
}

// --- Notifications ---

export async function getNotifications(): Promise<NotificationConfig> {
  return api<NotificationConfig>("/api/notifications");
}

export async function updateNotifications(
  config: Partial<NotificationConfig>
): Promise<NotificationConfig> {
  return api<NotificationConfig>("/api/notifications", {
    method: "PATCH",
    body: JSON.stringify(config),
  });
}

// --- Email ---

export async function getEmailConfig(): Promise<EmailConfig> {
  return api<EmailConfig>("/api/email");
}

export async function testEmailConnection(): Promise<{ success: boolean; message: string }> {
  return api<{ success: boolean; message: string }>("/api/email/test", {
    method: "POST",
  });
}

// --- Discovered Packages ---

export async function getDiscoveredPackages(): Promise<DiscoveredPackage[]> {
  return api<DiscoveredPackage[]>("/api/email/discovered");
}

export async function confirmPackage(tracking_id: string): Promise<void> {
  return api<void>(
    `/api/email/discovered/${encodeURIComponent(tracking_id)}/confirm`,
    { method: "POST" }
  );
}

export async function dismissPackage(tracking_id: string): Promise<void> {
  return api<void>(
    `/api/email/discovered/${encodeURIComponent(tracking_id)}`,
    { method: "DELETE" }
  );
}
