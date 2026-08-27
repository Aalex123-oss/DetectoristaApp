'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useMemo, useState } from 'react';

import LayerSidebar from '@/components/LayerSidebar';
import OmniSearch from '@/components/OmniSearch';
import ReportPanel from '@/components/ReportPanel';
import type { FocusTarget } from '@/components/ComparatorMap';
import { coordinateFormats, fetchLayers, researchLocation } from '@/lib/api';
import type {
  AnalysisPin,
  ComparatorMode,
  HistoricalReport,
  LayerDefinition,
  LayerState,
  RampId,
} from '@/lib/types';

const ComparatorMap = dynamic(() => import('@/components/ComparatorMap'), {
  ssr: false,
  loading: () => <div className="flex h-full items-center justify-center text-slate-500">Loading map engine…</div>,
});

function initialLayerState(layers: LayerDefinition[]): Record<string, LayerState> {
  return Object.fromEntries(
    layers.map((layer) => [
      layer.id,
      {
        visible: layer.default_visible,
        opacity: layer.default_opacity,
        intensity: 1,
        ramp: 'natural' as RampId,
      },
    ]),
  );
}

export default function WorkspaceShell() {
  const [layers, setLayers] = useState<LayerDefinition[]>([]);
  const [layerState, setLayerState] = useState<Record<string, LayerState>>({});
  const [layerError, setLayerError] = useState<string | null>(null);
  const [primaryBasemapId, setPrimaryBasemapId] = useState('osm');
  const [comparisonLayerId, setComparisonLayerId] = useState<string | null>('esri-imagery');
  const [mode, setMode] = useState<ComparatorMode>('swipe');
  const [epoch, setEpoch] = useState<number | null>(null);

  const [pins, setPins] = useState<AnalysisPin[]>([]);
  const [activePinId, setActivePinId] = useState<string | null>(null);
  const [report, setReport] = useState<HistoricalReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  const [focus, setFocus] = useState<FocusTarget | null>(null);
  const [cursor, setCursor] = useState<{ latitude: number; longitude: number } | null>(null);
  const [zoom, setZoom] = useState(13);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    fetchLayers()
      .then((definitions) => {
        setLayers(definitions);
        setLayerState(initialLayerState(definitions));
      })
      .catch((cause: unknown) =>
        setLayerError(
          cause instanceof Error
            ? `Layer catalogue unavailable: ${cause.message}`
            : 'Layer catalogue unavailable',
        ),
      );
  }, []);

  const activePin = useMemo(() => pins.find((pin) => pin.id === activePinId) ?? null, [pins, activePinId]);

  const runResearch = useCallback(async (pin: AnalysisPin, radiusMeters?: number) => {
    setReportLoading(true);
    setReportError(null);
    try {
      const result = await researchLocation(pin.latitude, pin.longitude, radiusMeters);
      setReport(result);
    } catch (cause) {
      setReportError(cause instanceof Error ? cause.message : 'Research request failed');
    } finally {
      setReportLoading(false);
    }
  }, []);

  const dropPin = useCallback(
    (latitude: number, longitude: number, label = 'Analysis pin') => {
      const pin: AnalysisPin = {
        id: `pin-${Date.now()}`,
        latitude,
        longitude,
        label,
        formats: null,
        createdAt: new Date().toISOString(),
      };
      setPins((current) => [...current, pin]);
      setActivePinId(pin.id);
      setReport(null);
      coordinateFormats(latitude, longitude)
        .then((formats) =>
          setPins((current) => current.map((item) => (item.id === pin.id ? { ...item, formats } : item))),
        )
        .catch(() => undefined);
      void runResearch(pin);
    },
    [runResearch],
  );

  const locate = useCallback(
    (latitude: number, longitude: number, label: string, targetZoom?: number) => {
      setFocus({ latitude, longitude, zoom: targetZoom, nonce: Date.now() });
      dropPin(latitude, longitude, label);
    },
    [dropPin],
  );

  const updateLayer = useCallback((layerId: string, patch: Partial<LayerState>) => {
    setLayerState((current) => ({ ...current, [layerId]: { ...current[layerId], ...patch } }));
  }, []);

  const applyEpoch = useCallback(
    (nextEpoch: number | null) => {
      setEpoch(nextEpoch);
      setLayerState((current) => {
        const next = { ...current };
        layers
          .filter((layer) => layer.epoch !== null)
          .forEach((layer) => {
            next[layer.id] = { ...next[layer.id], visible: layer.epoch === nextEpoch };
          });
        return next;
      });
      if (nextEpoch !== null) {
        const layer = layers.find((candidate) => candidate.epoch === nextEpoch);
        if (layer) setComparisonLayerId(layer.id);
      }
    },
    [layers],
  );

  const selectedPinCount = pins.length;

  return (
    <div className="flex h-screen w-screen flex-col bg-panel text-slate-200">
      <header className="flex items-center justify-between gap-4 border-b border-edge bg-panelSoft px-4 py-2">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="btn-ghost"
            onClick={() => setSidebarOpen((value) => !value)}
            aria-label="Toggle layer sidebar"
          >
            ☰
          </button>
          <h1 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-100">
            Detectorista · LiDAR &amp; Historical Intelligence GIS
          </h1>
        </div>
        <div className="flex items-center gap-4 font-mono text-[11px] text-slate-400">
          <span>zoom {zoom}</span>
          <span>
            cursor{' '}
            {cursor ? `${cursor.latitude.toFixed(5)}, ${cursor.longitude.toFixed(5)}` : '—'}
          </span>
          <span>{selectedPinCount} pin(s)</span>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {sidebarOpen && (
          <aside className="w-[336px] shrink-0 overflow-y-auto border-r border-edge bg-panelSoft p-3">
            <OmniSearch onLocate={locate} />
            {layerError && <p className="mt-2 text-xs text-danger">{layerError}</p>}
            {layers.length > 0 && (
              <div className="mt-4">
                <LayerSidebar
                  layers={layers}
                  layerState={layerState}
                  primaryBasemapId={primaryBasemapId}
                  comparisonLayerId={comparisonLayerId}
                  mode={mode}
                  epoch={epoch}
                  onToggle={(layerId) =>
                    updateLayer(layerId, { visible: !layerState[layerId]?.visible })
                  }
                  onOpacity={(layerId, opacity) => updateLayer(layerId, { opacity })}
                  onIntensity={(layerId, intensity) => updateLayer(layerId, { intensity })}
                  onRamp={(layerId, ramp) => updateLayer(layerId, { ramp })}
                  onPrimaryBasemap={setPrimaryBasemapId}
                  onComparison={setComparisonLayerId}
                  onMode={setMode}
                  onEpoch={applyEpoch}
                />
              </div>
            )}
          </aside>
        )}

        <main className="relative min-w-0 flex-1">
          {layers.length > 0 ? (
            <ComparatorMap
              layers={layers}
              layerState={layerState}
              primaryBasemapId={primaryBasemapId}
              comparisonLayerId={comparisonLayerId}
              mode={mode}
              pins={pins}
              activePinId={activePinId}
              focus={focus}
              onPinDrop={dropPin}
              onPinSelect={(pinId) => {
                setActivePinId(pinId);
                const pin = pins.find((candidate) => candidate.id === pinId);
                if (pin) void runResearch(pin);
              }}
              onCursorMove={(latitude, longitude) => setCursor({ latitude, longitude })}
              onViewChange={setZoom}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">
              {layerError ?? 'Loading layer catalogue…'}
            </div>
          )}
        </main>

        <aside className="w-[400px] shrink-0 overflow-hidden border-l border-edge bg-panelSoft">
          <ReportPanel
            pin={activePin}
            report={report}
            loading={reportLoading}
            error={reportError}
            onRefresh={(radiusMeters) => activePin && void runResearch(activePin, radiusMeters)}
          />
        </aside>
      </div>
    </div>
  );
}
