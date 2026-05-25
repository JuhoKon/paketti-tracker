import { useState } from "react";
import type { Package } from "../types";
import { removePackage } from "../api";
import { useAppContext } from "./App";
import { DeliveryTimeline } from "./DeliveryTimeline";
import { EditPackageDialog } from "./EditPackageDialog";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  in_transit: "In Transit",
  out_for_delivery: "Out for Delivery",
  delivered: "Delivered",
  exception: "Exception",
  unknown: "Unknown",
};

interface Props {
  pkg: Package;
}

export function PackageCard({ pkg }: Props) {
  const { reload } = useAppContext();
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Remove "${pkg.name || pkg.tracking_id}" from tracking?`)) return;
    setDeleting(true);
    try {
      await removePackage(pkg.tracking_id);
      await reload();
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <div className={`paketti-card ${pkg.delivered ? "paketti-card--delivered" : ""}`}>
        <div className="paketti-card__header" onClick={() => setExpanded(!expanded)}>
          <div className="paketti-card__info">
            <span className={`paketti-status paketti-status--${pkg.status}`}>
              {STATUS_LABELS[pkg.status] || pkg.status}
            </span>
            <h3 className="paketti-card__name">{pkg.name || pkg.tracking_id}</h3>
            <span className="paketti-card__meta">
              {pkg.vendor} &middot; {pkg.tracking_id}
            </span>
          </div>
          <div className="paketti-card__actions">
            {pkg.tracking_url && (
              <a
                href={pkg.tracking_url}
                target="_blank"
                rel="noopener noreferrer"
                className="paketti-btn paketti-btn--sm"
                onClick={(e) => e.stopPropagation()}
              >
                Track
              </a>
            )}
            <button
              className="paketti-btn paketti-btn--sm paketti-btn--ghost"
              onClick={(e) => { e.stopPropagation(); setEditing(true); }}
            >
              Edit
            </button>
            <button
              className="paketti-btn paketti-btn--sm paketti-btn--danger"
              onClick={(e) => { e.stopPropagation(); void handleDelete(); }}
              disabled={deleting}
            >
              {deleting ? "..." : "Remove"}
            </button>
          </div>
        </div>

        {expanded && pkg.events.length > 0 && (
          <div className="paketti-card__timeline">
            <DeliveryTimeline events={pkg.events} />
          </div>
        )}

        {expanded && pkg.events.length === 0 && (
          <div className="paketti-card__timeline paketti-card__timeline--empty">
            <p>No tracking events yet.</p>
          </div>
        )}
      </div>

      {editing && (
        <EditPackageDialog pkg={pkg} onClose={() => setEditing(false)} />
      )}
    </>
  );
}
