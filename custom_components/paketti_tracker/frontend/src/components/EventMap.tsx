import { lazy, Suspense } from "react";
import type { TrackingEvent } from "../types";

// Lazy-load the actual map component so Leaflet isn't in the initial bundle.
const EventMapInner = lazy(() => import("./EventMapInner"));

interface EventMapProps {
  events: TrackingEvent[];
}

export function EventMap({ events }: EventMapProps) {
  const eventsWithLocation = events.filter((e) => e.location);

  if (eventsWithLocation.length === 0) {
    return null;
  }

  return (
    <div className="paketti-map-container">
      <Suspense
        fallback={
          <div className="paketti-map-loading">
            <div className="paketti-spinner" />
            <span>Loading map...</span>
          </div>
        }
      >
        <EventMapInner events={eventsWithLocation} />
      </Suspense>
    </div>
  );
}
