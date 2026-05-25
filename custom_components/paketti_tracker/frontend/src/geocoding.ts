/**
 * Geocoding utility using Nominatim (OpenStreetMap).
 * Caches results in localStorage to avoid repeated lookups.
 * Respects Nominatim's 1 request/second rate limit.
 */

interface GeoResult {
  lat: number;
  lon: number;
}

const CACHE_KEY = "paketti_tracker_geocache";
const RATE_LIMIT_MS = 1100; // slightly over 1s to be safe

let lastRequestTime = 0;

function getCache(): Record<string, GeoResult | null> {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, GeoResult | null>) : {};
  } catch {
    return {};
  }
}

function setCache(cache: Record<string, GeoResult | null>) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch {
    // localStorage full or unavailable, ignore.
  }
}

async function rateLimitedFetch(url: string): Promise<Response> {
  const now = Date.now();
  const elapsed = now - lastRequestTime;
  if (elapsed < RATE_LIMIT_MS) {
    await new Promise((resolve) => setTimeout(resolve, RATE_LIMIT_MS - elapsed));
  }
  lastRequestTime = Date.now();
  return fetch(url);
}

/**
 * Geocode a city name. Returns cached result if available.
 * Returns null if the city cannot be resolved.
 */
export async function geocodeCity(city: string): Promise<GeoResult | null> {
  const normalizedCity = city.trim().toLowerCase();
  if (!normalizedCity) return null;

  const cache = getCache();
  if (normalizedCity in cache) {
    return cache[normalizedCity] ?? null;
  }

  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city)},Finland&format=json&limit=1`;
    const response = await rateLimitedFetch(url);

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as Array<{ lat: string; lon: string }>;

    if (data.length > 0 && data[0]) {
      const result: GeoResult = {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
      };
      cache[normalizedCity] = result;
      setCache(cache);
      return result;
    }

    // Cache the miss to avoid repeated lookups.
    cache[normalizedCity] = null;
    setCache(cache);
    return null;
  } catch {
    return null;
  }
}

/**
 * Geocode multiple cities. Processes sequentially to respect rate limits.
 * Returns only successful results.
 */
export async function geocodeCities(
  cities: string[]
): Promise<Map<string, GeoResult>> {
  const results = new Map<string, GeoResult>();
  const uniqueCities = [...new Set(cities.filter(Boolean))];

  for (const city of uniqueCities) {
    const result = await geocodeCity(city);
    if (result) {
      results.set(city, result);
    }
  }

  return results;
}
