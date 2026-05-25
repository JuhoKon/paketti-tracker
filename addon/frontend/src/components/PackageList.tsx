import { useAppContext } from "./App";
import { PackageCard } from "./PackageCard";

export function PackageList() {
  const { state } = useAppContext();

  if (state.loading) {
    return (
      <div className="paketti-empty">
        <div className="paketti-spinner" />
        <p>Loading packages...</p>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="paketti-empty paketti-empty--error">
        <p>Error loading packages</p>
        <p className="paketti-empty__detail">{state.error}</p>
      </div>
    );
  }

  if (state.packages.length === 0) {
    return (
      <div className="paketti-empty">
        <svg viewBox="0 0 24 24" width="64" height="64">
          <path
            fill="currentColor"
            d="M5,3C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3H5M5,5H19V19H5V5M7,7V9H17V7H7M7,11V13H14V11H7M7,15V17H17V15H7Z"
          />
        </svg>
        <p>No packages tracked</p>
        <p className="paketti-empty__detail">
          Click "Add Package" to start tracking a package.
        </p>
      </div>
    );
  }

  // Sort: active packages first, then delivered
  const sorted = [...state.packages].sort((a, b) => {
    if (a.delivered !== b.delivered) return a.delivered ? 1 : -1;
    return (b.last_updated || b.created_at).localeCompare(a.last_updated || a.created_at);
  });

  return (
    <div className="paketti-list">
      {sorted.map((pkg) => (
        <PackageCard key={pkg.tracking_id} pkg={pkg} />
      ))}
    </div>
  );
}
