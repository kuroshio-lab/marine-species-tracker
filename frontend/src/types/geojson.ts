export interface GeoJsonFeatureProperties {
  id: number | string;
  speciesName: string;
  commonName?: string;
  observationDatetime: string;
  locationName: string;
  machineObservation: string;
  source: "user" | "obis" | "other";

  depthMin: number | null;
  depthMax: number | null;
  bathymetry: number | null;
  temperature: number;
  visibility: number;
  notes: string | null;
  image: string | null;
  validated: "pending" | "validated" | "rejected";
  sex: "male" | "female" | "unknown" | null;
  userId: number;
  created_at: string;
  updated_at: string;
  username?: string | null;
}

export interface GeoJsonFeature {
  id: number | string;
  type: "Feature";
  properties: GeoJsonFeatureProperties;
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
}

export interface GeoJsonFeatureCollection {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

export interface PaginatedGeoJsonFeatures {
  count: number;
  next: string | null;
  previous: string | null;
  results: GeoJsonFeatureCollection;
}
