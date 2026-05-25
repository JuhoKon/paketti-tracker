import { useState } from "react";
import type { Package } from "../types";
import { editPackage } from "../api";
import { useAppContext } from "./App";

interface Props {
  pkg: Package;
  onClose: () => void;
}

export function EditPackageDialog({ pkg, onClose }: Props) {
  const { reload } = useAppContext();
  const [name, setName] = useState(pkg.name);
  const [vendor, setVendor] = useState(pkg.vendor);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await editPackage(pkg.tracking_id, { name, vendor });
      await reload();
      onClose();
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="paketti-overlay" onClick={onClose}>
      <div className="paketti-dialog" onClick={(e) => e.stopPropagation()}>
        <h2>Edit Package</h2>
        <form onSubmit={handleSubmit}>
          <div className="paketti-field">
            <label>Tracking ID</label>
            <input type="text" value={pkg.tracking_id} disabled />
          </div>
          <div className="paketti-field">
            <label>Carrier</label>
            <select value={vendor} onChange={(e) => setVendor(e.target.value)}>
              <option value="posti">Posti</option>
              <option value="postnord">Postnord</option>
              <option value="matkahuolto">Matkahuolto</option>
            </select>
          </div>
          <div className="paketti-field">
            <label>Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          {error && <p className="paketti-error">{error}</p>}
          <div className="paketti-dialog__actions">
            <button type="button" className="paketti-btn" onClick={onClose}>
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
