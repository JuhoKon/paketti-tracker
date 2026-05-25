import type { HomeAssistant, Package, Settings } from "./types";

interface PackagesResponse {
  packages: Package[];
}

interface AddPackageResponse {
  success: boolean;
  tracking_id: string;
}

interface RemovePackageResponse {
  success: boolean;
}

interface SettingsResponse {
  poll_interval_minutes: number;
}

/**
 * Fetch all tracked packages from the coordinator.
 */
export async function fetchPackages(hass: HomeAssistant): Promise<Package[]> {
  const resp = await hass.callWS<PackagesResponse>({
    type: "paketti_tracker/packages",
  });
  return resp.packages;
}

/**
 * Add a new package to track.
 */
export async function addPackage(
  hass: HomeAssistant,
  trackingId: string,
  vendor: string,
  name?: string
): Promise<AddPackageResponse> {
  return hass.callWS<AddPackageResponse>({
    type: "paketti_tracker/add_package",
    tracking_id: trackingId,
    vendor,
    name: name || "",
  });
}

/**
 * Remove a tracked package.
 */
export async function removePackage(
  hass: HomeAssistant,
  trackingId: string
): Promise<RemovePackageResponse> {
  return hass.callWS<RemovePackageResponse>({
    type: "paketti_tracker/remove_package",
    tracking_id: trackingId,
  });
}

/**
 * Trigger an immediate coordinator refresh and return updated packages.
 */
export async function refreshPackages(
  hass: HomeAssistant
): Promise<Package[]> {
  const resp = await hass.callWS<PackagesResponse>({
    type: "paketti_tracker/refresh",
  });
  return resp.packages;
}

/**
 * Get current integration settings.
 */
export async function getSettings(hass: HomeAssistant): Promise<Settings> {
  return hass.callWS<SettingsResponse>({
    type: "paketti_tracker/get_settings",
  });
}

/**
 * Update integration settings.
 */
export async function updateSettings(
  hass: HomeAssistant,
  settings: Partial<Settings>
): Promise<Settings> {
  return hass.callWS<SettingsResponse>({
    type: "paketti_tracker/update_settings",
    ...settings,
  });
}
