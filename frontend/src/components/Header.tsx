"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { useUser } from "./UserProvider";
import { Button } from "./ui/button";
import FilterModal from "./FilterModal";
import { cn } from "../lib/utils";

interface HeaderProps {
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

export default function Header({
  onApplyFilters,
  initialFilters,
}: HeaderProps) {
  const { user, loading, logout } = useUser();
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="h-28 w-full bg-brand-primary-900" />;
  }
  const handleApplyFiltersAndCloseModal = (filters: {
    speciesName: string | null;
    commonName: string | null;
    minDate: string | null;
    maxDate: string | null;
  }) => {
    onApplyFilters(filters);
    setIsFilterModalOpen(false);
  };

  const renderUserStatus = () => {
    if (loading) {
      return (
        <span className="text-[9px] uppercase tracking-tighter text-white/40">
          Syncing System...
        </span>
      );
    }

    if (user) {
      return (
        <span className="text-[9px] uppercase tracking-wider text-brand-primary-100 font-bold">
          Operator: {user.username}
        </span>
      );
    }
    return (
      <span className="text-[9px] uppercase tracking-wider text-semantic-error-500">
        System Offline
      </span>
    );
  };

  return (
    <header className="w-full relative z-30 shrink-0 overflow-hidden shadow-2xl">
      <div className="absolute inset-0 bg-brand-primary-900 kerama-depth -z-0" />

      <nav className="relative z-10 border-b border-white/10 backdrop-blur-md">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-28 items-center justify-between gap-8">
            {/* LEFT SECTION: Branding & Identity */}
            <div className="flex items-center gap-4">
              <div className="relative group">
                <div className="absolute -inset-1 bg-brand-primary-300 rounded-full blur opacity-20 group-hover:opacity-40 transition duration-1000" />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-xl bg-white/10 border border-white/20 backdrop-blur-sm shadow-2xl">
                  <Image
                    src="/kuroshio-logo.svg"
                    alt="Kuroshio-Lab Logo"
                    width={32}
                    height={32}
                    className="h-8 w-8 drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]"
                  />
                </div>
              </div>

              <div className="flex flex-col justify-center">
                <h1 className="text-2xl font-bold tracking-tight leading-none">
                  <span className="bg-gradient-to-r from-white via-brand-primary-100 to-brand-primary-300 bg-clip-text text-transparent">
                    Kuroshio-Lab
                  </span>
                  <span className="ml-2 text-lg font-light text-brand-primary-100/60 hidden md:inline">
                    Marine Species Observation Tracker
                  </span>
                </h1>

                <p className="text-xs font-medium text-brand-primary-300/80 mt-1.5 max-w-md line-clamp-1">
                  Empower divers, biologists, and hobbyists...
                </p>

                <div className="flex items-center gap-2 mt-2 bg-black/20 w-fit px-2 py-0.5 rounded-full border border-white/5">
                  <div
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      user
                        ? "bg-semantic-success-500 animate-pulse shadow-[0_0_5px_theme(colors.semantic.success-500)]"
                        : "bg-neutral-gray-500",
                    )}
                  />
                  {renderUserStatus()}
                </div>
              </div>
            </div>

            {/* RIGHT SECTION: Navigation Actions */}
            <div className="flex items-center gap-3">
              {/* Glassmorphism Action Group */}
              <div className="flex items-center p-1 bg-white/5 rounded-lg border border-white/10 backdrop-blur-xl shadow-inner">
                <Button
                  onClick={() => setIsFilterModalOpen(true)}
                  variant="ghost"
                  className="text-white hover:bg-white/10 hover:text-brand-primary-300 transition-all gap-2 px-4 h-9"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                    />
                  </svg>
                  <span className="hidden sm:inline font-medium">Filters</span>
                </Button>

                <div className="w-px h-5 bg-white/10 mx-1" />

                <Button
                  // eslint-disable-next-line no-alert
                  onClick={() => alert("Export functionality ready soon.")}
                  variant="ghost"
                  className="text-white hover:bg-white/10 hover:text-brand-primary-300 transition-all gap-2 px-4 h-9"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  <span className="hidden sm:inline font-medium">Export</span>
                </Button>
              </div>

              {/* Sign Out: Distinct Destructive Action */}
              {user && (
                <Button
                  onClick={logout}
                  variant="outline"
                  size="sm"
                  className="h-11 border-white/20 bg-transparent text-white hover:bg-semantic-error-500 hover:border-semantic-error-500 transition-colors"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H7a3 3 0 01-3-3V7a3 3 0 013-3h3a3 3 0 013 3v1"
                    />
                  </svg>
                  <span className="hidden lg:inline">Sign Out</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Reusable Filter Modal */}
      <FilterModal
        isOpen={isFilterModalOpen}
        onClose={() => setIsFilterModalOpen(false)}
        onApplyFilters={handleApplyFiltersAndCloseModal}
        initialFilters={initialFilters}
      />
    </header>
  );
}
