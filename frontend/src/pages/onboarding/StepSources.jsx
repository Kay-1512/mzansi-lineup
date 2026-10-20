import { useEffect, useState } from "react";
import { getOnboardingSources, getSources, setOnboardingSources } from "../../api/catalog";

export default function StepSources({ onNext }) {
  const [sources, setSources] = useState([]);
  const [selected, setSelected] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([getSources(), getOnboardingSources()]).then(([all, mine]) => {
      setSources(all);
      setSelected(mine);
    });
  }, []);

  function toggle(slug, isActive) {
    if (!isActive) return;
    setSelected((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
  }

  async function handleNext() {
    setSaving(true);
    try {
      await setOnboardingSources(selected);
      onNext();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="onboarding-step">
      <h2>Where should we look?</h2>
      <p className="step-hint">Pick the platforms you want events pulled from.</p>
      <div className="chip-grid">
        {sources.map((source) => (
          <button
            key={source.slug}
            type="button"
            className={`chip ${selected.includes(source.slug) ? "chip-selected" : ""} ${
              !source.is_active ? "chip-disabled" : ""
            }`}
            onClick={() => toggle(source.slug, source.is_active)}
            disabled={!source.is_active}
          >
            {source.name}
            {!source.is_active && <small> (coming soon)</small>}
          </button>
        ))}
      </div>
      <div className="step-actions">
        <button type="button" onClick={handleNext} disabled={saving || selected.length === 0}>
          {saving ? "Saving…" : "Next"}
        </button>
      </div>
    </div>
  );
}
