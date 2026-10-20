import { useState } from "react";

export default function ManualEventModal({ onClose, onCreate }) {
  const [title, setTitle] = useState("");
  const [venue, setVenue] = useState("");
  const [start, setStart] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await onCreate({ title, venue, start: new Date(start).toISOString(), notes });
      onClose();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="event-detail-overlay" onClick={onClose}>
      <form className="event-detail-panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <button type="button" className="close-btn" onClick={onClose}>
          ✕
        </button>
        <h2>Add your own event</h2>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Venue
          <input value={venue} onChange={(e) => setVenue(e.target.value)} />
        </label>
        <label>
          Date &amp; time
          <input
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            required
          />
        </label>
        <label>
          Notes
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        <div className="step-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Adding…" : "Add event"}
          </button>
        </div>
      </form>
    </div>
  );
}
