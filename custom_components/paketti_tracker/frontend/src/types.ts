/**
 * Minimal Home Assistant types for panel communication.
 */

export interface HomeAssistant {
  callWS: <T>(msg: Record<string, unknown>) => Promise<T>;
  language: string;
  states: Record<string, HassEntity>;
}

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export interface TrackingEvent {
  timestamp: string;
  description: string;
  location: string | null;
}

export interface Package {
  tracking_id: string;
  vendor: string;
  name: string;
  status: PackageStatus;
  delivered: boolean;
  events: TrackingEvent[];
  estimated_delivery: string | null;
  last_location: string | null;
  last_event_time: string | null;
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
}
