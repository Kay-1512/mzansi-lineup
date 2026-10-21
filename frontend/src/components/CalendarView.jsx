import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import interactionPlugin from "@fullcalendar/react/interaction";
import classicThemePlugin from "@fullcalendar/react/themes/classic";
import timeGridPlugin from "@fullcalendar/react/timegrid";
import { useState } from "react";
import EventCard from "./EventCard";

import "@fullcalendar/react/skeleton.css";
import "@fullcalendar/react/themes/classic/theme.css";
import "@fullcalendar/react/themes/classic/palette.css";

// Local calendar-date components, not toISOString() (which converts to UTC
// and can shift the date by a day depending on the viewer's timezone) —
// date_from/date_to are plain dates, not timezone-dependent instants.
function toLocalDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function CalendarView({ events, onSave, onUnsave, onHide, onRangeChange }) {
  const [selected, setSelected] = useState(null);

  const calendarEvents = events.map((event) => ({
    id: `${event.kind || "event"}-${event.id}`,
    title: event.title,
    start: event.start,
    end: event.end || undefined,
    extendedProps: { event },
  }));

  return (
    <div className="calendar-view">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, classicThemePlugin]}
        initialView="dayGridMonth"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,timeGridDay",
        }}
        height="auto"
        events={calendarEvents}
        eventClick={(info) => setSelected(info.event.extendedProps.event)}
        // The visible grid (including the leading/trailing days from
        // adjacent months) drives what we fetch — see CalendarPage's
        // handleRangeChange — instead of fetching every matched event with
        // an arbitrary cap. FullCalendar's `end` is exclusive (the day
        // after the last visible one); the API's date_to is inclusive, so
        // that needs a day subtracted or the last visible day's events
        // would be silently dropped.
        datesSet={(info) => {
          const inclusiveEnd = new Date(info.end);
          inclusiveEnd.setDate(inclusiveEnd.getDate() - 1);
          onRangeChange?.(toLocalDateString(info.start), toLocalDateString(inclusiveEnd));
        }}
      />

      {selected && (
        <div className="event-detail-overlay" onClick={() => setSelected(null)}>
          <div className="event-detail-panel" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="close-btn" onClick={() => setSelected(null)}>
              ✕
            </button>
            <EventCard event={selected} onSave={onSave} onUnsave={onUnsave} onHide={onHide} />
          </div>
        </div>
      )}
    </div>
  );
}
