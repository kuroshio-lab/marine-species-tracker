// frontend/src/components/MiniObservationCard.tsx
import React from "react";
import Image from "next/image";
import { format } from "date-fns";
import { Observation } from "../types/observation";
import { cn, formatDepth } from "../lib/utils";

interface MiniObservationCardProps {
  observation: Observation;
}

function MiniObservationCard({ observation }: MiniObservationCardProps) {
  const isUser = observation.source === "user";
  const status = observation.validated;

  // Aligning border color with the map marker color
  const getBorderColor = () => {
    if (!isUser) return "border-brand-primary-700";
    if (status === "validated") return "border-semantic-success-500";
    return "border-semantic-warning-500";
  };

  return (
    <div className={cn("p-1 min-w-[180px]", getBorderColor())}>
      <h3 className="font-bold text-sm border-b pb-1">
        {observation.speciesName}
        {observation.commonName && (
          <span className="block text-[10px] font-normal text-muted-foreground italic">
            ({observation.commonName})
          </span>
        )}
      </h3>

      {observation.image && (
        <div className="relative h-24 w-full">
          <Image
            src={observation.image}
            fill
            className="object-cover rounded-sm"
            loading="lazy"
            alt=""
          />
        </div>
      )}

      <div className="space-y-1 text-[11px] leading-tight">
        {isUser && observation.username && (
          <p className="font-semibold text-brand-primary-700">
            👤 Spotted by: {observation.username}
          </p>
        )}
        <p>
          <strong>Type:</strong> {observation.machineObservation}
        </p>
        <p>
          <strong>Date:</strong>{" "}
          {format(
            new Date(observation.observationDatetime),
            "dd/MM/yyyy HH:mm",
          )}
        </p>

        {/* All technical data preserved */}
        <div className="grid grid-cols-1 gap-0.25 mt-1 pt-1 border-t border-dashed">
          {observation.depthMin !== null && (
            <p>
              🌊 Depth:{" "}
              {formatDepth(observation.depthMin, observation.depthMax)}
            </p>
          )}
          {observation.bathymetry !== null && (
            <p>📉 Bathy: {observation.bathymetry}m</p>
          )}
          {observation.temperature !== null && (
            <p>🌡️ Temp: {observation.temperature}°C</p>
          )}
          {observation.visibility !== null && (
            <p>👁️ Vis: {observation.visibility}m</p>
          )}
          {observation.sex && <p>⚧ Sex: {observation.sex}</p>}
        </div>

        {observation.notes && (
          <p className="mt-1 italic text-muted-foreground border-l-2 pl-1 font-serif">
            &quot;{observation.notes}&quot;
          </p>
        )}

        <p className="mt-2 text-[9px] uppercase font-bold text-right opacity-70">
          Source: {observation.source}
        </p>
      </div>
    </div>
  );
}

export { MiniObservationCard };
