import ArtistSearchPicker from "../../components/ArtistSearchPicker";

export default function StepArtists({ onNext, onBack }) {
  return (
    <div className="onboarding-step">
      <h2>Who do you follow?</h2>
      <p className="step-hint">
        Search and tap to follow a few artists — we'll flag it when they announce an SA show.
      </p>

      <ArtistSearchPicker />

      <div className="step-actions">
        <button type="button" className="btn-secondary" onClick={onBack}>
          Back
        </button>
        <button type="button" onClick={onNext}>
          Next
        </button>
      </div>
    </div>
  );
}
