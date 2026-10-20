import { useState } from "react";
import { updateProfile } from "../../api/auth";

const CITIES = [
  { value: "", label: "Anywhere in SA" },
  { value: "johannesburg", label: "Johannesburg" },
  { value: "pretoria", label: "Pretoria" },
  { value: "cape_town", label: "Cape Town" },
  { value: "durban", label: "Durban" },
];

export default function StepCity({ onFinish, onBack }) {
  const [city, setCity] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleFinish() {
    setSaving(true);
    try {
      await updateProfile({ city: city || null, onboarding_complete: true });
      onFinish();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="onboarding-step">
      <h2>Where are you based?</h2>
      <p className="step-hint">Optional — narrows events to your city.</p>
      <div className="chip-grid">
        {CITIES.map((c) => (
          <button
            key={c.value}
            type="button"
            className={`chip ${city === c.value ? "chip-selected" : ""}`}
            onClick={() => setCity(c.value)}
          >
            {c.label}
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
