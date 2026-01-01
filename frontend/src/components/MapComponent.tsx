// frontend/src/app/MapComponent.tsx

"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useState, useEffect, useRef, useCallback } from "react";
import { GeoJsonFeature } from "../types/geojson";

import { Observation } from "../types/observation";
import { fetchMapObservations } from "../lib/observation";
import { MiniObservationCard } from "./MiniObservationCard";

interface MapComponentProps {
  selectedObservation: Observation | null;
  zIndex?: number;
  zoomTrigger: number;
  mapRefreshTrigger: number;
}

const externalIcon = L.divIcon({
  className: "custom-external-marker",
  html: '<div style="background-color: hsl(var(--brand-primary-700)); width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff;"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -8],
});

const validatedUserIcon = L.divIcon({
  className: "custom-user-marker",
  html: '<div style="background-color: hsl(var(--brand-primary-500)); width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff;"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -8],
});

const pendingUserIcon = L.divIcon({
  className: "custom-pending-marker",
  html: '<div style="background-color: hsl(var(--brand-primary-300)); width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff;"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -8],
});

export default function MapComponent({
  selectedObservation,
  zIndex,
  zoomTrigger,
  mapRefreshTrigger,
}: MapComponentProps) {
  // Make sure selectedObservation is destructured
  const defaultPosition: [number, number] = [0, 0];
  const [allMapObservations, setAllMapObservations] = useState<
    GeoJsonFeature[]
  >([]);
  const [isMounted, setIsMounted] = useState(false);

  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (mapRef.current && selectedObservation) {
      const [lng, lat] = selectedObservation.location.coordinates;
      mapRef.current.flyTo([lat, lng], 4);
    }
  }, [selectedObservation, zoomTrigger]);

  useEffect(() => {
    if (mapRef.current && selectedObservation) {
      const [lng, lat] = selectedObservation.location.coordinates;
      mapRef.current.flyTo([lat, lng], 4);
    }
  }, [selectedObservation, zoomTrigger]);

  const loadAllMapObservations = useCallback(async () => {
    try {
      const data = await fetchMapObservations();
      setAllMapObservations(data.features);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("Failed to fetch all map observations:", error);
    }
  }, []);

  useEffect(() => {
    setIsMounted(true);
    loadAllMapObservations();
  }, [loadAllMapObservations, mapRefreshTrigger]);

  if (!isMounted) {
    return null;
  }

  const allObservations = allMapObservations.filter(
    (feature) => feature.properties.validated !== "rejected",
  );

  return (
    <MapContainer
      center={defaultPosition}
      zoom={2}
      minZoom={2} // Prevents zooming out too far
      worldCopyJump
      scrollWheelZoom
      className="h-full w-full"
      style={{ zIndex }}
      ref={mapRef}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        noWrap={false}
      />
      {allObservations &&
        allObservations.length > 0 &&
        allObservations.map((feature) => {
          const [lng, lat] = feature.geometry.coordinates;
          // We define 3 positions for every marker so they repeat with the map banner
          const positions: [number, number][] = [
            [lat, lng], // Original
            [lat, lng + 360], // Right copy
            [lat, lng - 360], // Left copy
          ];
          return positions.map((pos) => {
            const markerKey = `${feature.id}-${pos[1]}`;
            // Determine the class for the Popup based on observation status and source
            let popupClassName = "";
            if (feature.properties.source === "user") {
              switch (feature.properties.validated) {
                case "validated":
                  popupClassName = "popup-validated";
                  break;
                case "pending":
                  popupClassName = "popup-pending";
                  break;
                default:
                  popupClassName = ""; // No specific class for default or unknown status
              }
            } else {
              popupClassName = "popup-external";
            }

            let markerIcon;
            if (feature.properties.source === "user") {
              if (feature.properties.validated === "validated") {
                markerIcon = validatedUserIcon;
              } else if (feature.properties.validated === "pending") {
                markerIcon = pendingUserIcon;
              } else {
                // This covers 'rejected' and any other unhandled user statuses
                markerIcon = externalIcon;
              }
            } else {
              // For non-user sources
              markerIcon = externalIcon;
            }

            return (
              <Marker key={markerKey} position={pos} icon={markerIcon}>
                <Popup className={popupClassName}>
                  <MiniObservationCard
                    observation={{
                      id: feature.id as number,
                      speciesName: feature.properties.speciesName,
                      commonName: feature.properties.commonName ?? null,
                      observationDatetime:
                        feature.properties.observationDatetime,
                      locationName: feature.properties.locationName ?? null,
                      source: feature.properties.source,
                      image: feature.properties.image ?? null,
                      depthMin: feature.properties.depthMin ?? null,
                      depthMax: feature.properties.depthMax ?? null,
                      bathymetry: feature.properties.bathymetry ?? null,
                      temperature: feature.properties.temperature ?? null,
                      visibility: feature.properties.visibility ?? null,
                      sex: feature.properties.sex ?? null,
                      notes: feature.properties.notes ?? null,
                      validated: feature.properties.validated,
                      location: feature.geometry,
                      userId: feature.properties.userId ?? null,
                      username: feature.properties.username ?? null,
                      createdAt: feature.properties.created_at ?? null,
                      updatedAt: feature.properties.updated_at ?? null,
                    }}
                  />
                </Popup>
              </Marker>
            );
          });
        })}
    </MapContainer>
  );
}
