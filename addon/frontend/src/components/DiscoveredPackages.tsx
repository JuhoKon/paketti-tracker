import { useEffect, useState } from "react";
import type { DiscoveredPackage } from "../types";
import { getDiscoveredPackages, confirmPackage, dismissPackage } from "../api";
import { useAppContext } from "./App";

export function DiscoveredPackages() {
  const { reload } = useAppContext();
  const [discovered, setDiscovered] = useState<DiscoveredPackage[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDiscovered = async () => {
    try {
      const data = await getDiscoveredPackages();
      setDiscovered(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchDiscovered();
  }, []);

  const handleConfirm = async (trackingId: string) => {
    await confirmPackage(trackingId);
    await fetchDiscovered();
    await reload();
  };

  const handleDismiss = async (trackingId: string) => {
    await dismissPackage(trackingId);
    await fetchDiscovered();
  };

  if (loading || discovered.length === 0) return null;

  return (
    <div className="paketti-discovered">
      <h3 className="paketti-discovered__title">
        Discovered from Email ({discovered.length})
      </h3>
      <div className="paketti-discovered__list">
        {discovered.map((pkg) => (
          <div key={pkg.tracking_id} className="paketti-discovered__item">
            <div className="paketti-discovered__info">
              <span className="paketti-discovered__id">{pkg.tracking_id}</span>
              <span className="paketti-discovered__meta">
                {pkg.vendor} &middot; {pkg.source_subject || pkg.source_sender}
              </span>
            </div>
            <div className="paketti-discovered__actions">
              <button
                className="paketti-btn paketti-btn--sm paketti-btn--primary"
                onClick={() => void handleConfirm(pkg.tracking_id)}
              >
                Add
              </button>
              <button
                className="paketti-btn paketti-btn--sm paketti-btn--ghost"
                onClick={() => void handleDismiss(pkg.tracking_id)}
              >
                Dismiss
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
