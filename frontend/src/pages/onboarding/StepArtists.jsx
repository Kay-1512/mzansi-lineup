import { useEffect, useRef, useState } from "react";
import { addWatchedArtist, getWatchedArtists, removeWatchedArtist, searchArtists } from "../../api/catalog";

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

  async function handleAdd(name, externalId) {
    if (watched.some((a) => a.name.toLowerCase() === name.toLowerCase())) return;
    const created = await addWatchedArtist(name, externalId);
    setWatched((prev) => [...prev, created]);
    setQuery("");
    setSuggestions([]);
  }

  async function handleRemove(id) {
    await removeWatchedArtist(id);
    setWatched((prev) => prev.filter((a) => a.id !== id));
  }

  return (
    <div className="onboarding-step">
      <h2>Who do you follow?</h2>
      <p className="step-hint">Search for artists — we'll flag it when they announce an SA show.</p>

      <div className="artist-search">
        <input
          type="text"
          placeholder="Search artists, e.g. Tyla"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && query.trim()) {
              e.preventDefault();
              handleAdd(query.trim(), null);
            }
          }}
        />
        {suggestions.length > 0 && (
          <ul className="suggestions">
            {suggestions.map((s) => (
              <li key={s.external_id || s.name}>
                <button type="button" onClick={() => handleAdd(s.name, s.external_id)}>
                  {s.name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <ul className="watched-list">
        {watched.map((artist) => (
          <li key={artist.id}>
            {artist.name}
            <button type="button" className="remove-btn" onClick={() => handleRemove(artist.id)}>
              ✕
            </button>
          </li>
        ))}
      </ul>

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
