import type {
  DiscoveredPackage,
  EmailConfig,
  HomeAssistant,
  NotificationConfig,
  Package,
  Settings,
} from "./types";

interface PackagesResponse {
  packages: Package[];
}

interface AddPackageResponse {
  success: boolean;
  tracking_id: string;
}

interface EditPackageResponse {
  success: boolean;
}

interface RemovePackageResponse {
  success: boolean;
}

interface SettingsResponse {
  poll_interval_minutes: number;
}

interface DiscoveredPackagesResponse {
  packages: DiscoveredPackage[];
}

interface TestConnectionResponse {
  success: boolean;
}

interface ConfirmPackageResponse {
  success: boolean;
  tracking_id: string;
}

interface DismissPackageResponse {
  success: boolean;
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
 * Edit an existing package (name/vendor).
 */
export async function editPackage(
  hass: HomeAssistant,
  trackingId: string,
  updates: { name?: string; vendor?: string }
): Promise<EditPackageResponse> {
  return hass.callWS<EditPackageResponse>({
    type: "paketti_tracker/edit_package",
    tracking_id: trackingId,
    ...updates,
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

/**
 * Get notification configuration.
 */
export async function getNotifications(
  hass: HomeAssistant
): Promise<NotificationConfig> {
  return hass.callWS<NotificationConfig>({
    type: "paketti_tracker/get_notifications",
  });
}

/**
 * Update notification configuration.
 */
export async function updateNotifications(
  hass: HomeAssistant,
  config: Partial<NotificationConfig>
): Promise<NotificationConfig> {
  return hass.callWS<NotificationConfig>({
    type: "paketti_tracker/update_notifications",
    ...config,
  });
}

/**
 * Get email configuration.
 */
export async function getEmailConfig(
  hass: HomeAssistant
): Promise<EmailConfig> {
  return hass.callWS<EmailConfig>({
    type: "paketti_tracker/get_email_config",
  });
}

/**
 * Update email configuration.
 */
export async function updateEmailConfig(
  hass: HomeAssistant,
  config: Partial<EmailConfig>
): Promise<EmailConfig> {
  return hass.callWS<EmailConfig>({
    type: "paketti_tracker/update_email_config",
    ...config,
  });
}

/**
 * Test email IMAP connection.
 */
export async function testEmailConnection(
  hass: HomeAssistant,
  server: string,
  port: number,
  username: string,
  password: string
): Promise<boolean> {
  const resp = await hass.callWS<TestConnectionResponse>({
    type: "paketti_tracker/test_email_connection",
    imap_server: server,
    imap_port: port,
    username,
    password,
  });
  return resp.success;
}

/**
 * Get discovered packages from email parsing.
 */
export async function getDiscoveredPackages(
  hass: HomeAssistant
): Promise<DiscoveredPackage[]> {
  const resp = await hass.callWS<DiscoveredPackagesResponse>({
    type: "paketti_tracker/discovered_packages",
  });
  return resp.packages;
}

/**
 * Confirm a discovered package (add to tracked).
 */
export async function confirmPackage(
  hass: HomeAssistant,
  trackingId: string,
  name?: string,
  vendor?: string
): Promise<ConfirmPackageResponse> {
  return hass.callWS<ConfirmPackageResponse>({
    type: "paketti_tracker/confirm_package",
    tracking_id: trackingId,
    ...(name ? { name } : {}),
    ...(vendor ? { vendor } : {}),
  });
}

/**
 * Dismiss a discovered package.
 */
export async function dismissPackage(
  hass: HomeAssistant,
  trackingId: string
): Promise<DismissPackageResponse> {
  return hass.callWS<DismissPackageResponse>({
    type: "paketti_tracker/dismiss_package",
    tracking_id: trackingId,
  });
}
