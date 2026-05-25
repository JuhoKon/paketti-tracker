import { useState } from "react";
import type { Package } from "../types";
import { useAppContext } from "./App";
import { removePackage } from "../api";
import { DeliveryTimeline } from "./DeliveryTimeline";
import { EventMap } from "./EventMap";

interface PackageCardProps {
  pkg: Package;
}

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  in_transit: "In Transit",
  out_for_delivery: "Out for Delivery",
  delivered: "Delivered",
  exception: "Exception",
  unknown: "Unknown",
};

const STATUS_CLASSES: Record<string, string> = {
  pending: "paketti-badge--pending",
  in_transit: "paketti-badge--transit",
  out_for_delivery: "paketti-badge--delivery",
  delivered: "paketti-badge--delivered",
  exception: "paketti-badge--exception",
  unknown: "paketti-badge--unknown",
};

const VENDOR_NAMES: Record<string, string> = {
  posti: "Posti",
  postnord: "Postnord",
  matkahuolto: "Matkahuolto",
};

export function PackageCard({ pkg }: PackageCardProps) {
  const { hass, reload } = useAppContext();
  const [expanded, setExpanded] = useState(false);
  const [removing, setRemoving] = useState(false);

  const lastEvent = pkg.events.length > 0 ? pkg.events[0] : null;

  const handleRemove = async () => {
    if (!confirm(`Remove "${pkg.name}" from tracking?`)) return;
    setRemoving(true);
    try {
      await removePackage(hass, pkg.tracking_id);
      await reload();
    } catch {
      setRemoving(false);
    }
  };

  return (
    <div className={`paketti-card ${expanded ? "paketti-card--expanded" : ""}`}>
      <div
        className="paketti-card__header"
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") setExpanded(!expanded);
        }}
      >
        <div className="paketti-card__info">
          <div className="paketti-card__top-row">
            <h3 className="paketti-card__name">{pkg.name}</h3>
            <span className={`paketti-badge ${STATUS_CLASSES[pkg.status] ?? ""}`}>
              {STATUS_LABELS[pkg.status] ?? pkg.status}
            </span>
          </div>
          <div className="paketti-card__meta">
            <span className="paketti-card__tracking-id">{pkg.tracking_id}</span>
            <span className="paketti-card__vendor">
              {VENDOR_NAMES[pkg.vendor] ?? pkg.vendor}
            </span>
          </div>
          {lastEvent && (
            <div className="paketti-card__last-event">
              <span className="paketti-card__event-desc">{lastEvent.description}</span>
              {lastEvent.location && (
                <span className="paketti-card__event-location">
                  {" "}
                  - {lastEvent.location}
                </span>
              )}
              <span className="paketti-card__event-time">
                {formatTime(lastEvent.timestamp)}
              </span>
            </div>
          )}
        </div>
        <div className="paketti-card__chevron">
          <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            style={{
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
              transition: "transform 0.2s ease",
            }}
          >
            <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z" />
          </svg>
        </div>
      </div>

      {expanded && (
        <div className="paketti-card__body">
          <DeliveryTimeline events={pkg.events} status={pkg.status} />

          {pkg.events.some((e) => e.location) && (
            <EventMap events={pkg.events} />
          )}

          <div className="paketti-card__actions">
            <button
              className="paketti-btn paketti-btn--danger paketti-btn--small"
              onClick={() => void handleRemove()}
              disabled={removing}
            >
              {removing ? "Removing..." : "Remove Package"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}
