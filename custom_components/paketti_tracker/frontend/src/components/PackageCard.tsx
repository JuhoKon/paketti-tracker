import { useState } from "react";
import type { Package } from "../types";
import { useAppContext } from "./App";
import { removePackage } from "../api";
import { DeliveryTimeline } from "./DeliveryTimeline";
import { EditPackageDialog } from "./EditPackageDialog";

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
  const [editing, setEditing] = useState(false);

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
    <>
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
              {pkg.last_updated && (
                <span className="paketti-card__last-updated">
                  Updated {formatRelativeTime(pkg.last_updated)}
                </span>
              )}
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

            <div className="paketti-card__actions">
              {pkg.tracking_url && (
                <a
                  href={pkg.tracking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="paketti-btn paketti-btn--small paketti-btn--outline"
                  onClick={(e) => e.stopPropagation()}
                >
                  <svg viewBox="0 0 24 24" width="16" height="16" style={{ marginRight: 4 }}>
                    <path
                      fill="currentColor"
                      d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"
                    />
                  </svg>
                  Track
                </a>
              )}
              <button
                className="paketti-btn paketti-btn--small paketti-btn--outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setEditing(true);
                }}
              >
                <svg viewBox="0 0 24 24" width="16" height="16" style={{ marginRight: 4 }}>
                  <path
                    fill="currentColor"
                    d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"
                  />
                </svg>
                Edit
              </button>
              <button
                className="paketti-btn paketti-btn--danger paketti-btn--small"
                onClick={(e) => {
                  e.stopPropagation();
                  void handleRemove();
                }}
                disabled={removing}
              >
                {removing ? "Removing..." : "Remove"}
              </button>
            </div>
          </div>
        )}
      </div>

      {editing && (
        <EditPackageDialog pkg={pkg} onClose={() => setEditing(false)} />
      )}
    </>
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

function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays}d ago`;
  } catch {
    return "";
  }
}
