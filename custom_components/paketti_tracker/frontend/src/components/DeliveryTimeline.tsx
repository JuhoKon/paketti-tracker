import type { PackageStatus, TrackingEvent } from "../types";

interface DeliveryTimelineProps {
  events: TrackingEvent[];
  status: PackageStatus;
}

/**
 * Color mapping based on event context and overall package status.
 */
function getNodeColor(
  event: TrackingEvent,
  index: number,
  packageStatus: PackageStatus
): string {
  // Most recent event (index 0) inherits from package status.
  if (index === 0) {
    switch (packageStatus) {
      case "delivered":
        return "var(--paketti-color-delivered, #4caf50)";
      case "out_for_delivery":
        return "var(--paketti-color-delivery, #2196f3)";
      case "exception":
        return "var(--paketti-color-exception, #f44336)";
      case "in_transit":
        return "var(--paketti-color-transit, #2196f3)";
      case "pending":
        return "var(--paketti-color-pending, #9e9e9e)";
      default:
        return "var(--paketti-color-unknown, #9e9e9e)";
    }
  }

  // Past events: determine from description keywords.
  const desc = event.description.toLowerCase();
  if (desc.includes("deliver") || desc.includes("pickup") || desc.includes("noudet")) {
    return "var(--paketti-color-delivered, #4caf50)";
  }
  if (desc.includes("exception") || desc.includes("failed") || desc.includes("return")) {
    return "var(--paketti-color-exception, #f44336)";
  }
  return "var(--paketti-color-transit, #2196f3)";
}

export function DeliveryTimeline({ events, status }: DeliveryTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="paketti-timeline">
        <div className="paketti-timeline__item paketti-timeline__item--placeholder">
          <div
            className="paketti-timeline__node"
            style={{ backgroundColor: "var(--paketti-color-pending, #9e9e9e)" }}
          />
          <div className="paketti-timeline__content">
            <span className="paketti-timeline__desc">Awaiting first scan</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="paketti-timeline">
      {events.map((event, index) => {
        const isActive = index === 0;
        const color = getNodeColor(event, index, status);

        return (
          <div
            key={`${event.timestamp}-${index}`}
            className={`paketti-timeline__item ${isActive ? "paketti-timeline__item--active" : ""}`}
          >
            {/* Connecting line (not on last item) */}
            {index < events.length - 1 && (
              <div className="paketti-timeline__line" />
            )}
            <div
              className={`paketti-timeline__node ${isActive ? "paketti-timeline__node--active" : ""}`}
              style={{ backgroundColor: color }}
            />
            <div className="paketti-timeline__content">
              <span className="paketti-timeline__desc">{event.description}</span>
              <div className="paketti-timeline__meta">
                {event.location && (
                  <span className="paketti-timeline__location">{event.location}</span>
                )}
                <span className="paketti-timeline__time">
                  {formatEventTime(event.timestamp)}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function formatEventTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}
