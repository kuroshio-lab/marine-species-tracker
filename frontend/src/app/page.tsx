// frontend/src/app/page.tsx

"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useLoading } from "../hooks/useLoading";
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
import { DNA } from "react-loader-spinner";
import FilterModal from "../components/FilterModal";
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

// Bind SpeciesSearch with the local search function
function BoundSpeciesSearch(props: any) {
  return <SpeciesSearch {...props} onSearch={searchSpecies} />;
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

// Wrapper for ObservationModal that binds tracker-specific API logic
function TrackerObservationModal(props: any) {
  const { user } = useUser();

  const handleSubmit = async (data: any) => {
    if (props.mode === "edit" && props.observation) {
      await updateObservation(props.observation.id, {
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
      {...props}
      onSubmit={handleSubmit}
      SpeciesSearchComponent={BoundSpeciesSearch}
    />
  );
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
          onFetchObservations={fetchUserObservations}
          onDeleteObservation={deleteObservation}
        />
      </div>
    </main>
  );
}
