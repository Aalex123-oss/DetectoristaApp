'use client';

import L from 'leaflet';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { rampFilter } from '@/lib/display';
import type { AnalysisPin, ComparatorMode, LayerDefinition, LayerState } from '@/lib/types';

export interface FocusTarget {
  latitude: number;
  longitude: number;
  zoom?: number;
  nonce: number;
}

interface ComparatorMapProps {
  layers: LayerDefinition[];
  layerState: Record<string, LayerState>;
  primaryBasemapId: string;
  comparisonLayerId: string | null;
  mode: ComparatorMode;
  pins: AnalysisPin[];
  activePinId: string | null;
  focus: FocusTarget | null;
  onPinDrop: (latitude: number, longitude: number) => void;
  onPinSelect: (pinId: string) => void;
  onCursorMove: (latitude: number, longitude: number) => void;
  onViewChange: (zoom: number) => void;
}

const PIN_ICON = L.divIcon({
  className: 'analysis-pin',
  html: '<span class="analysis-pin__dot"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const ACTIVE_PIN_ICON = L.divIcon({
  className: 'analysis-pin analysis-pin--active',
  html: '<span class="analysis-pin__dot"></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function buildLayer(definition: LayerDefinition, state: LayerState): L.TileLayer {
  const common = {
    opacity: state.opacity,
    attribution: definition.attribution,
    maxZoom: definition.max_zoom,
    className: `tile-layer-${definition.id}`,
  };
  if (definition.kind === 'wms') {
    return L.tileLayer.wms(definition.url, {
      ...common,
      layers: definition.wms_layers ?? '',
      format: definition.wms_format ?? 'image/png',
      transparent: definition.wms_transparent ?? true,
      version: '1.3.0',
      uppercase: true,
    });
  }
  return L.tileLayer(definition.url, {
    ...common,
    subdomains: definition.url.includes('{s}') ? ['a', 'b', 'c'] : [],
  });
}

function applyFilter(layer: L.TileLayer, definition: LayerDefinition, state: LayerState): void {
  const container = layer.getContainer();
  if (!container) return;
  container.style.filter = definition.supports_intensity
    ? rampFilter(state.ramp, state.intensity)
    : rampFilter(state.ramp, 1);
}

/**
 * Two synchronised Leaflet maps: pane A holds the working stack (basemap plus
 * LiDAR / historical overlays), pane B holds the comparison layer. In `swipe`
 * mode pane B is clipped by a draggable splitter; in `split` mode both panes
 * share the viewport side by side. Pan and zoom are always synchronised.
 */
export default function ComparatorMap({
  layers,
  layerState,
  primaryBasemapId,
  comparisonLayerId,
  mode,
  pins,
  activePinId,
  focus,
  onPinDrop,
  onPinSelect,
  onCursorMove,
  onViewChange,
}: ComparatorMapProps) {
  const leftHostRef = useRef<HTMLDivElement | null>(null);
  const rightHostRef = useRef<HTMLDivElement | null>(null);
  const leftMapRef = useRef<L.Map | null>(null);
  const rightMapRef = useRef<L.Map | null>(null);
  const syncingRef = useRef(false);
  const leftLayersRef = useRef<Map<string, L.TileLayer>>(new Map());
  const rightLayersRef = useRef<Map<string, L.TileLayer>>(new Map());
  const markersRef = useRef<Map<string, [L.Marker, L.Marker]>>(new Map());
  const [splitPercent, setSplitPercent] = useState(50);
  const [ready, setReady] = useState(false);
  const draggingRef = useRef(false);

  const layerById = useMemo(
    () => new Map(layers.map((definition) => [definition.id, definition])),
    [layers],
  );

  const leftStackIds = useMemo(() => {
    const overlays = layers
      .filter(
        (definition) =>
          definition.group !== 'basemap' &&
          layerState[definition.id]?.visible &&
          definition.id !== comparisonLayerId,
      )
      .sort((a, b) => (a.group === 'overlay' ? 1 : 0) - (b.group === 'overlay' ? 1 : 0))
      .map((definition) => definition.id);
    return [primaryBasemapId, ...overlays];
  }, [layers, layerState, primaryBasemapId, comparisonLayerId]);

  const rightStackIds = useMemo(() => {
    if (!comparisonLayerId) return [];
    const comparison = layerById.get(comparisonLayerId);
    if (!comparison) return [];
    return comparison.group === 'basemap' ? [comparison.id] : [primaryBasemapId, comparison.id];
  }, [comparisonLayerId, layerById, primaryBasemapId]);

  // --- map creation -------------------------------------------------------
  useEffect(() => {
    if (!leftHostRef.current || !rightHostRef.current || leftMapRef.current) return;

    const shared: L.MapOptions = {
      center: [37.7714, -1.5023],
      zoom: 13,
      zoomControl: false,
      attributionControl: true,
    };
    const left = L.map(leftHostRef.current, { ...shared, zoomControl: true });
    const right = L.map(rightHostRef.current, shared);
    L.control.scale({ imperial: false }).addTo(left);

    leftMapRef.current = left;
    rightMapRef.current = right;

    const sync = (source: L.Map, target: L.Map) => () => {
      if (syncingRef.current) return;
      syncingRef.current = true;
      target.setView(source.getCenter(), source.getZoom(), { animate: false });
      syncingRef.current = false;
      onViewChange(source.getZoom());
    };
    left.on('move zoom', sync(left, right));
    right.on('move zoom', sync(right, left));

    const dropPin = (event: L.LeafletMouseEvent) => onPinDrop(event.latlng.lat, event.latlng.lng);
    left.on('click', dropPin);
    left.on('contextmenu', dropPin);
    right.on('click', dropPin);
    right.on('contextmenu', dropPin);
    const trackCursor = (event: L.LeafletMouseEvent) => onCursorMove(event.latlng.lat, event.latlng.lng);
    left.on('mousemove', trackCursor);
    right.on('mousemove', trackCursor);

    const leftLayers = leftLayersRef.current;
    const rightLayers = rightLayersRef.current;
    const markers = markersRef.current;

    setReady(true);
    return () => {
      left.remove();
      right.remove();
      leftMapRef.current = null;
      rightMapRef.current = null;
      leftLayers.clear();
      rightLayers.clear();
      markers.clear();
    };
    // Handlers are stable callbacks provided by the workspace shell.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- layer stacks -------------------------------------------------------
  const syncStack = useCallback(
    (map: L.Map | null, cache: Map<string, L.TileLayer>, stack: string[]) => {
      if (!map) return;
      cache.forEach((layer, id) => {
        if (!stack.includes(id)) {
          map.removeLayer(layer);
          cache.delete(id);
        }
      });
      stack.forEach((id, index) => {
        const definition = layerById.get(id);
        if (!definition) return;
        const state =
          layerState[id] ?? {
            visible: true,
            opacity: definition.default_opacity,
            intensity: 1,
            ramp: 'natural' as const,
          };
        let layer = cache.get(id);
        if (!layer) {
          layer = buildLayer(definition, state);
          layer.addTo(map);
          cache.set(id, layer);
          layer.once('load', () => applyFilter(layer as L.TileLayer, definition, state));
        }
        layer.setOpacity(state.opacity);
        layer.setZIndex(index + 1);
        applyFilter(layer, definition, state);
      });
    },
    [layerById, layerState],
  );

  useEffect(() => {
    if (!ready) return;
    syncStack(leftMapRef.current, leftLayersRef.current, leftStackIds);
    syncStack(rightMapRef.current, rightLayersRef.current, rightStackIds);
  }, [ready, syncStack, leftStackIds, rightStackIds]);

  // --- markers ------------------------------------------------------------
  useEffect(() => {
    if (!ready || !leftMapRef.current || !rightMapRef.current) return;
    const left = leftMapRef.current;
    const right = rightMapRef.current;

    markersRef.current.forEach((pair, id) => {
      if (!pins.some((pin) => pin.id === id)) {
        left.removeLayer(pair[0]);
        right.removeLayer(pair[1]);
        markersRef.current.delete(id);
      }
    });

    pins.forEach((pin) => {
      const icon = pin.id === activePinId ? ACTIVE_PIN_ICON : PIN_ICON;
      const existing = markersRef.current.get(pin.id);
      if (existing) {
        existing.forEach((marker) => {
          marker.setLatLng([pin.latitude, pin.longitude]);
          marker.setIcon(icon);
        });
        return;
      }
      const tooltip = `${pin.label}<br/>${pin.latitude.toFixed(5)}, ${pin.longitude.toFixed(5)}`;
      const leftMarker = L.marker([pin.latitude, pin.longitude], { icon, keyboard: true })
        .addTo(left)
        .bindTooltip(tooltip)
        .on('click', () => onPinSelect(pin.id));
      const rightMarker = L.marker([pin.latitude, pin.longitude], { icon })
        .addTo(right)
        .bindTooltip(tooltip)
        .on('click', () => onPinSelect(pin.id));
      markersRef.current.set(pin.id, [leftMarker, rightMarker]);
    });
  }, [ready, pins, activePinId, onPinSelect]);

  // --- focus + resize -----------------------------------------------------
  useEffect(() => {
    if (!ready || !focus || !leftMapRef.current) return;
    leftMapRef.current.setView([focus.latitude, focus.longitude], focus.zoom ?? leftMapRef.current.getZoom());
  }, [ready, focus]);

  useEffect(() => {
    if (!ready) return;
    const invalidate = () => {
      leftMapRef.current?.invalidateSize();
      rightMapRef.current?.invalidateSize();
    };
    invalidate();
    const timer = window.setTimeout(invalidate, 260);
    window.addEventListener('resize', invalidate);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('resize', invalidate);
    };
  }, [ready, mode, comparisonLayerId]);

  // --- splitter dragging --------------------------------------------------
  const onSplitterDown = (event: React.PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    draggingRef.current = true;
    (event.target as HTMLElement).setPointerCapture(event.pointerId);
  };

  const onSplitterMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return;
    const host = event.currentTarget.parentElement;
    if (!host) return;
    const bounds = host.getBoundingClientRect();
    const percent = ((event.clientX - bounds.left) / bounds.width) * 100;
    setSplitPercent(Math.min(96, Math.max(4, percent)));
  };

  const onSplitterUp = (event: React.PointerEvent<HTMLDivElement>) => {
    draggingRef.current = false;
    (event.target as HTMLElement).releasePointerCapture(event.pointerId);
  };

  const comparatorActive = mode !== 'off' && rightStackIds.length > 0;
  const leftStyle: React.CSSProperties =
    comparatorActive && mode === 'split' ? { width: `${splitPercent}%` } : { width: '100%' };
  const rightStyle: React.CSSProperties = comparatorActive
    ? mode === 'split'
      ? { left: `${splitPercent}%`, width: `${100 - splitPercent}%` }
      : { left: 0, width: '100%', clipPath: `inset(0 0 0 ${splitPercent}%)` }
    : { display: 'none' };

  return (
    <div className="relative h-full w-full overflow-hidden bg-black">
      <div ref={leftHostRef} className="absolute inset-y-0 left-0" style={leftStyle} />
      <div ref={rightHostRef} className="absolute inset-y-0" style={rightStyle} />
      {comparatorActive && (
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Comparator splitter"
          aria-valuenow={Math.round(splitPercent)}
          className="comparator-splitter"
          style={{ left: `${splitPercent}%` }}
          onPointerDown={onSplitterDown}
          onPointerMove={onSplitterMove}
          onPointerUp={onSplitterUp}
        >
          <span className="comparator-splitter__grip">⇔</span>
        </div>
      )}
    </div>
  );
}
