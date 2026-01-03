// frontend/src/app/MapComponent.tsx

"use client";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMapEvents,
} from "react-leaflet";
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
  const defaultPosition: [number, number] = [0, 0];
  const [allMapObservations, setAllMapObservations] = useState<
    GeoJsonFeature[]
  >([]);
  const [isMounted, setIsMounted] = useState(false);

  const mapRef = useRef<L.Map | null>(null);

  // Function to calculate radius based on zoom level
  // Returns undefined for global view (no radius filter)
  const calculateRadius = useCallback((zoom: number): number | undefined => {
    // For very low zoom levels (global view), don't apply radius filter
    if (zoom < 3) return undefined; // Global view - show all observations
    if (zoom < 5) return 20000; // Very large radius for continent-level view
    if (zoom < 7) return 5000; // Large radius for country-level view
    if (zoom < 9) return 1000; // Medium radius for region-level view
    if (zoom < 11) return 200; // Smaller radius for city-level view
    return 50; // Small radius for street-level view
  }, []);

  const loadAllMapObservations = useCallback(async () => {
    // Wait a bit for map to initialize if it's not ready
    if (!mapRef.current) {
      // Retry after a short delay
      setTimeout(() => {
        if (mapRef.current) {
          loadAllMapObservations();
        }
      }, 100);
      return;
    }

    const center = mapRef.current.getCenter();
    const zoom = mapRef.current.getZoom();
    const currentRadius = calculateRadius(zoom);

    try {
      // Pass parameters to the backend
      // For global view (no radius), still send lat/lng for distance ordering
      const params: {
        lat: number;
        lng: number;
        radius?: number;
        limit: number;
        offset: number;
      } = {
        lat: center.lat,
        lng: center.lng,
        limit: 500,
        offset: 0,
      };

      // Only add radius if it's defined (not global view)
      if (currentRadius !== undefined) {
        params.radius = currentRadius;
      }

      const data = await fetchMapObservations(params);
      setAllMapObservations(data.features);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("Failed to fetch all map observations:", error);
    }
  }, [calculateRadius]);

  useEffect(() => {
    setIsMounted(true);
    // Wait a bit for the map to initialize before loading observations
    const timer = setTimeout(() => {
      loadAllMapObservations();
    }, 200);
    return () => clearTimeout(timer);
  }, [loadAllMapObservations, mapRefreshTrigger]);

  useEffect(() => {
    if (mapRef.current && selectedObservation) {
      const [lng, lat] = selectedObservation.location.coordinates;
      mapRef.current.flyTo([lat, lng], 4);
      // Trigger a reload after flying to a selected observation
      // Use a small delay to ensure the map has finished animating
      setTimeout(() => {
        loadAllMapObservations();
      }, 500);
    }
  }, [selectedObservation, zoomTrigger, loadAllMapObservations]);

  // Hook to handle map events for dynamic loading
  function MapEventsHandler() {
    useMapEvents({
      zoomend: () => {
        loadAllMapObservations();
      },
      moveend: () => {
        loadAllMapObservations();
      },
    });
    return null;
  }

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
      minZoom={2}
      maxBounds={[
        [-90, -700],
        [90, 700],
      ]}
      maxBoundsViscosity={1.0}
      worldCopyJump
      scrollWheelZoom
      className="h-full w-full"
      style={{ zIndex }}
      ref={mapRef}
      whenReady={() => {
        // Load observations once map is ready
        if (mapRef.current) {
          setTimeout(() => {
            loadAllMapObservations();
          }, 100);
        }
      }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        noWrap={false}
      />
      <MapEventsHandler />
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
                  popupClassName = "";
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
