import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import leafletCss from "leaflet/dist/leaflet.css?inline";
import type { TrackingEvent } from "../types";
import { geocodeCities } from "../geocoding";

interface EventMapInnerProps {
  events: TrackingEvent[];
}

interface GeoPoint {
  lat: number;
  lon: number;
  label: string;
}

export default function EventMapInner({ events }: EventMapInnerProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const [points, setPoints] = useState<GeoPoint[]>([]);
  const [loading, setLoading] = useState(true);

  // Geocode event cities.
  useEffect(() => {
    const cities = events
      .map((e) => e.location)
      .filter((loc): loc is string => loc != null);

    void geocodeCities(cities).then((results) => {
      const geoPoints: GeoPoint[] = [];
      // Iterate events in order to maintain route sequence.
      for (const event of events) {
        if (event.location && results.has(event.location)) {
          const geo = results.get(event.location)!;
          geoPoints.push({
            lat: geo.lat,
            lon: geo.lon,
            label: `${event.location} - ${event.description}`,
          });
        }
      }
      setPoints(geoPoints);
      setLoading(false);
    });
  }, [events]);

  // Render the map.
  useEffect(() => {
    if (loading || points.length === 0 || !mapRef.current) return;

    // Clean up existing map.
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
    }

    const map = L.map(mapRef.current);
    mapInstanceRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(map);

    // Add markers.
    const latLngs: L.LatLngExpression[] = [];
    points.forEach((point, index) => {
      const latLng: L.LatLngExpression = [point.lat, point.lon];
      latLngs.push(latLng);

      const marker = L.circleMarker(latLng, {
        radius: index === 0 ? 10 : 7,
        fillColor: index === 0 ? "#4caf50" : "#2196f3",
        color: "#fff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8,
      });
      marker.bindPopup(point.label);
      marker.addTo(map);
    });

    // Draw route polyline.
    if (latLngs.length > 1) {
      L.polyline(latLngs, {
        color: "#2196f3",
        weight: 3,
        opacity: 0.6,
        dashArray: "10, 5",
      }).addTo(map);
    }

    // Fit bounds.
    if (latLngs.length === 1) {
      map.setView(latLngs[0]!, 10);
    } else {
      map.fitBounds(L.latLngBounds(latLngs), { padding: [30, 30] });
    }

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [loading, points]);

  if (loading) {
    return (
      <div className="paketti-map-loading">
        <div className="paketti-spinner" />
        <span>Geocoding locations...</span>
      </div>
    );
  }

  if (points.length === 0) {
    return null;
  }

  return (
    <>
      <style>{leafletCss}</style>
      <div ref={mapRef} className="paketti-map" />
    </>
  );
}
