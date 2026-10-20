import { useEffect, useState } from "react";
import { getGenres, getOnboardingGenres, setOnboardingGenres } from "../../api/catalog";

export default function StepGenres({ onNext, onBack }) {
  const [genres, setGenres] = useState([]);
  const [selected, setSelected] = useState([]);
  const [internationalActs, setInternationalActs] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([getGenres(), getOnboardingGenres()]).then(([all, mine]) => {
      setGenres(all);
      setSelected(mine.genres);
      setInternationalActs(mine.international_acts);
    });
  }, []);

  function toggle(slug) {
    setSelected((prev) => (prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]));
  }

  async function handleNext() {
    setSaving(true);
    try {
      await setOnboardingGenres(selected, internationalActs);
      onNext();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="onboarding-step">
      <h2>What's your sound?</h2>
      <p className="step-hint">Pick as many genres as you like.</p>
      <div className="chip-grid">
        {genres.map((genre) => (
          <button
            key={genre.slug}
            type="button"
            className={`chip ${selected.includes(genre.slug) ? "chip-selected" : ""}`}
            onClick={() => toggle(genre.slug)}
          >
            {genre.name}
          </button>
        ))}
      </div>

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={internationalActs}
          onChange={(e) => setInternationalActs(e.target.checked)}
        />
        International artists coming to SA
      </label>

      <div className="step-actions">
        <button type="button" className="btn-secondary" onClick={onBack}>
          Back
        </button>
        <button type="button" onClick={handleNext} disabled={saving}>
          {saving ? "Saving…" : "Next"}
        </button>
      </div>
    </div>
  );
}
