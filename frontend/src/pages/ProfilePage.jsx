import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { updateProfile } from "../api/auth";
import {
  getGenres,
  getSources,
  getWatchedArtists,
  removeWatchedArtist,
  setOnboardingGenres,
  setOnboardingSources,
} from "../api/catalog";
import { useAuth } from "../context/AuthContext";

const CITIES = ["Johannesburg", "Pretoria", "Cape Town", "Durban"];

export default function ProfilePage() {
  const { profile, refreshProfile } = useAuth();
  const [allSources, setAllSources] = useState([]);
  const [allGenres, setAllGenres] = useState([]);
  const [selectedSources, setSelectedSources] = useState([]);
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [internationalActs, setInternationalActs] = useState(false);
  const [cities, setCities] = useState([]);
  const [artists, setArtists] = useState([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!profile) return;
    Promise.all([getSources(), getGenres(), getWatchedArtists()]).then(
      ([sources, genres, watchedArtists]) => {
        setAllSources(sources);
        setAllGenres(genres);
        setArtists(watchedArtists);
      }
    );
    setSelectedSources(profile.sources.map((s) => s.slug));
    setSelectedGenres(profile.genres.map((g) => g.slug));
    setInternationalActs(profile.international_acts);
    setCities(profile.cities || []);
  }, [profile]);

  function toggle(list, setList, value) {
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  async function handleRemoveArtist(id) {
    await removeWatchedArtist(id);
    setArtists((prev) => prev.filter((a) => a.id !== id));
  }

  async function handleSave() {
    setSaved(false);
    await Promise.all([
      setOnboardingSources(selectedSources),
      setOnboardingGenres(selectedGenres, internationalActs),
      updateProfile({ cities }),
    ]);
    await refreshProfile();
    setSaved(true);
  }

  if (!profile) return null;

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Your preferences</h1>
        <nav>
          <Link to="/">Back to calendar</Link>
        </nav>
      </header>

      <div className="profile-page">
        <p className="step-hint">Signed in as {profile.email}</p>

        <section>
          <h3>Sources</h3>
          <div className="chip-grid">
            {allSources.map((source) => (
              <button
                key={source.slug}
                type="button"
                className={`chip ${selectedSources.includes(source.slug) ? "chip-selected" : ""} ${
                  !source.is_active ? "chip-disabled" : ""
                }`}
                disabled={!source.is_active}
                onClick={() => toggle(selectedSources, setSelectedSources, source.slug)}
              >
                {source.name}
              </button>
            ))}
          </div>
        </section>

        <section>
          <h3>Genres</h3>
          <div className="chip-grid">
            {allGenres.map((genre) => (
              <button
                key={genre.slug}
                type="button"
                className={`chip ${selectedGenres.includes(genre.slug) ? "chip-selected" : ""}`}
                onClick={() => toggle(selectedGenres, setSelectedGenres, genre.slug)}
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
        </section>

        <section>
          <h3>Cities</h3>
          <div className="chip-grid">
            <button
              type="button"
              className={`chip ${cities.length === 0 ? "chip-selected" : ""}`}
              onClick={() => setCities([])}
            >
              Anywhere in SA
            </button>
            {CITIES.map((c) => (
              <button
                key={c}
                type="button"
                className={`chip ${cities.includes(c) ? "chip-selected" : ""}`}
                onClick={() => toggle(cities, setCities, c)}
              >
                {c}
              </button>
            ))}
          </div>
        </section>

        <section>
          <h3>Watched artists</h3>
          <ul className="watched-list">
            {artists.map((artist) => (
              <li key={artist.id}>
                {artist.name}
                <button
                  type="button"
                  className="remove-btn"
                  onClick={() => handleRemoveArtist(artist.id)}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </section>

        <div className="step-actions">
          <button type="button" onClick={handleSave}>
            Save changes
          </button>
          {saved && <span className="save-confirmation">Saved!</span>}
        </div>
      </div>
    </div>
  );
}
