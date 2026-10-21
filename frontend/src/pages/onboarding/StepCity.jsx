import { useState } from "react";
import { updateProfile } from "../../api/auth";

const CITIES = ["Johannesburg", "Pretoria", "Cape Town", "Durban"];

export default function StepCity({ onFinish, onBack }) {
  const [cities, setCities] = useState([]);
  const [saving, setSaving] = useState(false);

  function toggleCity(city) {
    setCities((prev) =>
      prev.includes(city) ? prev.filter((c) => c !== city) : [...prev, city]
    );
  }

  async function handleFinish() {
    setSaving(true);
    try {
      await updateProfile({ cities, onboarding_complete: true });
      onFinish();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="onboarding-step">
      <h2>Where are you based?</h2>
      <p className="step-hint">
        Optional — pick as many cities as you like to narrow events to those.
      </p>
      <div className="chip-grid">
        <button
          type="button"
          className={`chip ${cities.length === 0 ? "chip-selected" : ""}`}
          onClick={() => setCities([])}
        >
          Anywhere in SA
        </button>
        {CITIES.map((city) => (
          <button
            key={city}
            type="button"
            className={`chip ${cities.includes(city) ? "chip-selected" : ""}`}
            onClick={() => toggleCity(city)}
          >
            {city}
          </button>
        ))}
      </div>
      <div className="step-actions">
        <button type="button" className="btn-secondary" onClick={onBack}>
          Back
        </button>
        <button type="button" onClick={handleFinish} disabled={saving}>
          {saving ? "Finishing…" : "Finish"}
        </button>
      </div>
    </div>
  );
}
