import { useEffect, useRef, useState } from "react";

const CITIES = ["Johannesburg", "Pretoria", "Cape Town", "Durban"];

// `city: null` means "untouched — use the profile's default cities";
// `city: ""` means the user explicitly picked "Any city" (overriding the
// default to show everything). Both render as no checkboxes selected, but
// CalendarPage's buildForYouParams treats them differently — see its comment.
const EMPTY_FILTERS = { genre: "", source: "", city: null, date_from: "", date_to: "" };

export { EMPTY_FILTERS };

function CityMultiSelect({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  const selected = value ? value.split(",").filter(Boolean) : [];

  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function toggleCity(city) {
    const next = selected.includes(city)
      ? selected.filter((c) => c !== city)
      : [...selected, city];
    onChange(next.join(","));
  }

  const label =
    selected.length === 0 ? "Any city" : selected.length === 1 ? selected[0] : `${selected.length} cities`;

  return (
    <div className="multi-select" ref={containerRef}>
      <button type="button" className="multi-select-trigger" onClick={() => setOpen((o) => !o)}>
        {label}
      </button>
      {open && (
        <div className="multi-select-panel">
          {CITIES.map((city) => (
            <label key={city} className="multi-select-option">
              <input
                type="checkbox"
                checked={selected.includes(city)}
                onChange={() => toggleCity(city)}
              />
              {city}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export default function FilterBar({ genres, sources, filters, onChange }) {
  const hasActiveFilters = Object.entries(filters).some(
    ([key, value]) => key !== "city" && Boolean(value)
  );

  function set(key, value) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="filter-bar">
      <select value={filters.genre} onChange={(e) => set("genre", e.target.value)}>
        <option value="">All genres</option>
        {genres.map((genre) => (
          <option key={genre.slug} value={genre.slug}>
            {genre.name}
          </option>
        ))}
      </select>

      <select value={filters.source} onChange={(e) => set("source", e.target.value)}>
        <option value="">All your sources</option>
        {sources.map((source) => (
          <option key={source.slug} value={source.slug}>
            {source.name}
          </option>
        ))}
      </select>

      <CityMultiSelect value={filters.city} onChange={(value) => set("city", value)} />

      <input
        type="date"
        value={filters.date_from}
        onChange={(e) => set("date_from", e.target.value)}
        aria-label="From date"
      />
      <input
        type="date"
        value={filters.date_to}
        onChange={(e) => set("date_to", e.target.value)}
        aria-label="To date"
      />

      {(hasActiveFilters || filters.city !== null) && (
        <button type="button" className="btn-ghost" onClick={() => onChange(EMPTY_FILTERS)}>
          Clear filters
        </button>
      )}
    </div>
  );
}
