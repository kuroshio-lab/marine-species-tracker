// frontend/src/app/page.tsx

"use client";

import React, { useEffect, useState } from "react";
import { useLoading } from "../hooks/useLoading";
import UserObservationSection from "../components/UserObservationSection";
import Header from "../components/Header";
import { useUser } from "../components/UserProvider";

export default function Home() {
  const { startLoading, stopLoading } = useLoading();
  const { user, loading: isUserLoading } = useUser(); // Get user and loading state

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

  // Conditional rendering for Header, based on user login status
  const shouldShowHeader = !isUserLoading && user;

  return (
    <main className="h-screen flex flex-col">
      {shouldShowHeader && (
        <Header
          onApplyFilters={setActiveFilters}
          initialFilters={activeFilters}
        />
      )}
      <div className="mx-auto max-w-[2560px] h-full max-h-[1076px] w-full p-4">
        <UserObservationSection
          className="h-full"
          filterSpeciesName={activeFilters.speciesName}
          filterCommonName={activeFilters.commonName}
          filterMinDate={activeFilters.minDate}
          filterMaxDate={activeFilters.maxDate}
        />
      </div>
    </main>
  );
}
