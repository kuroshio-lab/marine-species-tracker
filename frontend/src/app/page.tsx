// frontend/src/app/page.tsx

"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  Header,
  UserObservationSection,
  ObservationCard,
  ObservationFilterAndSort,
  ObservationModal,
  SpeciesSearch,
  Loader,
  UserRoleBadge,
  useUser,
} from "@kuroshio-lab/components";
import FilterModal from "../components/FilterModal";
import { useLoading } from "../hooks/useLoading";
import {
  fetchUserObservations,
  deleteObservation,
  createObservation,
  updateObservation,
} from "../lib/observation";
import { searchSpecies } from "../lib/species";

const DynamicMapComponent = dynamic(
  () => import("../components/MapComponent"),
  { ssr: false },
);

const DNA = dynamic(
  () => import("react-loader-spinner").then((m) => ({ default: m.DNA })),
  { ssr: false },
);

type BoundSpeciesSearchProps = Omit<
  React.ComponentProps<typeof SpeciesSearch>,
  "onSearch"
>;

// Bind SpeciesSearch with the local search function
function BoundSpeciesSearch({
  value,
  onChange,
  onBlur,
  disabled,
  placeholder,
  error,
  id,
}: BoundSpeciesSearchProps) {
  return (
    <SpeciesSearch
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      disabled={disabled}
      placeholder={placeholder}
      error={error}
      id={id}
      onSearch={searchSpecies}
    />
  );
}

// DNA loader for the Loader component
function DNALoaderComponent() {
  return (
    <DNA
      visible
      height="80"
      width="80"
      ariaLabel="dna-loading"
      wrapperStyle={{}}
      wrapperClass="dna-wrapper"
    />
  );
}

// Loader that uses the design system Loader with DNA spinner
function BoundLoader({ isLoading }: { isLoading: boolean }) {
  return <Loader isLoading={isLoading} LoaderComponent={DNALoaderComponent} />;
}

interface ObservationFormData {
  speciesName: string;
  commonName?: string | null;
  locationName: string;
  latitude: number;
  longitude: number;
  observationDatetime: string;
  depthMin?: number | null;
  depthMax?: number | null;
  bathymetry?: number | null;
  temperature?: number | null;
  visibility?: number | null;
  notes?: string | null;
  sex?: "male" | "female" | "unknown";
}

type TrackerObservationModalProps = Omit<
  React.ComponentProps<typeof ObservationModal>,
  "onSubmit" | "SpeciesSearchComponent"
>;

// Wrapper for ObservationModal that binds tracker-specific API logic
function TrackerObservationModal({
  mode,
  observation,
  isOpen,
  onClose,
  onObservationUpserted,
}: TrackerObservationModalProps) {
  const { user } = useUser();

  const handleSubmit = async (data: ObservationFormData) => {
    if (mode === "edit" && observation) {
      await updateObservation(observation.id, {
        speciesName: data.speciesName,
        commonName: data.commonName || null,
        locationName: data.locationName,
        location: {
          type: "Point" as const,
          coordinates: [data.longitude, data.latitude] as [number, number],
        },
        observationDatetime: data.observationDatetime
          ? new Date(data.observationDatetime).toISOString()
          : undefined,
        depthMin: data.depthMin ?? null,
        depthMax: data.depthMax ?? null,
        bathymetry: data.bathymetry ?? null,
        temperature: data.temperature ?? null,
        visibility: data.visibility ?? null,
        notes: data.notes ?? null,
        sex: data.sex ?? "unknown",
      });
    } else {
      await createObservation({
        speciesName: data.speciesName,
        commonName: data.commonName || null,
        locationName: data.locationName,
        latitude: data.latitude,
        longitude: data.longitude,
        observationDatetime: new Date(data.observationDatetime).toISOString(),
        depthMin: data.depthMin ?? null,
        depthMax: data.depthMax ?? null,
        bathymetry: data.bathymetry ?? null,
        temperature: data.temperature ?? null,
        visibility: data.visibility ?? null,
        notes: data.notes ?? null,
        sex: data.sex ?? "unknown",
        userId: user!.id,
        username: user!.username,
        machineObservation: "User Observation",
      });
    }
  };

  return (
    <ObservationModal
      isOpen={isOpen}
      onClose={onClose}
      onObservationUpserted={onObservationUpserted}
      mode={mode}
      observation={observation}
      onSubmit={handleSubmit}
      SpeciesSearchComponent={BoundSpeciesSearch}
    />
  );
}

// The local Observation uses `null` for optional fields while the design system
// expects `undefined`. This adapter normalises the two shapes at the boundary.
async function fetchBoundObservations() {
  const observations = await fetchUserObservations();
  return observations.map(({ commonName, image, username, ...rest }) => ({
    ...rest,
    commonName: commonName ?? undefined,
    image: image ?? undefined,
    username: username ?? undefined,
  }));
}

export default function Home() {
  const { startLoading, stopLoading } = useLoading();
  const { user, loading, logout } = useUser();

  const [activeFilters, setActiveFilters] = useState<{
    speciesName: string | null;
    commonName: string | null;
    minDate: string | null;
    maxDate: string | null;
  }>({ speciesName: null, commonName: null, minDate: null, maxDate: null });

  useEffect(() => {
    const fetchData = async () => {
      startLoading();
      try {
        await new Promise((resolve) => {
          setTimeout(resolve, 2000);
        });
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Failed to fetch data:", error);
      } finally {
        stopLoading();
      }
    };

    fetchData();
  }, [startLoading, stopLoading]);

  return (
    <main className="h-screen flex flex-col overflow-hidden bg-background">
      <Header
        onApplyFilters={setActiveFilters}
        initialFilters={activeFilters}
        user={user}
        loading={loading}
        onLogout={logout}
        FilterModalComponent={FilterModal}
        UserRoleBadgeComponent={UserRoleBadge}
      />

      <div className="flex-1 w-full p-4 overflow-hidden">
        <UserObservationSection
          className="h-full"
          filterSpeciesName={activeFilters.speciesName}
          filterCommonName={activeFilters.commonName}
          filterMinDate={activeFilters.minDate}
          filterMaxDate={activeFilters.maxDate}
          ObservationModalComponent={TrackerObservationModal}
          ObservationCardComponent={ObservationCard}
          ObservationFilterAndSortComponent={ObservationFilterAndSort}
          LoaderComponent={BoundLoader}
          MapComponent={DynamicMapComponent}
          onFetchObservations={fetchBoundObservations}
          onDeleteObservation={deleteObservation}
        />
      </div>
    </main>
  );
}
