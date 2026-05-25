import type { TrackingEvent } from "../types";

interface Props {
  events: TrackingEvent[];
}

export function DeliveryTimeline({ events }: Props) {
  return (
    <div className="paketti-timeline">
      {events.map((event, i) => (
        <div key={i} className={`paketti-timeline__item ${i === 0 ? "paketti-timeline__item--latest" : ""}`}>
          <div className="paketti-timeline__dot" />
          <div className="paketti-timeline__content">
            <p className="paketti-timeline__desc">{event.description}</p>
            <span className="paketti-timeline__meta">
              {event.location && <>{event.location} &middot; </>}
              {new Date(event.timestamp).toLocaleString("fi-FI")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
