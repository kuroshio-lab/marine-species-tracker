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
import { MiniObservationCard } from "@kuroshio-lab/components";
import { GeoJsonFeature } from "../types/geojson";
import { Observation } from "../types/observation";
import { fetchMapObservations } from "../lib/observation";

interface MapComponentProps {
  selectedObservation: Observation | null;
  zIndex?: number;
  zoomTrigger: number;
  mapRefreshTrigger: number;
  filterSpeciesName: string | null;
  filterCommonName: string | null;
  filterMinDate: string | null;
  filterMaxDate: string | null;
}

const externalIcon = L.divIcon({
  className: "custom-external-marker",
  html: `<div style="background-color: hsl(var(--brand-primary-700)); border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.3); width: 12px; height: 12px; border-radius: 50%;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -8],
});

const validatedUserIcon = L.divIcon({
  className: "custom-user-marker",
  html: `<div style="background-color: hsl(var(--semantic-success-500)); border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.3); width: 12px; height: 12px; border-radius: 50%;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -8],
});

const pendingUserIcon = L.divIcon({
  className: "custom-pending-marker",
  html: `<div style="background-color: hsl(var(--semantic-warning-500)); border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.3); width: 12px; height: 12px; border-radius: 50%;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -8],
});

export default function MapComponent({
  selectedObservation,
  zIndex,
  zoomTrigger,
  mapRefreshTrigger,
  filterSpeciesName,
  filterCommonName,
  filterMinDate,
  filterMaxDate,
}: MapComponentProps) {
  const defaultPosition: [number, number] = [0, 0];
  const [allMapObservations, setAllMapObservations] = useState<
    GeoJsonFeature[]
  >([]);
  const [isMounted, setIsMounted] = useState(false);

  const mapRef = useRef<L.Map | null>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastRequestParamsRef = useRef<string>("");
  const isLoadingRef = useRef<boolean>(false);
  const initialLoadDoneRef = useRef<boolean>(false);
  const openPopupRef = useRef<L.Popup | null>(null);
  const isAutoPanningForPopupRef = useRef<boolean>(false);

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

  const loadAllMapObservations = useCallback(
    async (force = false): Promise<void> => {
      // CRITICAL: Skip if we're auto-panning for a popup - this prevents popup from closing
      if (isAutoPanningForPopupRef.current && !force) {
        return;
      }

      // Wait a bit for map to initialize if it's not ready
      if (!mapRef.current) {
        return;
      }

      const center = mapRef.current.getCenter();
      const zoom = mapRef.current.getZoom();
      const currentRadius = calculateRadius(zoom);

      // Create a unique key for this request
      const requestKey = `${center.lat.toFixed(4)}_${center.lng.toFixed(4)}_${zoom}_${currentRadius ?? "global"}`;

      // Skip if this is the same request as the last one (unless forced)
      if (!force && requestKey === lastRequestParamsRef.current) {
        return;
      }

      // Skip if already loading
      if (isLoadingRef.current) {
        return;
      }

      try {
        isLoadingRef.current = true;
        lastRequestParamsRef.current = requestKey;

        const params: {
          lat: number;
          lng: number;
          radius?: number;
          limit: number;
          offset: number;
          speciesName?: string;
          commonName?: string;
          minDate?: string;
          maxDate?: string;
        } = {
          lat: center.lat,
          lng: center.lng,
          limit: 500,
          offset: 0,
        };

        if (currentRadius !== undefined) {
          params.radius = currentRadius;
        }
        if (filterSpeciesName) params.speciesName = filterSpeciesName;
        if (filterCommonName) params.commonName = filterCommonName;
        if (filterMinDate) params.minDate = filterMinDate;
        if (filterMaxDate) params.maxDate = filterMaxDate;

        const data = await fetchMapObservations(params);

        if (isAutoPanningForPopupRef.current && !force) {
          return;
        }

        setAllMapObservations(data.features);
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Failed to fetch all map observations:", error);
        // Reset last request params on error so we can retry
        lastRequestParamsRef.current = "";
      } finally {
        isLoadingRef.current = false;
      }
    },
    [
      calculateRadius,
      filterSpeciesName,
      filterCommonName,
      filterMinDate,
      filterMaxDate,
    ],
  );

  useEffect(() => {
    setIsMounted(true);
    // Wait a bit for the map to initialize before loading observations
    const timer = setTimeout(() => {
      loadAllMapObservations(true); // Force initial load
    }, 200);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    mapRefreshTrigger,
    filterSpeciesName,
    filterCommonName,
    filterMinDate,
    filterMaxDate,
  ]);

  useEffect(() => {
    if (mapRef.current && selectedObservation) {
      const [lng, lat] = selectedObservation.location.coordinates;
      mapRef.current.flyTo([lat, lng], 4);
      // Trigger a reload after flying to a selected observation
      // Use a small delay to ensure the map has finished animating
      const timer = setTimeout(() => {
        loadAllMapObservations(true); // Force reload after flyTo
      }, 500);
      return () => clearTimeout(timer);
    }
    return () => {};
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedObservation, zoomTrigger, loadAllMapObservations]);

  // Hook to handle map events for dynamic loading with debouncing
  function MapEventsHandler() {
    useMapEvents({
      zoomend: () => {
        // Skip if we're auto-panning for a popup
        if (isAutoPanningForPopupRef.current) {
          return;
        }
        // Clear any pending debounce timer
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
        // Debounce the request by 300ms
        debounceTimerRef.current = setTimeout(() => {
          loadAllMapObservations();
        }, 300);
      },
      moveend: () => {
        // Skip if we're auto-panning for a popup OR if a popup is currently open
        // This prevents reloads when popup is open, even if flag was reset
        if (isAutoPanningForPopupRef.current || openPopupRef.current) {
          return;
        }
        // Clear any pending debounce timer
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
        // Debounce the request by 300ms
        debounceTimerRef.current = setTimeout(() => {
          loadAllMapObservations();
        }, 300);
      },
    });
    return null;
  }

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

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
        // Load observations once map is ready (only once)
        if (mapRef.current && !initialLoadDoneRef.current) {
          initialLoadDoneRef.current = true;
          setTimeout(() => {
            loadAllMapObservations(true);
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
              <Marker
                key={markerKey}
                position={pos}
                icon={markerIcon}
                eventHandlers={{
                  click: (e) => {
                    // CRITICAL: Clear any pending debounced observation reloads
                    if (debounceTimerRef.current) {
                      clearTimeout(debounceTimerRef.current);
                      debounceTimerRef.current = null;
                    }

                    // Get marker position before popup opens
                    const marker = e.target;

                    // Close any previously open popup
                    if (
                      openPopupRef.current &&
                      openPopupRef.current !== marker.getPopup()
                    ) {
                      openPopupRef.current.close();
                    }
                    // Track the newly opened popup
                    const popup = marker.getPopup();
                    if (popup) {
                      openPopupRef.current = popup;
                    }
                  },
                }}
              >
                <Popup
                  className={popupClassName}
                  autoPan
                  autoPanPadding={[200, 200]}
                  autoPanPaddingTopLeft={[200, 200]}
                  autoPanPaddingBottomRight={[200, 200]}
                  keepInView
                  closeOnClick={false}
                  autoClose={false}
                  eventHandlers={{
                    remove: () => {
                      // Clear reference when popup is closed
                      if (openPopupRef.current) {
                        openPopupRef.current = null;
                      }
                    },
                  }}
                >
                  <MiniObservationCard
                    observation={{
                      id: feature.id as number,
                      speciesName: feature.properties.speciesName,
                      commonName: feature.properties.commonName ?? null,
                      observationDatetime:
                        feature.properties.observationDatetime,
                      locationName: feature.properties.locationName ?? "",
                      machineObservation:
                        feature.properties.machineObservation ?? null,
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
