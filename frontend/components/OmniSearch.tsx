'use client';

import { useState } from 'react';

import { omniSearch } from '@/lib/api';
import type { GeocodeResult, ParsedCoordinate } from '@/lib/types';

interface OmniSearchProps {
  onLocate: (latitude: number, longitude: number, label: string, zoom?: number) => void;
}

export default function OmniSearch({ onLocate }: OmniSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<GeocodeResult[]>([]);
  const [coordinate, setCoordinate] = useState<ParsedCoordinate | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    setError(null);
    setResults([]);
    setCoordinate(null);
    try {
      const response = await omniSearch(query.trim());
      if (response.interpretation === 'coordinate' && response.coordinate) {
        setCoordinate(response.coordinate);
        onLocate(
          response.coordinate.latitude,
          response.coordinate.longitude,
          `Coordinate (${response.coordinate.format.toUpperCase()})`,
          15,
        );
      } else {
        setResults(response.results);
        if (response.results.length === 0) setError('No matches found.');
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Search failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel-section">
      <h2 className="panel-title">Omni-search &amp; locator</h2>
      <form onSubmit={submit} className="flex gap-2">
        <input
          className="input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Place, 37.7714 -1.5023, 37°46'17&quot;N 1°30'08&quot;W, 30S 631881 4180253"
          aria-label="Search place or coordinates"
        />
        <button type="submit" className="btn" disabled={busy}>
          {busy ? '…' : 'Go'}
        </button>
      </form>
      <p className="hint">Accepts decimal degrees, DMS and UTM, or any place / landmark name.</p>
      {error && <p className="text-xs text-danger">{error}</p>}
      {coordinate && (
        <dl className="mt-1 grid grid-cols-[auto,1fr] gap-x-2 text-[11px] font-mono text-slate-300">
          <dt className="text-slate-500">DD</dt>
          <dd>{coordinate.normalized}</dd>
          <dt className="text-slate-500">UTM</dt>
          <dd>{coordinate.utm}</dd>
          <dt className="text-slate-500">Parsed as</dt>
          <dd>{coordinate.format}</dd>
        </dl>
      )}
      {results.length > 0 && (
        <ul className="mt-1 max-h-52 overflow-auto rounded-md border border-edge bg-panel text-xs">
          {results.map((result) => (
            <li key={`${result.display_name}-${result.latitude}-${result.longitude}`}>
              <button
                type="button"
                className="w-full px-2 py-2 text-left hover:bg-panelSoft"
                onClick={() => onLocate(result.latitude, result.longitude, result.display_name, 14)}
              >
                <span className="block text-slate-100">{result.display_name}</span>
                <span className="block font-mono text-[10px] text-slate-500">
                  {result.latitude.toFixed(5)}, {result.longitude.toFixed(5)} · {result.kind ?? 'place'} ·{' '}
                  {result.source}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
