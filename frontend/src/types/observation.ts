export interface Observation {
  id: number;
  userId: number;
  speciesName: string;
  commonName: string | null;
  location: {
    type: "Point";
    coordinates: [number, number];
  };
  observationDatetime: string;
  locationName: string;
  machineObservation: string;
  depthMin: number | null;
  depthMax: number | null;
  bathymetry: number | null;
  temperature: number | null;
  visibility: number | null;
  notes: string | null;
  image: string | null;
  validated: "pending" | "validated" | "rejected";
  source: "user" | "obis" | "other";
  sex: "male" | "female" | "unknown" | null;
  createdAt: string;
  updatedAt: string;
  username: string | null;
}
