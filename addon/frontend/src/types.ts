/** Shared TypeScript types for Paketti Tracker frontend. */

export interface TrackingEvent {
  timestamp: string;
  description: string;
  location: string;
}

export interface Package {
  tracking_id: string;
  vendor: string;
  name: string;
  status: PackageStatus;
  delivered: boolean;
  events: TrackingEvent[];
  estimated_delivery: string | null;
  last_location: string;
  last_event_time: string | null;
  last_updated: string | null;
  tracking_url: string;
  created_at: string;
}

export type PackageStatus =
  | "pending"
  | "in_transit"
  | "out_for_delivery"
  | "delivered"
  | "exception"
  | "unknown";

export interface Settings {
  poll_interval_minutes: number;
  email_poll_interval_minutes: number;
}

export interface NotificationTrigger {
  event_type: string;
  enabled: boolean;
}

export interface NotificationConfig {
  enabled: boolean;
  triggers: NotificationTrigger[];
  devices: string[];
}

export interface EmailConfig {
  enabled: boolean;
  host: string;
  port: number;
  username: string;
  password_set: boolean;
  folder: string;
  auto_add: boolean;
}

export interface DiscoveredPackage {
  tracking_id: string;
  vendor: string;
  source_subject: string;
  source_sender: string;
  discovered_at: string;
}
