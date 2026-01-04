import { api } from "./api";

export interface SpeciesSearchResult {
  speciesName: string;
  commonName: string;
}

export async function searchSpecies(
  query: string,
): Promise<SpeciesSearchResult[]> {
  try {
    const response = await api.get<SpeciesSearchResult[]>(
      `v1/species/search/?q=${encodeURIComponent(query)}`,
    );
    return response.data;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error("Error searching species:", error);
    throw error;
  }
}
