import EventCard from "./EventCard";
import { groupEventsByBucket } from "../utils/dateGroups";

export default function ListView({ events, onSave, onUnsave, onHide }) {
  if (events.length === 0) {
    return <p className="empty-state">Nothing here yet.</p>;
  }

  const groups = groupEventsByBucket(events);

  return (
    <div className="list-view">
      {Object.entries(groups).map(([label, items]) =>
        items.length === 0 ? null : (
          <section key={label} className="list-group">
            <h3 className="list-group-label">{label}</h3>
            {items.map((event) => (
              <EventCard
                key={`${event.kind || "event"}-${event.id}`}
                event={event}
                onSave={onSave}
                onUnsave={onUnsave}
                onHide={onHide}
              />
            ))}
          </section>
        )
      )}
    </div>
  );
}
