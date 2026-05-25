import { useEffect, useState } from "react";
import type { DiscoveredPackage } from "../types";
import { useAppContext } from "./App";
import { getDiscoveredPackages, confirmPackage, dismissPackage } from "../api";

export function DiscoveredPackages() {
  const { hass, reload } = useAppContext();
  const [packages, setPackages] = useState<DiscoveredPackage[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDiscovered = async () => {
    const pkgs = await getDiscoveredPackages(hass);
    setPackages(pkgs);
    setLoading(false);
  };

  useEffect(() => {
    void fetchDiscovered();
  }, [hass]);

  if (loading || packages.length === 0) return null;

  const handleConfirm = async (trackingId: string) => {
    await confirmPackage(hass, trackingId);
    await reload();
    await fetchDiscovered();
  };

  const handleDismiss = async (trackingId: string) => {
    await dismissPackage(hass, trackingId);
    await fetchDiscovered();
  };

  return (
    <div className="paketti-discovered">
      <h3 className="paketti-discovered__title">
        Discovered from Email ({packages.length})
      </h3>
      <div className="paketti-discovered__list">
        {packages.map((pkg) => (
          <div key={pkg.tracking_id} className="paketti-discovered__item">
            <div className="paketti-discovered__info">
              <span className="paketti-discovered__id">{pkg.tracking_id}</span>
              <span className="paketti-discovered__vendor">{pkg.vendor}</span>
              <span className="paketti-discovered__source" title={pkg.source_subject}>
                {pkg.source_subject.substring(0, 40)}
                {pkg.source_subject.length > 40 ? "..." : ""}
              </span>
            </div>
            <div className="paketti-discovered__actions">
              <button
                className="paketti-btn paketti-btn--primary paketti-btn--small"
                onClick={() => void handleConfirm(pkg.tracking_id)}
              >
                Add
              </button>
              <button
                className="paketti-btn paketti-btn--text paketti-btn--small"
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
