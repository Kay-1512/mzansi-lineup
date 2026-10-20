import { formatEventDateTime } from "../utils/dateGroups";

export default function EventCard({ event, onSave, onUnsave, onHide }) {
  const isManual = event.kind === "manual";

  return (
    <div className="event-card">
      {!isManual && event.image_url && (
        <img src={event.image_url} alt="" className="event-card-image" />
      )}
      <div className="event-card-body">
        <div className="event-card-header">
          <h3>{event.title}</h3>
          {!isManual &&
            event.listings?.map((listing) => (
              <span key={listing.source_slug} className="source-badge">
                {listing.source_name}
              </span>
            ))}
        </div>

        {event.artists?.length > 0 && (
          <p className="event-card-artists">{event.artists.join(", ")}</p>
        )}

        <p className="event-card-meta">
          {formatEventDateTime(event.start)}
          {event.venue && ` · ${event.venue}`}
          {event.city && ` · ${event.city}`}
        </p>

        {!isManual && event.match_reasons?.length > 0 && (
          <p className="match-reason">{event.match_reasons[0]}</p>
        )}

        {isManual && event.notes && <p className="event-card-notes">{event.notes}</p>}

        <div className="event-card-actions">
          {!isManual && event.listings?.[0]?.ticket_url && (
            <a
              href={event.listings[0].ticket_url}
              target="_blank"
              rel="noreferrer"
              className="btn-link"
            >
              Get tickets
            </a>
          )}
          {!isManual && (
            <>
              {event.is_saved ? (
                <button type="button" className="btn-secondary" onClick={() => onUnsave?.(event)}>
                  Saved ✓
                </button>
              ) : (
                <button type="button" className="btn-secondary" onClick={() => onSave?.(event)}>
                  Save
                </button>
              )}
              <button type="button" className="btn-ghost" onClick={() => onHide?.(event)}>
                Not interested
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
