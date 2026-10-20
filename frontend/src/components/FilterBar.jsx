const CITIES = [
  { value: "", label: "Any city" },
  { value: "Johannesburg", label: "Johannesburg" },
  { value: "Pretoria", label: "Pretoria" },
  { value: "Cape Town", label: "Cape Town" },
  { value: "Durban", label: "Durban" },
];

const EMPTY_FILTERS = { genre: "", source: "", city: "", date_from: "", date_to: "" };

export { EMPTY_FILTERS };

export default function FilterBar({ genres, sources, filters, onChange }) {
  const hasActiveFilters = Object.values(filters).some(Boolean);

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

      <select value={filters.city} onChange={(e) => set("city", e.target.value)}>
        {CITIES.map((city) => (
          <option key={city.value} value={city.value}>
            {city.label}
          </option>
        ))}
      </select>

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

      {hasActiveFilters && (
        <button type="button" className="btn-ghost" onClick={() => onChange(EMPTY_FILTERS)}>
          Clear filters
        </button>
      )}
    </div>
  );
}
