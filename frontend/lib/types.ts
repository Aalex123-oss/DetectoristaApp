export type LayerGroup = 'basemap' | 'lidar' | 'historical' | 'overlay';

export interface LayerDefinition {
  id: string;
  name: string;
  group: LayerGroup;
  kind: 'tile' | 'wms';
  url: string;
  attribution: string;
  description: string;
  default_opacity: number;
  default_visible: boolean;
  max_zoom: number;
  epoch: number | null;
  wms_layers: string | null;
  wms_format: string | null;
  wms_transparent: boolean | null;
  supports_intensity: boolean;
  requires_token: boolean;
}

export interface ParsedCoordinate {
  latitude: number;
  longitude: number;
  format: 'decimal' | 'dms' | 'utm' | 'mgrs-like';
  normalized: string;
  utm: string | null;
}

export interface GeocodeResult {
  display_name: string;
  latitude: number;
  longitude: number;
  kind: string | null;
  bounding_box: number[] | null;
  source: string;
}

export interface SearchResponse {
  query: string;
  interpretation: 'coordinate' | 'place';
  coordinate: ParsedCoordinate | null;
  results: GeocodeResult[];
}

export interface CoordinateFormats {
  decimal: string;
  dms: string;
  utm: string;
}

export type Era = 'Prehistoric' | 'Ancient' | 'Medieval' | 'Industrial' | 'Modern';

export interface Source {
  provider: 'wikipedia' | 'europeana' | 'internet_archive' | 'nominatim' | 'llm';
  title: string;
  url: string;
  snippet: string | null;
  year: number | null;
  distance_meters: number | null;
  creator: string | null;
}

export interface TimelineEntry {
  year: number | null;
  label: string;
  era: Era;
  description: string;
  source_url: string | null;
}

export interface EraNarrative {
  era: Era;
  summary: string;
  evidence_count: number;
}

export interface ArchaeologicalPotential {
  rating: 'High' | 'Medium' | 'Low';
  score: number;
  confidence: 'high' | 'medium' | 'low';
  markers: string[];
  rationale: string;
}

export interface ReverseGeocodeResult {
  display_name: string;
  source: 'nominatim' | 'photon';
  place_name: string | null;
  county: string | null;
  state: string | null;
  country: string | null;
  country_code: string | null;
  osm_type: string | null;
}

export interface HistoricalReport {
  location: { latitude: number; longitude: number };
  place_label: string;
  administrative_context: ReverseGeocodeResult | null;
  narrative: string;
  era_breakdown: EraNarrative[];
  archaeological_potential: ArchaeologicalPotential;
  timeline: TimelineEntry[];
  sources: Source[];
  synthesis_engine: 'heuristic' | 'llm';
  provider_status: Record<string, string>;
  generated_at: string;
  cached: boolean;
}

export interface AnalysisPin {
  id: string;
  latitude: number;
  longitude: number;
  label: string;
  formats: CoordinateFormats | null;
  createdAt: string;
}

export interface LayerState {
  visible: boolean;
  opacity: number;
  intensity: number;
  ramp: RampId;
}

export type RampId = 'natural' | 'grayscale' | 'terrain' | 'inverted' | 'contrast';

export type ComparatorMode = 'off' | 'swipe' | 'split';
