'use client';

import { useState } from 'react';

import { PROVIDER_LABELS, formatDistance, ratingColor } from '@/lib/display';
import type { AnalysisPin, HistoricalReport } from '@/lib/types';

interface ReportPanelProps {
  pin: AnalysisPin | null;
  report: HistoricalReport | null;
  loading: boolean;
  error: string | null;
  onRefresh: (radiusMeters: number) => void;
}

function Collapsible({
  title,
  badge,
  defaultOpen = true,
  children,
}: {
  title: string;
  badge?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="rounded-md border border-edge bg-panel">
      <button
        type="button"
        className="flex w-full items-center justify-between px-3 py-2 text-left"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-slate-100">{title}</span>
        <span className="flex items-center gap-2 text-xs text-slate-400">
          {badge && <span className="rounded bg-panelSoft px-1.5 py-0.5 font-mono">{badge}</span>}
          <span>{open ? '▾' : '▸'}</span>
        </span>
      </button>
      {open && <div className="border-t border-edge px-3 py-3 text-sm text-slate-300">{children}</div>}
    </section>
  );
}

export default function ReportPanel({ pin, report, loading, error, onRefresh }: ReportPanelProps) {
  const [radius, setRadius] = useState(10000);

  if (!pin) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-center text-sm text-slate-400">
        Click (or right-click) anywhere on the map to drop an Analysis Pin and run the historical
        intelligence engine.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <section className="rounded-md border border-edge bg-panelSoft p-3">
        <h2 className="text-sm font-semibold text-slate-100">Analysis pin</h2>
        <dl className="mt-2 grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 font-mono text-[11px] text-slate-300">
          <dt className="text-slate-500">DD</dt>
          <dd>{pin.formats?.decimal ?? `${pin.latitude.toFixed(6)}, ${pin.longitude.toFixed(6)}`}</dd>
          <dt className="text-slate-500">DMS</dt>
          <dd>{pin.formats?.dms ?? '…'}</dd>
          <dt className="text-slate-500">UTM</dt>
          <dd>{pin.formats?.utm ?? '…'}</dd>
        </dl>
        <div className="mt-3 flex items-end gap-2">
          <label className="flex-1 text-[11px] text-slate-400">
            Research radius: <span className="font-mono text-accent">{(radius / 1000).toFixed(1)} km</span>
            <input
              type="range"
              min={500}
              max={30000}
              step={500}
              value={radius}
              onChange={(event) => setRadius(Number(event.target.value))}
              className="w-full"
            />
          </label>
          <button type="button" className="btn" onClick={() => onRefresh(radius)} disabled={loading}>
            {loading ? 'Researching…' : 'Re-run'}
          </button>
        </div>
      </section>

      {loading && !report && (
        <p className="animate-pulse rounded-md border border-edge bg-panel p-3 text-sm text-slate-400">
          Querying Wikipedia, Europeana and the Internet Archive…
        </p>
      )}
      {error && <p className="rounded-md border border-danger/50 bg-danger/10 p-3 text-sm text-red-300">{error}</p>}

      {report && (
        <>
          <section className="rounded-md border border-edge bg-panelSoft p-3">
            <h2 className="text-base font-semibold text-slate-50">{report.place_label}</h2>
            {report.administrative_context && (
              <p className="text-[11px] text-slate-400">{report.administrative_context.display_name}</p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span
                className={`rounded border px-2 py-0.5 text-xs font-semibold ${ratingColor(
                  report.archaeological_potential.rating,
                )}`}
              >
                Archaeological potential: {report.archaeological_potential.rating}
              </span>
              <span className="rounded border border-edge bg-panel px-2 py-0.5 font-mono text-xs text-slate-300">
                {report.archaeological_potential.score.toFixed(0)}/100
              </span>
              <span className="rounded border border-edge bg-panel px-2 py-0.5 text-xs text-slate-400">
                {report.archaeological_potential.confidence} confidence
              </span>
              <span className="rounded border border-edge bg-panel px-2 py-0.5 text-xs text-slate-400">
                {report.synthesis_engine === 'llm' ? 'LLM synthesis' : 'heuristic synthesis'}
              </span>
              {report.cached && (
                <span className="rounded border border-edge bg-panel px-2 py-0.5 text-xs text-slate-500">
                  cached
                </span>
              )}
            </div>
          </section>

          <Collapsible title="Historical narrative">
            {report.narrative.split('\n\n').map((paragraph, index) => (
              <p key={index} className="mb-2 leading-relaxed last:mb-0">
                {paragraph}
              </p>
            ))}
          </Collapsible>

          <Collapsible
            title="Archaeological potential"
            badge={`${report.archaeological_potential.markers.length} markers`}
          >
            <p className="mb-2 leading-relaxed">{report.archaeological_potential.rationale}</p>
            <ul className="list-disc space-y-1 pl-5 text-[13px]">
              {report.archaeological_potential.markers.map((marker) => (
                <li key={marker}>{marker}</li>
              ))}
              {report.archaeological_potential.markers.length === 0 && (
                <li className="list-none pl-0 text-slate-500">No historical markers detected.</li>
              )}
            </ul>
          </Collapsible>

          <Collapsible title="Era breakdown" badge={`${report.era_breakdown.length} eras`} defaultOpen={false}>
            <ul className="space-y-2">
              {report.era_breakdown.map((era) => (
                <li key={era.era}>
                  <span className="font-semibold text-slate-100">{era.era}</span>{' '}
                  <span className="font-mono text-[11px] text-slate-500">({era.evidence_count})</span>
                  <p className="leading-relaxed text-[13px]">{era.summary}</p>
                </li>
              ))}
              {report.era_breakdown.length === 0 && <li className="text-slate-500">No era evidence.</li>}
            </ul>
          </Collapsible>

          <Collapsible title="Chronological timeline" badge={`${report.timeline.length} events`}>
            <ol className="space-y-2 border-l border-edge pl-4">
              {report.timeline.map((entry, index) => (
                <li key={`${entry.year}-${index}`} className="relative">
                  <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-accent" />
                  <span className="font-mono text-xs text-accent">
                    {entry.year !== null && entry.year < 0 ? `${Math.abs(entry.year)} BC` : entry.year ?? '—'}
                  </span>{' '}
                  <span className="text-[11px] uppercase tracking-wide text-slate-500">{entry.era}</span>
                  <p className="text-[13px] leading-relaxed">{entry.description}</p>
                  {entry.source_url && (
                    <a
                      className="text-[11px] text-accent hover:underline"
                      href={entry.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      source
                    </a>
                  )}
                </li>
              ))}
              {report.timeline.length === 0 && <li className="text-slate-500">No dated milestones found.</li>}
            </ol>
          </Collapsible>

          <Collapsible title="Sources &amp; bibliography" badge={`${report.sources.length}`}>
            <ul className="space-y-2">
              {report.sources.map((source) => (
                <li key={source.url} className="border-b border-edge pb-2 last:border-none">
                  <a
                    className="text-[13px] font-medium text-accent hover:underline"
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {source.title}
                  </a>
                  <div className="font-mono text-[10px] text-slate-500">
                    {PROVIDER_LABELS[source.provider] ?? source.provider}
                    {source.year ? ` · ${source.year}` : ''}
                    {source.creator ? ` · ${source.creator}` : ''}
                    {source.distance_meters !== null ? ` · ${formatDistance(source.distance_meters)}` : ''}
                  </div>
                  {source.snippet && (
                    <p className="mt-1 text-[12px] leading-snug text-slate-400">{source.snippet.slice(0, 320)}</p>
                  )}
                </li>
              ))}
              {report.sources.length === 0 && <li className="text-slate-500">No sources retrieved.</li>}
            </ul>
          </Collapsible>

          <Collapsible title="Provider status" defaultOpen={false}>
            <dl className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 font-mono text-[11px]">
              {Object.entries(report.provider_status).map(([provider, status]) => (
                <div key={provider} className="contents">
                  <dt className="text-slate-500">{provider}</dt>
                  <dd className={status.startsWith('error') ? 'text-danger' : 'text-slate-300'}>{status}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-2 text-[11px] text-slate-500">
              Generated {new Date(report.generated_at).toLocaleString()}
            </p>
          </Collapsible>
        </>
      )}
    </div>
  );
}
