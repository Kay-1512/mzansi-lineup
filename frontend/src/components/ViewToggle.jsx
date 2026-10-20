export default function ViewToggle({ view, onChange }) {
  return (
    <div className="view-toggle">
      <button
        type="button"
        className={view === "calendar" ? "active" : ""}
        onClick={() => onChange("calendar")}
      >
        Calendar
      </button>
      <button
        type="button"
        className={view === "list" ? "active" : ""}
        onClick={() => onChange("list")}
      >
        List
      </button>
    </div>
  );
}
