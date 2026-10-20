import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as eventsApi from "../api/events";
import CalendarView from "../components/CalendarView";
import ListView from "../components/ListView";
import ManualEventModal from "../components/ManualEventModal";
import ViewToggle from "../components/ViewToggle";
import { useAuth } from "../context/AuthContext";

function loadView() {
  const stored = localStorage.getItem("preferred_view");
  if (stored) return stored;
  return window.innerWidth < 768 ? "list" : "calendar";
}

export default function CalendarPage() {
  const { profile, logout } = useAuth();
  const [view, setView] = useState(loadView);
  const [tab, setTab] = useState("for-you");
  const [sort, setSort] = useState("date");
  const [forYou, setForYou] = useState([]);
  const [saved, setSaved] = useState([]);
  const [manual, setManual] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showManualModal, setShowManualModal] = useState(false);

  function changeView(next) {
    setView(next);
    localStorage.setItem("preferred_view", next);
  }

  async function loadForYou() {
    const data = await eventsApi.getForYouEvents({ sort });
    setForYou(data.results);
  }

  async function loadSaved() {
    const [savedEvents, manualEvents] = await Promise.all([
      eventsApi.getSavedEvents(),
      eventsApi.getManualEvents(),
    ]);
    setSaved(savedEvents);
    setManual(manualEvents.map((m) => ({ ...m, kind: "manual" })));
  }

  useEffect(() => {
    setLoading(true);
    Promise.all([loadForYou(), loadSaved()]).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort]);

  async function handleSave(event) {
    await eventsApi.saveEvent(event.id);
    setForYou((prev) => prev.map((e) => (e.id === event.id ? { ...e, is_saved: true } : e)));
    loadSaved();
  }

  async function handleUnsave(event) {
    await eventsApi.unsaveEvent(event.id);
    setForYou((prev) => prev.map((e) => (e.id === event.id ? { ...e, is_saved: false } : e)));
    setSaved((prev) => prev.filter((e) => e.id !== event.id));
  }

  async function handleHide(event) {
    await eventsApi.hideEvent(event.id);
    setForYou((prev) => prev.filter((e) => e.id !== event.id));
    setSaved((prev) => prev.filter((e) => e.id !== event.id));
  }

  async function handleCreateManual(payload) {
    await eventsApi.createManualEvent(payload);
    loadSaved();
  }

  const savedTabEvents = [...saved, ...manual].sort(
    (a, b) => new Date(a.start) - new Date(b.start)
  );
  const activeEvents = tab === "for-you" ? forYou : savedTabEvents;

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Mzansi Lineup</h1>
        <nav>
          <Link to="/profile">Profile</Link>
          <button type="button" className="btn-ghost" onClick={logout}>
            Log out
          </button>
        </nav>
      </header>

      <div className="app-toolbar">
        <div className="tabs">
          <button
            type="button"
            className={tab === "for-you" ? "active" : ""}
            onClick={() => setTab("for-you")}
          >
            For you
          </button>
          <button
            type="button"
            className={tab === "saved" ? "active" : ""}
            onClick={() => setTab("saved")}
          >
            Saved
          </button>
        </div>

        <ViewToggle view={view} onChange={changeView} />

        {tab === "for-you" && (
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="sort-select">
            <option value="date">Sort: Date</option>
            <option value="match">Sort: Best match</option>
          </select>
        )}

        <button type="button" className="btn-secondary" onClick={() => setShowManualModal(true)}>
          + Add event
        </button>
      </div>

      {loading ? (
        <p className="empty-state">Loading your lineup…</p>
      ) : view === "calendar" ? (
        <CalendarView
          events={activeEvents}
          onSave={handleSave}
          onUnsave={handleUnsave}
          onHide={handleHide}
        />
      ) : (
        <ListView
          events={activeEvents}
          onSave={handleSave}
          onUnsave={handleUnsave}
          onHide={handleHide}
        />
      )}

      {!profile?.onboarding_complete && (
        <p className="empty-state">
          <Link to="/onboarding">Finish onboarding</Link> to get personalised matches.
        </p>
      )}

      {showManualModal && (
        <ManualEventModal onClose={() => setShowManualModal(false)} onCreate={handleCreateManual} />
      )}
    </div>
  );
}
