import type { RampId } from './types';

export const RAMPS: { id: RampId; label: string }[] = [
  { id: 'natural', label: 'Natural' },
  { id: 'grayscale', label: 'Grayscale relief' },
  { id: 'terrain', label: 'Warm terrain' },
  { id: 'inverted', label: 'Inverted (micro-relief)' },
  { id: 'contrast', label: 'High contrast' },
];

/**
 * CSS filter applied to a tile layer container. `intensity` (0.2 - 2.5) drives
 * contrast so faint LiDAR micro-relief such as ditches can be pushed out.
 */
export function rampFilter(ramp: RampId, intensity: number): string {
  const contrast = (100 * intensity).toFixed(0);
  switch (ramp) {
    case 'grayscale':
      return `grayscale(1) contrast(${contrast}%) brightness(105%)`;
    case 'terrain':
      return `sepia(0.55) saturate(180%) hue-rotate(-15deg) contrast(${contrast}%)`;
    case 'inverted':
      return `invert(1) grayscale(1) contrast(${contrast}%)`;
    case 'contrast':
      return `contrast(${(140 * intensity).toFixed(0)}%) saturate(130%) brightness(96%)`;
    case 'natural':
    default:
      return `contrast(${contrast}%)`;
  }
}

export function formatDistance(meters: number | null): string {
  if (meters === null) return '—';
  return meters < 1000 ? `${meters.toFixed(0)} m` : `${(meters / 1000).toFixed(2)} km`;
}

export function ratingColor(rating: 'High' | 'Medium' | 'Low'): string {
  if (rating === 'High') return 'bg-danger/20 text-red-300 border-danger/50';
  if (rating === 'Medium') return 'bg-warn/20 text-amber-300 border-warn/50';
  return 'bg-ok/20 text-emerald-300 border-ok/50';
}

export const PROVIDER_LABELS: Record<string, string> = {
  wikipedia: 'Wikipedia',
  europeana: 'Europeana',
  internet_archive: 'Internet Archive',
  nominatim: 'OpenStreetMap',
  llm: 'LLM synthesis',
};
