import { useEffect, useRef, useState } from "react";
import ArtistCard from "../../components/ArtistCard";
import {
  addWatchedArtist,
  getWatchedArtists,
  removeWatchedArtist,
  searchArtists,
} from "../../api/catalog";

export default function StepArtists({ onNext, onBack }) {
  const [watched, setWatched] = useState([]);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const debounceRef = useRef(null);

  useEffect(() => {
    getWatchedArtists().then(setWatched);
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      const results = await searchArtists(query.trim());
      setSuggestions(results);
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  function isWatched(name) {
    return watched.some((a) => a.name.toLowerCase() === name.toLowerCase());
  }

  async function handleAdd(name, externalId, imageUrl) {
    const created = await addWatchedArtist(name, externalId, imageUrl);
    setWatched((prev) => [...prev, created]);
  }

  async function handleRemove(id) {
    await removeWatchedArtist(id);
    setWatched((prev) => prev.filter((a) => a.id !== id));
  }

  function toggleSuggestion(suggestion) {
    const existing = watched.find(
      (a) => a.name.toLowerCase() === suggestion.name.toLowerCase()
    );
    if (existing) {
      handleRemove(existing.id);
    } else {
      handleAdd(suggestion.name, suggestion.external_id, suggestion.image_url);
    }
  }

  return (
    <div className="onboarding-step">
      <h2>Who do you follow?</h2>
      <p className="step-hint">
        Search and tap to follow a few artists — we'll flag it when they announce an SA show.
      </p>

      <input
        type="text"
        placeholder="Search artists, e.g. Tyla"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {suggestions.length > 0 && (
        <div className="artist-card-grid">
          {suggestions.map((suggestion) => (
            <ArtistCard
              key={suggestion.external_id || suggestion.name}
              name={suggestion.name}
              imageUrl={suggestion.image_url}
              selected={isWatched(suggestion.name)}
              onClick={() => toggleSuggestion(suggestion)}
            />
          ))}
        </div>
      )}

      {watched.length > 0 && (
        <>
          <h3 className="artist-section-label">Following ({watched.length})</h3>
          <div className="artist-card-grid">
            {watched.map((artist) => (
              <ArtistCard
                key={artist.id}
                name={artist.name}
                imageUrl={artist.image_url}
                selected
                onClick={() => handleRemove(artist.id)}
              />
            ))}
          </div>
        </>
      )}

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
