// frontend/src/components/ObservationFilterAndSort.tsx
import React, { useState, useMemo } from "react";
import { Observation } from "../types/observation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

interface ObservationFilterAndSortProps {
  observations: Observation[];
  onFilteredObservationsChange: (filteredObservations: Observation[]) => void;
  onFilterChange?: (
    filter: "all" | "validated" | "pending" | "rejected",
  ) => void;
}

export function ObservationFilterAndSort({
  observations,
  onFilteredObservationsChange,
  onFilterChange,
}: ObservationFilterAndSortProps) {
  const [statusFilter, setStatusFilter] = useState<
    "all" | "validated" | "pending" | "rejected"
  >("all");

  useMemo(() => {
    let filtered = [...observations];

    if (statusFilter !== "all") {
      filtered = filtered.filter(
        (observation) => observation.validated === statusFilter,
      );
    }

    filtered.sort((a, b) => {
      const dateA = new Date(a.createdAt || 0);
      const dateB = new Date(b.createdAt || 0);
      return dateB.getTime() - dateA.getTime();
    });

    // Communicate the filtered and sorted list back to the parent
    onFilteredObservationsChange(filtered);
  }, [observations, statusFilter, onFilteredObservationsChange]);

  const handleFilterChange = (
    value: "all" | "validated" | "pending" | "rejected",
  ) => {
    setStatusFilter(value);
    if (onFilterChange) {
      onFilterChange(value);
    }
  };

  return (
    <div className="flex justify-between items-center pr-0">
      <Select onValueChange={handleFilterChange} defaultValue={statusFilter}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Observations</SelectItem>
          <SelectItem value="validated">Validated</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
          <SelectItem value="rejected">Rejected</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
