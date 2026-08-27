'use client';

import { RAMPS } from '@/lib/display';
import type { ComparatorMode, LayerDefinition, LayerState, RampId } from '@/lib/types';

interface LayerSidebarProps {
  layers: LayerDefinition[];
  layerState: Record<string, LayerState>;
  primaryBasemapId: string;
  comparisonLayerId: string | null;
  mode: ComparatorMode;
  epoch: number | null;
  onToggle: (layerId: string) => void;
  onOpacity: (layerId: string, opacity: number) => void;
  onIntensity: (layerId: string, intensity: number) => void;
  onRamp: (layerId: string, ramp: RampId) => void;
  onPrimaryBasemap: (layerId: string) => void;
  onComparison: (layerId: string | null) => void;
  onMode: (mode: ComparatorMode) => void;
  onEpoch: (epoch: number | null) => void;
}

const GROUP_TITLES: Record<string, string> = {
  lidar: 'LiDAR & terrain',
  historical: 'Historical archive',
  overlay: 'Overlays',
};

export default function LayerSidebar({
  layers,
  layerState,
  primaryBasemapId,
  comparisonLayerId,
  mode,
  epoch,
  onToggle,
  onOpacity,
  onIntensity,
  onRamp,
  onPrimaryBasemap,
  onComparison,
  onMode,
  onEpoch,
}: LayerSidebarProps) {
  const basemaps = layers.filter((layer) => layer.group === 'basemap');
  const epochs = Array.from(
    new Set(layers.filter((layer) => layer.epoch !== null).map((layer) => layer.epoch as number)),
  ).sort((a, b) => a - b);

  return (
    <div className="flex flex-col gap-5">
      <section className="panel-section">
        <h2 className="panel-title">Map comparator</h2>
        <div className="grid grid-cols-3 gap-1 rounded-md border border-edge bg-panel p-1 text-xs">
          {(['off', 'swipe', 'split'] as ComparatorMode[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onMode(option)}
              className={`rounded px-2 py-1 capitalize transition ${
                mode === option ? 'bg-accent text-slate-900 font-semibold' : 'text-slate-300 hover:bg-panelSoft'
              }`}
            >
              {option === 'off' ? 'Single' : option}
            </button>
          ))}
        </div>
        <label className="field-label" htmlFor="comparison-layer">
          Comparison pane layer
        </label>
        <select
          id="comparison-layer"
          className="input"
          value={comparisonLayerId ?? ''}
          onChange={(event) => onComparison(event.target.value || null)}
        >
          <option value="">— none —</option>
          {layers
            .filter((layer) => layer.group !== 'overlay')
            .map((layer) => (
              <option key={layer.id} value={layer.id}>
                {layer.name}
              </option>
            ))}
        </select>
        <p className="hint">
          Pane zoom and pan stay synchronised. Drag the splitter to swipe between the LiDAR stack and the
          comparison layer.
        </p>
      </section>

      <section className="panel-section">
        <h2 className="panel-title">Base cartography</h2>
        <select
          className="input"
          value={primaryBasemapId}
          onChange={(event) => onPrimaryBasemap(event.target.value)}
          aria-label="Primary basemap"
        >
          {basemaps.map((layer) => (
            <option key={layer.id} value={layer.id}>
              {layer.name}
            </option>
          ))}
        </select>
      </section>

      <section className="panel-section">
        <h2 className="panel-title">Historical epoch</h2>
        <input
          type="range"
          min={0}
          max={epochs.length - 1}
          step={1}
          value={epoch === null ? 0 : Math.max(0, epochs.indexOf(epoch))}
          onChange={(event) => onEpoch(epochs[Number(event.target.value)] ?? null)}
          aria-label="Historical epoch"
          className="w-full"
        />
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>{epochs[0]}</span>
          <span className="font-mono text-accent">{epoch ?? 'none'}</span>
          <span>{epochs[epochs.length - 1]}</span>
        </div>
        <button type="button" className="btn-ghost" onClick={() => onEpoch(null)}>
          Clear historical overlay
        </button>
      </section>

      {(['lidar', 'historical', 'overlay'] as const).map((group) => {
        const groupLayers = layers.filter((layer) => layer.group === group);
        if (groupLayers.length === 0) return null;
        return (
          <section key={group} className="panel-section">
            <h2 className="panel-title">{GROUP_TITLES[group]}</h2>
            <div className="flex flex-col gap-3">
              {groupLayers.map((layer) => {
                const state = layerState[layer.id];
                if (!state) return null;
                return (
                  <div key={layer.id} className="rounded-md border border-edge bg-panel p-2">
                    <label className="flex items-start gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={state.visible}
                        onChange={() => onToggle(layer.id)}
                        className="mt-1"
                      />
                      <span>
                        <span className="block font-medium text-slate-100">{layer.name}</span>
                        <span className="block text-[11px] leading-snug text-slate-400">
                          {layer.description}
                        </span>
                      </span>
                    </label>
                    {state.visible && (
                      <div className="mt-2 flex flex-col gap-2">
                        <div>
                          <div className="flex justify-between text-[11px] text-slate-400">
                            <span>Opacity</span>
                            <span className="font-mono">{Math.round(state.opacity * 100)}%</span>
                          </div>
                          <input
                            type="range"
                            min={0}
                            max={1}
                            step={0.05}
                            value={state.opacity}
                            onChange={(event) => onOpacity(layer.id, Number(event.target.value))}
                            aria-label={`${layer.name} opacity`}
                            className="w-full"
                          />
                        </div>
                        {layer.supports_intensity && (
                          <div>
                            <div className="flex justify-between text-[11px] text-slate-400">
                              <span>Relief intensity</span>
                              <span className="font-mono">{state.intensity.toFixed(2)}×</span>
                            </div>
                            <input
                              type="range"
                              min={0.4}
                              max={2.5}
                              step={0.05}
                              value={state.intensity}
                              onChange={(event) => onIntensity(layer.id, Number(event.target.value))}
                              aria-label={`${layer.name} intensity`}
                              className="w-full"
                            />
                          </div>
                        )}
                        <label className="text-[11px] text-slate-400">
                          Colour ramp
                          <select
                            className="input mt-1"
                            value={state.ramp}
                            onChange={(event) => onRamp(layer.id, event.target.value as RampId)}
                          >
                            {RAMPS.map((ramp) => (
                              <option key={ramp.id} value={ramp.id}>
                                {ramp.label}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
