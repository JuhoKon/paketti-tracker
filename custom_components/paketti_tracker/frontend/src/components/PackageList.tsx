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
        <svg viewBox="0 0 24 24" width="48" height="48">
          <path
            fill="currentColor"
            d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"
          />
        </svg>
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
            d="M21,16.5C21,16.88 20.79,17.21 20.47,17.38L12.57,21.82C12.41,21.94 12.21,22 12,22C11.79,22 11.59,21.94 11.43,21.82L3.53,17.38C3.21,17.21 3,16.88 3,16.5V7.5C3,7.12 3.21,6.79 3.53,6.62L11.43,2.18C11.59,2.06 11.79,2 12,2C12.21,2 12.41,2.06 12.57,2.18L20.47,6.62C20.79,6.79 21,7.12 21,7.5V16.5Z"
          />
        </svg>
        <p>No packages tracked</p>
        <p className="paketti-empty__detail">
          Click the + button to add your first package
        </p>
      </div>
    );
  }

  return (
    <div className="paketti-package-list">
      {state.packages.map((pkg) => (
        <PackageCard key={pkg.tracking_id} pkg={pkg} />
      ))}
    </div>
  );
}
