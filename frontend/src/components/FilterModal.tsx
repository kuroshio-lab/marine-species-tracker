// frontend/src/components/FilterModal.tsx
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  Button,
  Input,
} from "@kuroshio-lab/ui";
import { SpeciesSearch } from "@kuroshio-lab/components";
import { searchSpecies } from "../lib/species";

interface FilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyFilters: (filters: {
    speciesName: string | null;
    commonName: string | null;
    minDate: string | null;
    maxDate: string | null;
  }) => void;
  initialFilters: {
    speciesName: string | null;
    commonName: string | null;
    minDate: string | null;
    maxDate: string | null;
  };
}

export default function FilterModal({
  isOpen,
  onClose,
  onApplyFilters,
  initialFilters,
}: FilterModalProps) {
  const [selectedSpecies, setSelectedSpecies] = useState<{
    speciesName: string;
    commonName: string;
  } | null>(
    initialFilters.speciesName
      ? {
          speciesName: initialFilters.speciesName,
          commonName: initialFilters.commonName || "",
        }
      : null,
  );
  const [minDate, setMinDate] = useState<string>(initialFilters.minDate || "");
  const [maxDate, setMaxDate] = useState<string>(initialFilters.maxDate || "");

  // Reset internal state when the modal opens or initial filters change
  useEffect(() => {
    setSelectedSpecies(
      initialFilters.speciesName
        ? {
            speciesName: initialFilters.speciesName,
            commonName: initialFilters.commonName || "",
          }
        : null,
    );
    setMinDate(initialFilters.minDate || "");
    setMaxDate(initialFilters.maxDate || "");
  }, [isOpen, initialFilters]);

  const handleApply = () => {
    onApplyFilters({
      speciesName: selectedSpecies?.speciesName || null,
      commonName: selectedSpecies?.commonName || null,
      minDate: minDate || null,
      maxDate: maxDate || null,
    });
    onClose();
  };

  const handleClear = () => {
    setSelectedSpecies(null);
    setMinDate("");
    setMaxDate("");
    onApplyFilters({
      speciesName: null,
      commonName: null,
      minDate: null,
      maxDate: null,
    });
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] max-h-[90vh] w-[90vw] max-w-md flex flex-col p-0 z-[1050]">
        <DialogHeader className="p-6 pb-2">
          <DialogTitle>Filter Observations</DialogTitle>
          <DialogDescription>
            Apply filters to refine the observations on the map.
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Species
              <SpeciesSearch
                id="species-search"
                value={selectedSpecies}
                onChange={setSelectedSpecies}
                onSearch={searchSpecies}
                placeholder="Search for species..."
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Date
              <Input
                id="min-date"
                type="date"
                value={minDate}
                onChange={(e) => setMinDate(e.target.value)}
                className="w-full"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Maximum Date
              <Input
                id="max-date"
                type="date"
                value={maxDate}
                onChange={(e) => setMaxDate(e.target.value)}
                className="w-full"
              />
            </label>
          </div>
        </div>
        <div className="flex justify-end p-6 pt-0 space-x-2">
          <Button variant="outline" onClick={handleClear}>
            Clear Filters
          </Button>
          <Button onClick={handleApply}>Apply Filters</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
