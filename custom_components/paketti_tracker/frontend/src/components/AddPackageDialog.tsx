import React, { useState } from "react";
import { useAppContext } from "./App";
import { addPackage } from "../api";

const VENDORS = [
  { value: "posti", label: "Posti" },
  { value: "postnord", label: "Postnord" },
  { value: "matkahuolto", label: "Matkahuolto" },
];

export function AddPackageDialog() {
  const { hass, dispatch, reload } = useAppContext();
  const [trackingId, setTrackingId] = useState("");
  const [vendor, setVendor] = useState("posti");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleClose = () => dispatch({ type: "TOGGLE_ADD_DIALOG" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedId = trackingId.trim();
    if (!trimmedId) {
      setError("Tracking ID is required");
      return;
    }

    setSubmitting(true);
    try {
      await addPackage(hass, trimmedId, vendor, name.trim() || undefined);
      await reload();
      handleClose();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to add package";
      if (message.includes("already_tracked")) {
        setError("This package is already being tracked");
      } else {
        setError(message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="paketti-overlay" onClick={handleClose}>
      <div
        className="paketti-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="add-package-title"
      >
        <h2 id="add-package-title" className="paketti-dialog__title">
          Add Package
        </h2>
        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="paketti-field">
            <label htmlFor="tracking-id">Tracking ID *</label>
            <input
              id="tracking-id"
              type="text"
              value={trackingId}
              onChange={(e) => setTrackingId(e.target.value)}
              placeholder="e.g. JJFI12345600001234"
              autoFocus
              disabled={submitting}
            />
          </div>
          <div className="paketti-field">
            <label htmlFor="vendor">Carrier *</label>
            <select
              id="vendor"
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
              disabled={submitting}
            >
              {VENDORS.map((v) => (
                <option key={v.value} value={v.value}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>
          <div className="paketti-field">
            <label htmlFor="pkg-name">Name (optional)</label>
            <input
              id="pkg-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Amazon order"
              disabled={submitting}
            />
          </div>
          {error && <p className="paketti-field__error">{error}</p>}
          <div className="paketti-dialog__actions">
            <button
              type="button"
              className="paketti-btn paketti-btn--text"
              onClick={handleClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="paketti-btn paketti-btn--primary"
              disabled={submitting}
            >
              {submitting ? "Adding..." : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
