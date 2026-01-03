"use client";

import Image from "next/image";
import { useUser } from "./UserProvider";
import { Button } from "./ui/button";

export default function Header() {
  const { user, loading, logout } = useUser();

  const handleExport = () => {
    // eslint-disable-next-line no-alert
    alert("Export functionality will be implemented later.");
  };

  const handleAllObservations = () => {
    // eslint-disable-next-line no-alert
    alert("All Observations functionality will be implemented later.");
  };

  return (
    <header className="w-full">
      <nav className="border-b border-white/10 bg-brand-primary-900 backdrop-blur-sm">
        <div className="sm:px-6 lg:px-4">
          <div className="flex h-24 items-center justify-between">
            {/* LEFT SECTION - Logo, Title, Tagline, User Info */}
            <div className="flex flex-col">
              <div className="flex items-center gap-3">
                <div className="flex h-10 items-center justify-center rounded-lg">
                  <Image
                    src="/kuroshio-logo.svg"
                    alt="Kuroshio-Lab Logo"
                    width={24}
                    height={24}
                    className="h-6 w-6"
                  />
                </div>
                <span className="text-xl font-bold text-neutral-white">
                  Kuroshio-Lab: Marine Species Observation Tracker
                </span>
              </div>

              <p className="text-sm font-body text-brand-primary-300 mt-1">
                Empower divers, biologists, and hobbyists...
              </p>

              {/* User Logic */}
              {loading && (
                <p className="text-xs text-brand-primary-500 mt-1">
                  Loading user...
                </p>
              )}
              {!loading && user && (
                <p className="text-xs text-brand-primary-300 mt-1">
                  Welcome, {user.username}
                </p>
              )}
              {!loading && !user && (
                <p className="text-xs text-semantic-error-500 mt-1">
                  Not logged in.
                </p>
              )}
            </div>

            {/* RIGHT BUTTON GROUP - Export, All Observations, Sign Out */}
            <div className="flex items-center space-x-3">
              {/* EXPORT BUTTON */}
              <Button
                onClick={handleExport}
                type="button"
                variant="actions"
                className="px-3 py-1.5 text-sm"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4 mr-1.5"
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
                Export
              </Button>

              {/* ALL OBSERVATIONS */}
              <Button
                onClick={handleAllObservations}
                type="button"
                variant="actions"
                className="px-3 py-1.5 text-sm"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4 mr-1.5"
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
                All Observations
              </Button>

              {/* SIGN OUT */}
              {user && (
                <Button
                  onClick={logout}
                  type="button"
                  variant="signOut"
                  className="px-3 py-1.5 text-sm"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4 mr-1.5"
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
                  Sign Out
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
}
