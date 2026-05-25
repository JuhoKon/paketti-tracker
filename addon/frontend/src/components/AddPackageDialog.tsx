import { useState } from "react";
import { addPackage } from "../api";
import { useAppContext } from "./App";

export function AddPackageDialog() {
  const { dispatch, reload } = useAppContext();
  const [trackingId, setTrackingId] = useState("");
  const [vendor, setVendor] = useState("posti");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackingId.trim()) return;

    setSubmitting(true);
    setError("");
    try {
      await addPackage(trackingId.trim(), vendor, name.trim());
      await reload();
      dispatch({ type: "TOGGLE_ADD_DIALOG" });
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="paketti-overlay" onClick={() => dispatch({ type: "TOGGLE_ADD_DIALOG" })}>
      <div className="paketti-dialog" onClick={(e) => e.stopPropagation()}>
        <h2>Add Package</h2>
        <form onSubmit={handleSubmit}>
          <div className="paketti-field">
            <label>Tracking ID *</label>
            <input
              type="text"
              value={trackingId}
              onChange={(e) => setTrackingId(e.target.value)}
              placeholder="e.g. JJFI12345678901"
              required
              autoFocus
            />
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
            <label>Name (optional)</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. New headphones"
            />
          </div>
          {error && <p className="paketti-error">{error}</p>}
          <div className="paketti-dialog__actions">
            <button
              type="button"
              className="paketti-btn"
              onClick={() => dispatch({ type: "TOGGLE_ADD_DIALOG" })}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="paketti-btn paketti-btn--primary"
              disabled={submitting || !trackingId.trim()}
            >
              {submitting ? "Adding..." : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
