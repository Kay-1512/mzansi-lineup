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

export default function CalendarView({ events, onSave, onUnsave, onHide }) {
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
