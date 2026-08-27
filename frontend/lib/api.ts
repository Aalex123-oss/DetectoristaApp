import type {
  CoordinateFormats,
  HistoricalReport,
  LayerDefinition,
  SearchResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail.slice(0, 240)}`);
  }
  return (await response.json()) as T;
}

export function fetchLayers(): Promise<LayerDefinition[]> {
  return request<LayerDefinition[]>('/api/layers');
}

export function omniSearch(query: string): Promise<SearchResponse> {
  return request<SearchResponse>(`/api/search?q=${encodeURIComponent(query)}`);
}

export function coordinateFormats(lat: number, lon: number): Promise<CoordinateFormats> {
  return request<CoordinateFormats>(`/api/search/formats?lat=${lat}&lon=${lon}`);
}

export function researchLocation(
  latitude: number,
  longitude: number,
  radiusMeters?: number,
): Promise<HistoricalReport> {
  return request<HistoricalReport>('/api/research', {
    method: 'POST',
    body: JSON.stringify({ latitude, longitude, radius_meters: radiusMeters }),
  });
}

export { API_BASE_URL };
