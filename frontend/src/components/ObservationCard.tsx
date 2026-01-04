// frontend/src/components/ObservationCard.tsx
import React from "react";
import Image from "next/image";
import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Observation } from "../types/observation";
import { cn, formatDepth } from "../lib/utils";

interface ObservationCardProps {
  observation: Observation;
  onSelectObservation: (observation: Observation) => void;
  onDeleteObservation: (observationId: number) => void;
  onEditObservationClick: (observation: Observation) => void;
  className?: string;
}

function ObservationCard({
  observation,
  onSelectObservation,
  onDeleteObservation,
  onEditObservationClick,
  className,
}: ObservationCardProps) {
  const isUser = observation.source === "user";
  const currentStatus = observation.validated || "pending";

  // Visual mapping for Status & Source
  const statusConfig = {
    validated: {
      text: "text-semantic-success-500",
      fill: "fill-semantic-success-500",
      bg: "bg-semantic-success-100",
      border: "border-semantic-success-500",
    },
    pending: {
      text: "text-semantic-warning-500",
      fill: "fill-semantic-warning-500",
      bg: "bg-semantic-warning-100",
      border: "border-semantic-warning-500",
    },
    rejected: {
      text: "text-semantic-error-500",
      fill: "fill-semantic-error-500",
      bg: "bg-semantic-error-100",
      border: "border-semantic-error-500",
    },
  };

  const currentStyles = statusConfig[currentStatus];

  return (
    <Card
      className={cn(
        "group relative overflow-hidden transition-all duration-200 hover:shadow-lg cursor-pointer border-l-8",
        isUser ? currentStyles.border : "border-brand-primary-700",
        className,
      )}
      onClick={() => onSelectObservation(observation)}
    >
      <CardHeader className="p-4 pb-2">
        <div className="flex justify-between items-start gap-2">
          <div className="space-y-1">
            <CardTitle className="text-xl font-bold text-brand-primary-900 leading-tight">
              {observation.speciesName}
            </CardTitle>
            {observation.commonName && (
              <p className="text-sm text-muted-foreground italic font-medium">
                {observation.commonName}
              </p>
            )}
          </div>
          {isUser && (
            <Badge
              className={cn(
                "capitalize border shrink-0 shadow-sm",
                currentStyles.bg,
                currentStyles.text,
                currentStyles.border,
              )}
            >
              {currentStatus}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-0 space-y-4">
        {observation.image && (
          <div className="relative h-48 w-full overflow-hidden rounded-lg border shadow-inner">
            <Image
              src={observation.image}
              alt={observation.speciesName}
              layout="fill"
              objectFit="cover"
              className="transition-transform duration-500 group-hover:scale-105"
            />
          </div>
        )}

        {/* Data Container: Preserving all fields */}
        <div className="rounded-md border bg-neutral-gray-100/50 p-3 space-y-3">
          <div className="space-y-1">
            <p className="text-sm font-semibold flex items-center gap-2">
              <span className="opacity-70">📍</span> {observation.locationName}
            </p>
            <p className="text-xs text-muted-foreground font-medium flex items-center gap-2">
              <span className="opacity-70">📅</span>{" "}
              {format(new Date(observation.observationDatetime), "PPP p")}
            </p>
          </div>

          {/* Technical Grid (Depth, Temp, etc.) */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-neutral-gray-300">
            {formatDepth(observation.depthMin, observation.depthMax) && (
              <div className="text-xs">
                <span className="text-muted-foreground">Depth:</span>
                <p className="font-bold">
                  {formatDepth(observation.depthMin, observation.depthMax)}
                </p>
              </div>
            )}
            {observation.bathymetry !== null && (
              <div className="text-xs">
                <span className="text-muted-foreground">Bathymetry:</span>
                <p className="font-bold">{observation.bathymetry}m</p>
              </div>
            )}
            {observation.temperature !== null && (
              <div className="text-xs">
                <span className="text-muted-foreground">Temperature:</span>
                <p className="font-bold">{observation.temperature}°C</p>
              </div>
            )}
            {observation.visibility !== null && (
              <div className="text-xs">
                <span className="text-muted-foreground">Visibility:</span>
                <p className="font-bold">{observation.visibility}m</p>
              </div>
            )}
            {observation.sex && (
              <div className="text-xs col-span-2">
                <span className="text-muted-foreground">Sex:</span>
                <p className="font-bold">{observation.sex}</p>
              </div>
            )}
          </div>

          {observation.notes && (
            <div className="pt-2 border-t border-neutral-gray-300">
              <p className="text-xs text-muted-foreground leading-relaxed italic">
                &quot;{observation.notes}&quot;
              </p>
            </div>
          )}
        </div>

        {/* Footer: Actions & Source */}
        <div className="flex items-center justify-between border-t pt-3">
          <div className="flex items-center space-x-2">
            <svg
              className={cn("h-3 w-3", currentStyles.fill)}
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="12" cy="12" r="8" />
            </svg>
            <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
              Source: {observation.source}
            </span>
          </div>

          <div className="flex space-x-2">
            <Button
              variant="edit"
              size="sm"
              className="h-8 px-3"
              onClick={(e) => {
                e.stopPropagation();
                onEditObservationClick(observation);
              }}
            >
              Edit
            </Button>
            <Button
              variant="delete"
              size="sm"
              className="h-8 px-3"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteObservation(observation.id);
              }}
            >
              Delete
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export { ObservationCard };
