// frontend/src/components/UserObservationSection.tsx

"use client";

import dynamic from "next/dynamic";
import React, { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import ObservationModal from "./ObservationModal";
import { ObservationCard } from "./ObservationCard";
import { ObservationFilterAndSort } from "./ObservationFilterAndSort";
import { useUser } from "./UserProvider";

import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { fetchUserObservations, deleteObservation } from "../lib/observation";
import { Observation } from "../types/observation";
import Loader from "./Loader";
import { Button } from "./ui/button";

interface UserObservationSectionProps {
  className?: string;
}

const DynamicMapComponent = dynamic(() => import("./MapComponent"), {
  ssr: false,
});

const renderObservationListContent = (
  isLoading: boolean,
  error: string | null,
  observations: Observation[],
  onSelectObservation: (observation: Observation) => void,
  onDeleteObservation: (observationId: number) => void,
  onEditObservationClick: (observation: Observation) => void,
) => {
  if (isLoading) {
    return <Loader isLoading />;
  }
  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }
  if (observations.length === 0) {
    return (
      <p className="p-4">No observations found. Start by adding a new one!</p>
    );
  }
  return observations.map((observation: Observation, index: number) => (
    <ObservationCard
      key={observation.id}
      observation={observation}
      onSelectObservation={onSelectObservation}
      onDeleteObservation={onDeleteObservation}
      onEditObservationClick={onEditObservationClick}
      className={index < observations.length - 1 ? "mb-2" : ""}
    />
  ));
};

function UserObservationSection({ className }: UserObservationSectionProps) {
  const { user, loading: isUserLoading } = useUser();
  const [observations, setObservations] = useState<Observation[]>([]); // This state holds the observations for both the list and the map
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedObservation, setSelectedObservation] =
    useState<Observation | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [zoomTrigger, setZoomTrigger] = useState(0);
  const [mapRefreshTrigger, setMapRefreshTrigger] = useState(0);
  const [displayObservations, setDisplayObservations] = useState<Observation[]>(
    [],
  );

  const loadObservations = useCallback(async () => {
    if (!user) {
      setIsLoading(false);
      setObservations([]);
      setDisplayObservations([]);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const userObservations = await fetchUserObservations();
      setObservations(userObservations);
      setDisplayObservations(userObservations);
    } catch (err) {
      const errorMessage = "Failed to load observations.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const handleFilteredObservationsChange = useCallback(
    (filteredList: Observation[]) => {
      setDisplayObservations(filteredList);
    },
    [], // Empty dependency array means this function is created once
  );

  const handleSelectObservation = useCallback((observation: Observation) => {
    if (observation.validated !== "rejected") {
      setSelectedObservation(observation);
      setZoomTrigger((prev) => prev + 1);
    } else {
      // eslint-disable-next-line no-console
      console.log("Rejected observations cannot be selected for zooming.");
    }
  }, []);

  const handleDeleteObservation = useCallback(
    async (observationId: number) => {
      if (!user) {
        // eslint-disable-next-line no-console
        console.warn("User not logged in. Cannot delete observation.");
        return;
      }
      try {
        await deleteObservation(observationId);
        await loadObservations();
        if (selectedObservation && selectedObservation.id === observationId) {
          setSelectedObservation(null);
        }
        setMapRefreshTrigger((prev) => prev + 1);
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error("Failed to delete observation:", err);
        setError("Failed to delete observation.");
      }
    },
    [user, loadObservations, selectedObservation, setMapRefreshTrigger],
  );

  const handleEditObservationClick = useCallback((observation: Observation) => {
    setSelectedObservation(observation);
    setModalMode("edit");
    setIsModalOpen(true);
  }, []);

  const handleAddObservationClick = () => {
    setSelectedObservation(null);
    setModalMode("add");
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleObservationUpserted = () => {
    loadObservations();
    setMapRefreshTrigger((prev) => prev + 1);
    setIsModalOpen(false);
  };

  useEffect(() => {
    if (!isUserLoading) {
      loadObservations();
    }
  }, [loadObservations, isUserLoading]);

  if (isUserLoading) {
    return (
      <section id="user-observations" className="container mx-auto py-8">
        <h2 className="text-3xl font-bold mb-6">Your Observations</h2>
        <Loader isLoading />
        <p className="text-center mt-4">Loading user data...</p>
      </section>
    );
  }

  if (!user) {
    return (
      <section id="user-observations" className="container mx-auto py-8">
        <h2 className="text-3xl font-bold mb-6">Your Observations</h2>
        <p>Please log in to view your observations.</p>
      </section>
    );
  }

  return (
    <div
      className={cn(
        "border rounded-lg bg-white p-2 grid grid-cols-1 md:grid-cols-3 w-full h-full overflow-hidden",
        className,
      )}
    >
      <div className="md:col-span-2 h-full">
        <div
          style={{ position: "relative" }}
          className="h-full bg-white rounded-lg overflow-hidden"
        >
          <DynamicMapComponent
            selectedObservation={selectedObservation}
            zIndex={isModalOpen ? 0 : 1}
            zoomTrigger={zoomTrigger}
            mapRefreshTrigger={mapRefreshTrigger}
          />
          <div
            className="absolute top-4 right-4 z-[1000] p-2 pointer-events-auto"
            style={{ display: "flex", gap: 8 }}
          >
            <Button variant="addingObs" onClick={handleAddObservationClick}>
              Add Observation
            </Button>
          </div>
        </div>
      </div>
      <div className="md:col-span-1 h-full flex flex-col overflow-hidden">
        <Card className="rounded-none shadow-none border-none flex-grow flex flex-col overflow-hidden">
          <CardHeader className="pr-0">
            <CardTitle className="flex justify-between items-center">
              Observations ({displayObservations.length})
              <ObservationFilterAndSort
                observations={observations}
                onFilteredObservationsChange={handleFilteredObservationsChange}
              />
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-grow overflow-hidden pr-0">
            <ScrollArea className="h-full pr-4">
              {renderObservationListContent(
                isLoading,
                error,
                displayObservations,
                handleSelectObservation,
                handleDeleteObservation,
                handleEditObservationClick,
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
      <ObservationModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onObservationUpserted={handleObservationUpserted}
        mode={modalMode}
        observation={modalMode === "edit" ? selectedObservation : null}
      />
    </div>
  );
}

export default UserObservationSection;
