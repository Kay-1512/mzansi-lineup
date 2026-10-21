import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getGenres } from "../api/catalog";
import * as eventsApi from "../api/events";
import CalendarView from "../components/CalendarView";
import FilterBar, { EMPTY_FILTERS } from "../components/FilterBar";
import ListView from "../components/ListView";
import ManualEventModal from "../components/ManualEventModal";
import ViewToggle from "../components/ViewToggle";
import { useAuth } from "../context/AuthContext";

function loadView() {
  const stored = localStorage.getItem("preferred_view");
  if (stored) return stored;
  return window.innerWidth < 768 ? "list" : "calendar";
}

// The list view paginates with a real "Load more" (matches what the API's
// page/page_size params are for). The calendar view instead scopes its
// fetch to whatever date range is currently visible in the grid (see
// handleRangeChange, fed by CalendarView's `datesSet`), re-fetching as the
// user navigates — so there's no cap on total matches, just a generous
// per-page size as a sanity ceiling for one visible grid's worth of events.
const LIST_PAGE_SIZE = 20;
const CALENDAR_PAGE_SIZE = 500;

export default function CalendarPage() {
  const { profile, logout } = useAuth();
  const [view, setView] = useState(loadView);
  const [tab, setTab] = useState("for-you");
  const [sort, setSort] = useState("date");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [genres, setGenres] = useState([]);
  const [forYou, setForYou] = useState([]);
  const [forYouCount, setForYouCount] = useState(0);
  const [forYouPage, setForYouPage] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);
  const [calendarRangeStart, setCalendarRangeStart] = useState(null);
  const [calendarRangeEnd, setCalendarRangeEnd] = useState(null);
  const [saved, setSaved] = useState([]);
  const [manual, setManual] = useState([]);
  // Only gates the very first paint — re-fetches triggered by filter/sort/
  // range changes must NOT flip this back to true, or they'd unmount
  // <CalendarView>, wiping out FullCalendar's own navigation state (it
  // would always snap back to the current month on every range change).
  const [initialLoading, setInitialLoading] = useState(true);
  const [showManualModal, setShowManualModal] = useState(false);

  function changeView(next) {
    setView(next);
    localStorage.setItem("preferred_view", next);
  }

  function handleRangeChange(start, end) {
    setCalendarRangeStart(start);
    setCalendarRangeEnd(end);
  }

  function buildForYouParams(page) {
    const params = {
      sort,
      page,
      page_size: view === "calendar" ? CALENDAR_PAGE_SIZE : LIST_PAGE_SIZE,
    };
    for (const [key, value] of Object.entries(filters)) {
      if (key === "city") {
        // `null` means "untouched — use the profile's default cities",
        // so it must be omitted entirely for that default to apply. Any
        // string value (including "", an explicit "Any city") is a real
        // override and must always be sent — see EventListView's handling.
        if (value !== null) params.city = value;
        continue;
      }
      if (value) params[key] = value;
    }
    // On the calendar, scope the fetch to the visible grid instead of
    // fetching every upcoming match — unless the user already set an
    // explicit date filter, which wins.
    if (view === "calendar" && calendarRangeStart && !filters.date_from && !filters.date_to) {
      params.date_from = calendarRangeStart;
      params.date_to = calendarRangeEnd;
    }
    return params;
  }

  async function loadForYouFirstPage() {
    const data = await eventsApi.getForYouEvents(buildForYouParams(1));
    setForYou(data.results);
    setForYouCount(data.count);
    setForYouPage(1);
  }

  async function loadMoreForYou() {
    setLoadingMore(true);
    try {
      const nextPage = forYouPage + 1;
      const data = await eventsApi.getForYouEvents(buildForYouParams(nextPage));
      setForYou((prev) => [...prev, ...data.results]);
      setForYouPage(nextPage);
    } finally {
      setLoadingMore(false);
    }
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
    getGenres().then(setGenres);
    loadSaved();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadForYouFirstPage().finally(() => setInitialLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort, filters, view, calendarRangeStart, calendarRangeEnd]);

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

      {tab === "for-you" && (
        <FilterBar
          genres={genres}
          sources={profile?.sources || []}
          filters={filters}
          onChange={setFilters}
        />
      )}

      {initialLoading ? (
        <p className="empty-state">Loading your lineup…</p>
      ) : view === "calendar" ? (
        <CalendarView
          events={activeEvents}
          onSave={handleSave}
          onUnsave={handleUnsave}
          onHide={handleHide}
          onRangeChange={handleRangeChange}
        />
      ) : (
        <>
          <ListView
            events={activeEvents}
            onSave={handleSave}
            onUnsave={handleUnsave}
            onHide={handleHide}
          />
          {tab === "for-you" && forYou.length < forYouCount && (
            <div className="load-more-row">
              <button type="button" className="btn-secondary" onClick={loadMoreForYou} disabled={loadingMore}>
                {loadingMore ? "Loading…" : `Load more (${forYouCount - forYou.length} more)`}
              </button>
            </div>
          )}
        </>
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
