import React, { useState } from "react";
import type { Package } from "../types";
import { useAppContext } from "./App";
import { editPackage } from "../api";

const VENDORS = [
  { value: "posti", label: "Posti" },
  { value: "postnord", label: "Postnord" },
  { value: "matkahuolto", label: "Matkahuolto" },
];

interface EditPackageDialogProps {
  pkg: Package;
  onClose: () => void;
}

export function EditPackageDialog({ pkg, onClose }: EditPackageDialogProps) {
  const { hass, reload } = useAppContext();
  const [name, setName] = useState(pkg.name);
  const [vendor, setVendor] = useState(pkg.vendor);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const updates: { name?: string; vendor?: string } = {};
    const trimmedName = name.trim();
    if (trimmedName && trimmedName !== pkg.name) {
      updates.name = trimmedName;
    }
    if (vendor !== pkg.vendor) {
      updates.vendor = vendor;
    }

    if (Object.keys(updates).length === 0) {
      onClose();
      return;
    }

    try {
      await editPackage(hass, pkg.tracking_id, updates);
      await reload();
      onClose();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update package";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="paketti-overlay" onClick={onClose}>
      <div
        className="paketti-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="edit-package-title"
      >
        <h2 id="edit-package-title" className="paketti-dialog__title">
          Edit Package
        </h2>
        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="paketti-field">
            <label htmlFor="edit-tracking-id">Tracking ID</label>
            <input
              id="edit-tracking-id"
              type="text"
              value={pkg.tracking_id}
              disabled
              className="paketti-field__readonly"
            />
          </div>
          <div className="paketti-field">
            <label htmlFor="edit-vendor">Carrier</label>
            <select
              id="edit-vendor"
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
            <label htmlFor="edit-name">Name</label>
            <input
              id="edit-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Package name"
              autoFocus
              disabled={submitting}
            />
          </div>
          {error && <p className="paketti-field__error">{error}</p>}
          <div className="paketti-dialog__actions">
            <button
              type="button"
              className="paketti-btn paketti-btn--text"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="paketti-btn paketti-btn--primary"
              disabled={submitting}
            >
              {submitting ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
