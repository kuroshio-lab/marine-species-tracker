// frontend/src/components/SpeciesSearch.tsx
import React, { useState, useEffect, useRef } from "react";
import { Input } from "./ui/input";
import { searchSpecies, SpeciesSearchResult } from "../lib/species";
import { cn } from "../lib/utils";

interface SpeciesSearchProps {
  value?: { speciesName: string; commonName: string } | null;
  onChange: (
    species: { speciesName: string; commonName: string } | null,
  ) => void;
  onBlur?: () => void;
  disabled?: boolean;
  placeholder?: string;
  error?: boolean;
}

export default function SpeciesSearch({
  value,
  onChange,
  onBlur,
  disabled = false,
  placeholder = "Search for species...",
  error = false,
}: SpeciesSearchProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<SpeciesSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initialize search query from value
  useEffect(() => {
    if (value) {
      const displayText = value.commonName
        ? `${value.speciesName} (${value.commonName})`
        : value.speciesName;
      setSearchQuery(displayText);
    } else {
      setSearchQuery("");
    }
  }, [value]);

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (searchQuery.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
    } else {
      setIsLoading(true);
      debounceTimerRef.current = setTimeout(async () => {
        try {
          const searchResults = await searchSpecies(searchQuery);
          setResults(searchResults);
          setIsOpen(searchResults.length > 0);
          setSelectedIndex(-1);
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error("Error searching species:", err);
          setResults([]);
          setIsOpen(false);
        } finally {
          setIsLoading(false);
        }
      }, 300);
    }

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchQuery]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    setSearchQuery(newQuery);
    setIsOpen(true);

    // If user clears the input, clear the selection
    if (!newQuery.trim()) {
      onChange(null);
    }
  };

  const handleSelect = (species: SpeciesSearchResult) => {
    onChange(species);
    const displayText = species.commonName
      ? `${species.speciesName} (${species.commonName})`
      : species.speciesName;
    setSearchQuery(displayText);
    setIsOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.blur();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) {
      if (e.key === "Enter") {
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < results.length - 1 ? prev + 1 : prev,
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case "Escape":
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full">
      <Input
        ref={inputRef}
        type="text"
        value={searchQuery}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (results.length > 0) {
            setIsOpen(true);
          }
        }}
        onBlur={() => {
          // Delay to allow click events on dropdown items
          setTimeout(() => {
            setIsOpen(false);
            setSelectedIndex(-1);
            onBlur?.();
          }, 200);
        }}
        disabled={disabled}
        placeholder={placeholder}
        className={cn(error && "border-red-500")}
      />
      {isOpen && (
        <div className="absolute z-[9999] mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
          {isLoading && (
            <div className="p-4 text-sm text-gray-500 text-center">
              Searching...
            </div>
          )}
          {!isLoading && results.length === 0 && (
            <div className="p-4 text-sm text-gray-500 text-center">
              No species found
            </div>
          )}
          {!isLoading &&
            results.length > 0 &&
            results.map((species, index) => (
              <button
                key={species.speciesName}
                type="button"
                className={cn(
                  "w-full text-left px-4 py-2 text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none",
                  selectedIndex === index && "bg-gray-100",
                )}
                onClick={() => handleSelect(species)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="font-medium">{species.speciesName}</div>
                {species.commonName && (
                  <div className="text-xs text-gray-500">
                    {species.commonName}
                  </div>
                )}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
